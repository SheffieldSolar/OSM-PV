#!/usr/bin/env python3
"""
Clean up the OSM neighbour pairings from Turing Institute.

- Jamie Taylor <jamie.taylor@sheffield.ac.uk>
- Ethan Jones <ejones18@sheffield.ac.uk>
- First Authored: 2020-03-04
"""

import os
import argparse
import pandas as pd
from OSMPythonTools.api import Api

def munge_groups(filename):
    """
    Load a file of OSM object 1:1 pairings and restructure as groups.
    """
    pairings = pd.read_csv(filename)
    groups = []
    processed = []
    for i in pairings.index:
        target = pairings.loc[[i], :]
        if target.object.values[0] in processed:
            continue
        neighbours = pairings.loc[pairings.object == target.object.values[0], "neighbour_object"]
        group = target.loc[:, "object"]
        nnn = 0
        while True:
            if not neighbours.empty and len(neighbours) > nnn:
                group = pd.concat((group, neighbours), ignore_index=True)
                nnn = len(neighbours)
            else:
                break
            neighbours = pairings.loc[pairings.object.isin(neighbours), "neighbour_object"]
        group.drop_duplicates(inplace=True)
        group.reset_index(drop=True, inplace=True)
        groups.append(group)
        processed += group.values.tolist()
    groups_ = pd.DataFrame([[i+1, g] for i, gr in enumerate(groups) for g in gr.values],
                           columns=["id", "objects"])
    return groups_

def fetch_osm_data(groups):
    """
    Fetch ways/nodes from the OSM API.
    """
    osm = Api()
    for i in groups.index:
        way_id = groups.loc[i, "objects"].split("/")[-1]
        way = osm.query(f"way/{way_id}")
        latlons = [(n.lat(), n.lon()) for n in way.nodes()]
        groups.loc[i, "lats"] = "|".join(map(str, [l[0] for l in latlons]))
        groups.loc[i, "lons"] = "|".join(map(str, [l[1] for l in latlons]))
    return groups

def main(input_file, output_file):
    """
    Fix 1:1 pairings in OSM CSV file.
    """
    groups = munge_groups(input_file)
    groups_with_latlons = fetch_osm_data(groups)
    groups_with_latlons.to_csv(output_file, index=False)

def parse_options():
    """Parse command line options."""
    parser = argparse.ArgumentParser(description=("This is a command line interface (CLI) for "
                                                  "the fix_groupings.py module"),
                                     epilog="Jamie Taylor & Ethan Jones, 2020-03-04")
    parser.add_argument("-f", "--input-file", dest="input_file", action="store", type=str,
                        required=True, metavar="</path/to/file>",
                        help="Specify the path to the input CSV file.")
    parser.add_argument("-o", "--output-file", dest="output_file", action="store", type=str,
                        required=True, metavar="</path/to/file>",
                        help="Specify the path to the output CSV file.")
    options = parser.parse_args()
    if not os.path.isfile(options.input_file):
        raise Exception(f"The input file '{options.input_file}' does not exist.")
    return options

if __name__ == "__main__":
    OPTIONS = parse_options()
    main(OPTIONS.input_file, OPTIONS.output_file)
