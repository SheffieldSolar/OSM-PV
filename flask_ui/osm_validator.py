#!/usr/bin/env python3
"""
A Flask UI to semi-automate the process of validating OSM PV groupings.

- Jamie Taylor <jamie.taylor@sheffield.ac.uk>
- Ethan Jones <ejones18@sheffield.ac.uk>
- First Authored: 2020-03-04
"""

import os
import pickle
from flask import Flask, request, url_for, redirect
from flask.templating import render_template
import pandas as pd
import numpy as np

ROOT_PATH = os.path.dirname(os.path.realpath(__file__))
UPLOAD_FOLDER = os.path.join(ROOT_PATH, "uploads")

APP = Flask(__name__)
APP.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

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
    if group_id not in osm_groups.id:
        return home_page()
    if "is_valid" in request.form:
        is_valid = request.form["is_valid"] == "yes"
        flush_results(group_id, is_valid)
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
                           center_lat=mean_lats, center_lon=mean_lons)

def flush_results(group_id, is_valid):
    results_file = os.path.join(ROOT_PATH, "results", "group_validations.csv")
    new_result = pd.DataFrame([[group_id, is_valid]], columns=["group_id", "is_valid"])
    if os.path.isfile(results_file):
        results = pd.read_csv(results_file)
        if group_id in results.group_id:
            results.drop(results[results.group_id == group_id].index, inplace=True)
        results = pd.concat((results, new_result), ignore_index=True)
    else:
        results = new_result
    results.to_csv(results_file, index=False)
