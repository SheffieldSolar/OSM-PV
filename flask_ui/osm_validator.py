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

FLAG_CODES_REPD_OSM_DISAGREEMENT_MATCHES = {
    1: ("No install date", "A system in the match has no install date"),
    2: ("Same match", "Turing and Soton have the same match, just different order of systems"),
    3: ("Potential grouping missed", "From the matches, the osm way looks like a group system and is missing an repd entry"),
    4: ("Not a correct grouping", "Includes a system that doesn't seem to be part of the group")
}

FLAG_CODES_REPD_OSM_MATCHES = {
    1: ("Wrong system", "Match includes an incorrect system"),
    2: ("Wrong instance of system", "The wrong instance of the system has been put forward i.e. a system in the match has no install date"),
    3: ("Missing system/way", "The ways matched possibly don't cover the whole system or a system is missing from a match"),
    4: ("Potential grouping missed", "From the matches, the osm way looks like a group system and is missing an repd entry"),
    5: ("Too greedy (Includes domestic systems)", "The match includes domestic systems"),
    6: ("Wrong way", "Match includes a way that isn't part of the system / may not cover all the system"),
    7: ("System not built yet", "The REPD system in this match is awaiting construction")
}

REPD_FILE = "C:/Users/EJones820/Desktop/Sheffield_Solar/osm_pv/pv_datasets/renewable-energy-planning-database-june-2020.xlsx"

@APP.route("/", methods=["GET", "POST"])
def home_page():
    """Home page of the flask app."""
    return render_template("landing_page.html")

@APP.route("/validate_osm_groups_landing_page", methods=["GET", "POST"])
def validate_osm_groups_landing_page():
    """Group validation landing page."""
    return render_template("home_page.html")

@APP.route("/osm_repd_validation_landing_page", methods=["GET", "POST"])
def osm_repd_validation_landing_page():
    """OSM-REPD matches validation landing page."""
    return render_template("osm_repd_validation_homepage.html")

@APP.route("/osm_repd_disagreement_validation_landing_page", methods=["GET", "POST"])
def osm_repd_disagreement_validation_landing_page():
    """OSM-REPD disagreement matches validation landing page."""
    return render_template("osm_repd_disagreement_validation_homepage.html")

@APP.route("/validate_osm_repd_disagreement_matches/<int:index>", methods=["GET", "POST"])
def validate_osm_repd_disagreement_matches(index):
    """OSM-REPD disagreement matches page."""
    groups_cache_dir = os.path.join(ROOT_PATH, "cache")
    groups_cache_file = os.path.join(groups_cache_dir, "osmWayFile.p")
    repd_cache_file = os.path.join(groups_cache_dir, "repd_data.p")
    if request.method == "POST" and "osmWayFile" in request.files:
        osm_repd_matches = pd.read_csv(request.files["osmWayFile"].stream)
        osm_repd_matches = osm_repd_matches.rename(columns={'Unnamed: 0': 'match_id'})
        osm_repd_matches_groups = fix_disagreement_groupings(osm_repd_matches)
        if not os.path.isdir(groups_cache_dir):
            os.mkdir(groups_cache_dir)
        with open(groups_cache_file, "wb") as fid:
            pickle.dump(osm_repd_matches_groups, fid)
        print("\n")
        print("Loading the REPD dataset...")
        print("\n")
        repd_df = load_repd(REPD_FILE)
        print("\n")
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
        flush_disagreement_matches_results(osm_repd_matches_groups[index].sol_id.values[0], is_valid, flags)
        return redirect(url_for("validate_osm_repd_disagreement_matches", index=index+1))
    matches = osm_repd_matches_groups[index]
    lats = matches.iloc[0, :].latitude
    lons = matches.iloc[0, :].longitude
    soton_repd_ids = matches.soton_repd_id.unique().tolist()
    turing_repd_ids = matches.turing_repd_id.unique().tolist()
    turing_repds_table = repd_df.loc[repd_df["id"].isin(turing_repd_ids)].to_html()
    soton_repds_table = repd_df.loc[repd_df["id"].isin(soton_repd_ids)].to_html()
    ways = {osm_id: fetch_osm_data(osm_id, "way") for osm_id in matches.osm_id.unique().tolist()}
    turing_coords = {turing_repd_id: (repd_df[repd_df.id==turing_repd_id].latitude.values[0], repd_df[repd_df.id==turing_repd_id].longitude.values[0]) for turing_repd_id in matches.turing_repd_id.unique().tolist()}
    soton_coords = {soton_repd_id: (repd_df[repd_df.id == soton_repd_id].latitude.values[0], repd_df[repd_df.id == soton_repd_id].longitude.values[0]) for soton_repd_id in matches.soton_repd_id.unique().tolist()}
    return render_template("validate_osm_repd_disagreement_matches.html", index=index, ways=ways,
                           center_lat=lats, center_lon=lons,
                           bing_key=BING_KEY,
                           turing_coords=turing_coords, soton_coords=soton_coords,
                           tables=[turing_repds_table, soton_repds_table],
                           flag_codes=FLAG_CODES_REPD_OSM_DISAGREEMENT_MATCHES)

