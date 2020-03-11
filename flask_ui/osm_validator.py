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
import pandas as pd
import numpy as np

ROOT_PATH = os.path.dirname(os.path.realpath(__file__))
UPLOAD_FOLDER = os.path.join(ROOT_PATH, "uploads")

APP = Flask(__name__)
APP.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

FLAG_CODES = {
    1: ("Domestic neighbours", "Multiple domestic neighbours should be independent systems"),
    2: ("Good group within bad group", "A good group within the bad group"),
    3: ("Missing system", "A missing system with the good group"),
    4: ("Commercial neighbours", "Multiple commercial neighbours should be independent systems")
}

@APP.route("/", methods=["GET", "POST"])
def home_page():
    return render_template("home_page.html")

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
        # validation_notes = request.form["validation_notes"]
        # validation_notes = validation_notes.replace(",", ";")
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
                           center_lat=mean_lats, center_lon=mean_lons, bing_key=bing_key, flag_codes=FLAG_CODES)

def flush_results(group_id, is_valid, flags):
    print(flags)
    results_file = os.path.join(ROOT_PATH, "results", "group_validations_2.csv")
    all_flags = FLAG_CODES.keys()
    flag_labels = [FLAG_CODES[k][0] for k in all_flags]
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