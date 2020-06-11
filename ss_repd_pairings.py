"""
Extracting REPD groupings from SS dataset
- Jamie Taylor <jamie.taylor@sheffield.ac.uk>
- Ethan Jones <ejones18@sheffield.ac.uk>
- First Authored: 2020-04-10
"""

import os
import argparse
import pandas as pd

def get_matches(filename):
    """
    Extract REPD groupings from CSV
    """
    pairings = pd.read_csv(filename)
    pairings = pairings.drop(columns=['SOLAR_MEDIA_REF', 'RO_Generator_ID', 'SS_SUB_ID'])
    pairings = pairings.loc[pairings.REPD_REF_ID.notnull()].reset_index(drop=True)
    matches = []
    for i in pairings.index:
        if i >= 1:
            if pairings.SS_ID[i-1] == pairings.SS_ID[i]:
                matches.append(matches[i-1] + 1)
            else:
                matches.append(1)
        else:
            matches.append(1)
    pairings['matches'] = matches
    pairings = pairings.convert_dtypes()
    pairings.set_index(['SS_ID', 'matches'], inplace=True)
    pairings.sort_index(inplace=True)
    return pairings

def get_groups_from_matches(matches):
    """
    Unstacks dataframe
    """
    grouped_repd_ids = matches.unstack(level=-1)
    return grouped_repd_ids

def main(input_file, output_file=None):
    """
    Get REPD grouping from SS dataset and save to CSV.
    """
    matches = get_matches(input_file)
    groups = get_groups_from_matches(matches)
    if output_file is not None:
        groups.to_csv(output_file, index=False)
    return groups

def parse_options():
    """Parse command line options."""
    parser = argparse.ArgumentParser(description=("This is a command line interface (CLI) for "
                                                  "the ss_repd_groupings.py module"),
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