@APP.route("/validate_osm_repd_matches/<int:index>", methods=["GET", "POST"])
def validate_osm_repd_matches(index):
    """OSM-REPD matches validation page."""
    groups_cache_dir = os.path.join(ROOT_PATH, "cache")
    groups_cache_file = os.path.join(groups_cache_dir, "osmWayFile.p")
    repd_cache_file = os.path.join(groups_cache_dir, "repd_data.p")
    if request.method == "POST" and "osmWayFile" in request.files:
        raw_dataset = pd.read_csv(request.files["osmWayFile"].stream, low_memory=False)
        filtered_dataset = raw_dataset[raw_dataset[['osm_id', 'repd_id']].notnull().all(1)]
        expanded_dataset = expand_relations(filtered_dataset)
        osm_repd_matches_groups = fix_groupings(expanded_dataset)
        if not os.path.isdir(groups_cache_dir):
            os.mkdir(groups_cache_dir)
        with open(groups_cache_file, "wb") as fid:
            pickle.dump(osm_repd_matches_groups, fid)
        print("\n")
        print("Loading the REPD dataset...")
        print("\n")
        repd_df = load_repd(REPD_FILE)
        print("\n")
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
        print("\n")
        print(f"Flushing validation for match index: {index}")
        print("\n")
        flushes_osm_repd__validation_results(index, osm_repd_matches_groups[index].osm_id_nw.unique().tolist(), osm_repd_matches_groups[index].repd_id.unique().tolist(), is_valid, flags)
        return redirect(url_for("validate_osm_repd_matches", index=index+1))
    matches = osm_repd_matches_groups[index]
    lats = matches.iloc[0, :].latitude
    lons = matches.iloc[0, :].longitude
    repd_ids = matches.repd_id.unique().tolist()
    matches_table = matches.to_html()
    repds_table = repd_df.loc[repd_df["id"].isin(repd_ids)].to_html()
    osm_data = {osm_id: fetch_osm_data(osm_id, matches[matches["osm_id_nw"] == osm_id].osm_objtype.tolist()[0])
                for osm_id in matches.osm_id_nw.unique().tolist()}
    coords = {repd_id: (repd_df[repd_df.id == repd_id].latitude.values[0], repd_df[repd_df.id == repd_id].longitude.values[0])
              for repd_id in matches.repd_id.unique().tolist()}
    return render_template("validate_osm_repd_matches.html", index=index, ways=osm_data,
                           center_lat=lats, center_lon=lons,
                           bing_key=BING_KEY,
                           coords=coords,
                           tables=[repds_table, matches_table],
                           flag_codes=FLAG_CODES_REPD_OSM_MATCHES)

@APP.route("/validate_osm_groups/<int:group_id>", methods=["GET", "POST"])
def validate_osm_groups(group_id):
    """Group validation page."""
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
                           center_lat=mean_lats, center_lon=mean_lons, bing_key=BING_KEY, flag_codes=FLAG_CODES_OSM_GROUPINGS)

