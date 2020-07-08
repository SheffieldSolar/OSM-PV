#!/usr/bin/env python3
"""
A Flask UI to semi-automate the process of validating OSM PV groupings.

- Jamie Taylor <jamie.taylor@sheffield.ac.uk>
- Ethan Jones <ejones18@sheffield.ac.uk>
- First Authored: 2020-03-04
"""

import os
import pickle
import warnings
from flask import Flask, request, url_for, redirect
from flask.templating import render_template
from OSMPythonTools.api import Api
import pandas as pd
import numpy as np

from repd import load_repd

ROOT_PATH = os.path.dirname(os.path.realpath(__file__))
UPLOAD_FOLDER = os.path.join(ROOT_PATH, "uploads")

APP = Flask(__name__)
APP.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

FLAG_CODES_OSM_GROUPINGS = {
    1: ("Domestic neighbours", "Multiple domestic neighbours should be independent systems"),
    2: ("Good group within bad group", "A good group within the bad group"),
    3: ("Missing system", "A missing system with the good group"),
    4: ("Commercial neighbours", "Multiple commercial neighbours should be independent systems")
}

FLAG_CODES_REPD_OSM_MATCHES = {
    1: ("No install date", "A system in the match has no install date"),
    2: ("Same match", "Turing and Soton have the same match, just different order of systems"),
    3: ("Potential grouping missed", "From the matches, the osm way looks like a group system and is missing an repd entry"),
    4: ("Not a correct grouping", "Includes a system that doesn't seem to be part of the group")
}

REPD_FILE = "C:/Users/EJones820/Desktop/Sheffield_Solar/osm_pv/pv_datasets/renewable-energy-planning-database-march-2020.xlsx"

@APP.route("/", methods=["GET", "POST"])
def home_page():
    return render_template("landing_page.html")

@APP.route("/validate_osm_groups_landing_page", methods=["GET", "POST"])
def validate_osm_groups_landing_page():
    return render_template("home_page.html")

@APP.route("/osm_repd_validation_landing_page", methods=["GET", "POST"])
def osm_repd_validation_landing_page():
    return render_template("osm_repd_validation_homepage.html")

@APP.route("/validate_osm_repd_matches/<int:index>", methods=["GET", "POST"])
def validate_osm_repd_matches(index):
    groups_cache_dir = os.path.join(ROOT_PATH, "cache")
    groups_cache_file = os.path.join(groups_cache_dir, "osmWayFile.p")
    repd_cache_file = os.path.join(groups_cache_dir, "repd_data.p")
    if request.method == "POST" and "osmWayFile" in request.files:
        osm_repd_matches = pd.read_csv(request.files["osmWayFile"].stream)
        osm_repd_matches = osm_repd_matches.rename(columns={'Unnamed: 0': 'match_id'})
        osm_repd_matches_groups = fix_groupings(osm_repd_matches)
        if not os.path.isdir(groups_cache_dir):
            os.mkdir(groups_cache_dir)
        with open(groups_cache_file, "wb") as fid:
            pickle.dump(osm_repd_matches_groups, fid)
        repd_df = load_repd(REPD_FILE)
        with open(repd_cache_file, "wb") as fid:
            pickle.dump(repd_df, fid)
    else:
        with open(groups_cache_file, "rb") as fid:
            osm_repd_matches_groups = pickle.load(fid)
        with open(repd_cache_file, "rb") as fid:
            repd_df = pickle.load(fid)
    if index >= len(osm_repd_matches_groups):
        return redirect(url_for("home_page"))
    if "is_valid" in request.form:
        is_valid = request.form["is_valid"]
        flags = list(map(int, request.form.getlist("flag")))
        flush_matches_results(osm_repd_matches_groups[index].sol_id.values[0], is_valid, flags)
        return redirect(url_for("validate_osm_repd_matches", index=index+1))
    matches = osm_repd_matches_groups[index]
    lats = matches.iloc[0, :].latitude
    lons = matches.iloc[0, :].longitude
    soton_repd_ids = matches.soton_repd_id.unique().tolist()
    turing_repd_ids = matches.turing_repd_id.unique().tolist()
    turing_repds_table = repd_df.loc[repd_df["id"].isin(turing_repd_ids)].to_html()
    soton_repds_table = repd_df.loc[repd_df["id"].isin(soton_repd_ids)].to_html()
    ways = {osm_id: fetch_osm_data(osm_id) for osm_id in matches.osm_id.unique().tolist()}
    turing_coords = {turing_repd_id: (repd_df[repd_df.id==turing_repd_id].latitude.values[0], repd_df[repd_df.id==turing_repd_id].longitude.values[0]) for turing_repd_id in matches.turing_repd_id.unique().tolist()}
    soton_coords = {soton_repd_id: (repd_df[repd_df.id==soton_repd_id].latitude.values[0], repd_df[repd_df.id==soton_repd_id].longitude.values[0]) for soton_repd_id in matches.soton_repd_id.unique().tolist()}
    return render_template("validate_osm_repd_matches.html", index=index, ways=ways,
                           center_lat=lats, center_lon=lons, 
                           bing_key=bing_key,
                           turing_coords=turing_coords, soton_coords=soton_coords,
                           tables=[turing_repds_table, soton_repds_table],
                           flag_codes=FLAG_CODES_REPD_OSM_MATCHES)

