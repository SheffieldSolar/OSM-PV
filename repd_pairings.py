"""
Extracting REPD groupings from Turing
- Jamie Taylor <jamie.taylor@sheffield.ac.uk>
- Ethan Jones <ethan.jones@sheffield.ac.uk>
- First Authored: 2020-04-10
"""

import os
import argparse
import pandas as pd

def munge_turing_groups(filename):
    """
    Load a file of turing REPD 1:1 pairings and restructure as groups.
    """
    pairings = pd.read_csv(filename)
    groups = []
    processed = []
    for i in pairings.index:
        target = pairings.loc[[i], :]
        if target.repd_id.values[0] in processed:
            continue
        neighbours = pairings.loc[pairings.neighbour_id == target.repd_id.values[0], "repd_id"]
        group = target.loc[:, "repd_id"]
        nnn = 0
        while True:
            if not neighbours.empty and len(neighbours) > nnn:
                group = pd.concat((group, neighbours), ignore_index=True)
                nnn = len(neighbours)
            else:
                break
            neighbours = pairings.loc[pairings.neighbour_id == target.repd_id.values[0],
                                      "repd_id"]
        group.drop_duplicates(inplace=True)
        group.reset_index(drop=True, inplace=True)
        groups.append(group)
        processed += group.values.tolist()
    groups_ = pd.DataFrame([[i+1, g] for i, gr in enumerate(groups) for g in gr.values],
                           columns=["group_id", "repd_id"])
    return groups_

def main(input_file, output_file):
    """
    Fix 1:1 pairings in REPD CSV file.
    """
    groups = munge_turing_groups(input_file)
    groups.to_csv(output_file, index=False)

def parse_options():
    """Parse command line options."""
    parser = argparse.ArgumentParser(description=("This is a command line interface (CLI) for "
                                                  "the fix_REPD_groupings.py module"),
                                     epilog="Jamie Taylor & Ethan Jones, 2020-04-10")
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