def flushes_osm_repd__validation_results(group_id, osm_id, repd_id, validation, flags):
    """Flushes the OSM-REPD validation result to a file."""
    results_file = os.path.join(ROOT_PATH, "results", "repd_osm_matches_dataset_results.csv")
    if validation == "correct":
        validation = 1
    else:
        validation = 0
    all_flags = FLAG_CODES_REPD_OSM_MATCHES.keys()
    flag_labels = [FLAG_CODES_REPD_OSM_MATCHES[k][0] for k in all_flags]
    flag_bools = [f in flags for f in all_flags]
    new_result = pd.DataFrame([[group_id, "|".join(map(str, osm_id)), "|".join(map(str, repd_id)), validation]+flag_bools], columns=["group_id", "osm_id(s)", "repd_id(s)", "validation"] + flag_labels)
    if os.path.isfile(results_file):
        results = pd.read_csv(results_file)
        if group_id in results.group_id:
            results.drop(results[results.group_id == group_id].index, inplace=True)
        results = pd.concat((results, new_result), ignore_index=True)
    else:
        results = new_result
    results.to_csv(results_file, index=False)

def flush_disagreement_matches_results(sol_id, validation, flags):
    """Flushes the OSM-REPD disagreement validation result to a file."""
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

def fix_disagreement_groupings(repd_matches_df):
    """Breaks dataset into groupings."""
    groups = []
    for sol_id in repd_matches_df.sol_id.unique().tolist():
        group = repd_matches_df.loc[repd_matches_df.sol_id == sol_id, :]
        groups.append(group)
    print("\n")
    print(f"Found a total of {len(groups)} groups")
    print("\n")
    return groups

def fix_groupings(raw_dataset):
    """Breaks dataset into groupings."""
    print("\n")
    print("Fetching groupings...")
    print("\n")
    groups = []
    processed_repd = []
    processed_osm = []
    for row in raw_dataset.iterrows():
        if row.osm_id_nw in processed_osm or row.repd_id in processed_repd:
            continue
        group = raw_dataset.loc[(raw_dataset.repd_id == row.repd_id) | (raw_dataset.osm_id_nw == row.osm_id_nw), :]
        groups.append(group)
        processed_osm += group.osm_id_nw.unique().tolist()
        processed_repd += group.repd_id.unique().tolist()
    print("\n")
    print(f"Found a total of {len(groups)} groups")
    print("\n")
    return groups

def expand_relations(raw_dataset):
    """Expands relations into their ways."""
    non_relation_data = raw_dataset.loc[raw_dataset.osm_objtype != "relation", :]
    non_relation_data.loc[:, "osm_id_nw"] = non_relation_data.loc[:, "osm_id"]
    relation_data = raw_dataset.loc[raw_dataset.osm_objtype == "relation", :]
    for row in relation_data.iterrows():
        try:
            way_ids = break_relation_into_ways(row.osm_id)
            temp_df = pd.DataFrame(row).copy(deep=True, ignore_index=True)
            temp_df["osm_id_nw"] = way_ids
            non_relation_data = pd.concat([non_relation_data, temp_df], ignore_index=True)
        except:
            continue
    return non_relation_data

def break_relation_into_ways(osm_id):
    """Takes a relation id and returns the way ids within."""
    osm_id = int(osm_id)
    osm = Api()
    relation = osm.query(f"relation/{osm_id}")
    way_ids = []
    for way in relation.members():
        way_ids.append(way.id())
    return way_ids

def fetch_osm_data(osm_id, osm_type):
    """
    Fetch ways/nodes from the OSM API.
    """
    osm_id = int(osm_id)
    osm = Api()
    if osm_type == "way":
        way = osm.query(f"way/{osm_id}")
        latlons = [(n.lat(), n.lon()) for n in way.nodes()]
    elif osm_type == "node":
        node = osm.query(f"node/{osm_id}")
        latlons = [(node.lat(), node.lon())]
    return latlons

def flush_results(group_id, is_valid, flags):
    """
    Flushes results to file.
    """
    print(flags)
    results_file = os.path.join(ROOT_PATH, "results", "group_validations.csv")
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
    """
    Loads the bing maps API key.
    """
    try:
        with open(api_key_file) as fid:
            key = fid.read().strip()
    except FileNotFoundError:
        warnings.warn("Failed to load Bing Maps API key - you will not be able to make new "
                      "queries to the Bing Maps API!")
        return None
    return key
API_KEY_FILE = os.path.join(ROOT_PATH, "bing_api_key.txt")
BING_KEY = load_bing_key(API_KEY_FILE)