@APP.route("/validate_osm_groups/<int:group_id>", methods=["GET", "POST"])
def validate_osm_groups(group_id):
    groups_cache_dir = os.path.join(ROOT_PATH, "cache")
    groups_cache_file = os.path.join(groups_cache_dir, "osmGroupsFile.p")
    if request.method == "POST" and "osmGroupsFile" in request.files:
        osm_groups = pd.read_csv(request.files["osmGroupsFile"].stream)
        if not os.path.isdir(groups_cache_dir):
            os.mkdir(groups_cache_dir)
        with open(groups_cache_file, "wb") as fid:
            pickle.dump(osm_groups, fid)
    else:
        with open(groups_cache_file, "rb") as fid:
            osm_groups = pickle.load(fid)
    if group_id > osm_groups.id.max():
        return redirect(url_for("home_page"))
    if "is_valid" in request.form:
        is_valid = request.form["is_valid"] == "yes"
        flags = list(map(int, request.form.getlist("flag")))
        flush_results(group_id, is_valid, flags)
        return redirect(url_for("validate_osm_groups", group_id=group_id+1))
    group = osm_groups.loc[osm_groups.id == group_id]
    ways = {}
    mean_lats = []
    mean_lons = []
    for i in group.index:
        lats = group.loc[i, "lats"].split("|")
        lons = group.loc[i, "lons"].split("|")
        ways[group.loc[i, "objects"]] = zip(lats, lons)
        mean_lats.append(np.mean(list(map(float, lats))))
        mean_lons.append(np.mean(list(map(float, lons))))
    mean_lats = np.mean(mean_lats)
    mean_lons = np.mean(mean_lons)
    return render_template("validate_osm_groups.html", ways=ways, group_id=group_id,
                           center_lat=mean_lats, center_lon=mean_lons, bing_key=bing_key, flag_codes=FLAG_CODES_OSM_GROUPINGS)

def flush_matches_results(sol_id, validation, flags):
    results_file = os.path.join(ROOT_PATH, "results", "repd_osm_matches_results.csv")
    if validation == "turing":
        validation = 0 #turing mapped to 0
    elif validation == "soton":
        validation = 1 #soton mapped to 1
    elif validation == "both":
        validation = 2 #both correct mapped to 2
    else:
        validation = 3 #other
    all_flags = FLAG_CODES_REPD_OSM_MATCHES.keys()
    flag_labels = [FLAG_CODES_REPD_OSM_MATCHES[k][0] for k in all_flags]
    flag_bools = [f in flags for f in all_flags]
    new_result = pd.DataFrame([[sol_id, validation]+flag_bools], columns=["sol_id", "validation"] + flag_labels)
    if os.path.isfile(results_file):
        results = pd.read_csv(results_file)
        if sol_id in results.sol_id:
            results.drop(results[results.sol_id == sol_id].index, inplace=True)
        results = pd.concat((results, new_result), ignore_index=True)
    else:
        results = new_result
    results.to_csv(results_file, index=False)
    

def fix_groupings(repd_matches_df):
    groups = []
    for sol_id in repd_matches_df.sol_id.unique().tolist():
        group = repd_matches_df.loc[repd_matches_df.sol_id==sol_id, :]
        groups.append(group)
    return groups

def fetch_osm_data(way_id):
    """
    Fetch ways/nodes from the OSM API.
    """
    osm = Api()
    way = osm.query(f"way/{way_id}")
    latlons = [(n.lat(), n.lon()) for n in way.nodes()]
    return latlons

def flush_results(group_id, is_valid, flags):
    print(flags)
    results_file = os.path.join(ROOT_PATH, "results", "group_validations_2.csv")
    all_flags = FLAG_CODES_OSM_GROUPINGS.keys()
    flag_labels = [FLAG_CODES_OSM_GROUPINGS[k][0] for k in all_flags]
    flag_bools = [f in flags for f in all_flags]
    new_result = pd.DataFrame([[group_id, is_valid]+flag_bools], columns=["group_id", "is_valid"] + flag_labels)
    if os.path.isfile(results_file):
        results = pd.read_csv(results_file)
        if group_id in results.group_id:
            results.drop(results[results.group_id == group_id].index, inplace=True)
        results = pd.concat((results, new_result), ignore_index=True)
    else:
        results = new_result
    results.to_csv(results_file, index=False)

def load_bing_key(api_key_file):
    try:
        with open(api_key_file) as fid:
            key = fid.read().strip()
    except FileNotFoundError:
        warnings.warn("Failed to load Bing Maps API key - you will not be able to make new "
                      "queries to the Bing Maps API!")
        return None
    return key
api_key_file = os.path.join(ROOT_PATH, "bing_api_key.txt")
bing_key = load_bing_key(api_key_file)