"""
Compare REPD groupings from SS dataset with Turing REPD groupings
- Ethan Jones <ejones18@sheffield.ac.uk>
- Jamie Taylor <jamie.taylor@sheffield.ac.uk>
- First Authored: 2020-04-16
"""

import sys
import os
import argparse

import pandas as pd
import numpy as np

from ss_repd_pairings import main as ss_repd_pairings

def main(ss_file, turing_file, out_file):
    """
    Concatenate Turing REPD groupings and SS REPD groupings then compare against one another. 
    Resulting dataframe is saved to a csv file.
    """
    ss_groupings = ss_repd_pairings(ss_file)
    turing_groupings = unstack_turing_groupings(turing_file)
    compared_dataframe = compare_to_ss_dataset(ss_groupings, turing_groupings)
    compared_dataframe.to_csv(out_file, index=False)

def unstack_turing_groupings(filename):
    """
    Unstack Turing matches from csv into groups.
    """
    pairings = pd.read_csv(filename)
    matches = []
    for i in pairings.index:
        if i >= 1:
            if pairings.group_id[i-1] == pairings.group_id[i]:
                matches.append(matches[i-1] + 1)
            else:
                matches.append(1)
        else:
            matches.append(1)
    pairings['matches'] = matches
    pairings = pairings.convert_dtypes()
    pairings.set_index(['group_id', 'matches'], inplace=True)
    pairings.sort_index(inplace=True)
    grouped_repd_ids = pairings.unstack(level=-1)
    grouped_repd_ids = grouped_repd_ids.add_prefix("turing_")
    return grouped_repd_ids

def print_progress(iteration, total, prefix="", suffix="", decimals=2, bar_length=100):
    """
    Call in a loop to create terminal progress bar.
    Parameters
    ----------
    `iteration` : int
        current iteration (required)
    `total` : int
        total iterations (required)
    `prefix` : string
        prefix string (optional)
    `suffix` : string
        suffix string (optional)
    `decimals` : int
        number of decimals in percent complete (optional)
    `bar_length` : int
        character length of bar (optional)
    Notes
    -----
    Taken from `Stack Overflow <http://stackoverflow.com/a/34325723>`_.
    """
    filled_length = int(round(bar_length * iteration / float(total)))
    percents = round(100.00 * (iteration / float(total)), decimals)
    progress_bar = "#" * filled_length + "-" * (bar_length - filled_length)
    sys.stdout.write("\r%s |%s| %s%s %s" % (prefix, progress_bar, percents, "%", suffix))
    sys.stdout.flush()
    if iteration == total:
        sys.stdout.write("\n")
        sys.stdout.flush()

def compare_to_ss_dataset(ss_groupings, turing_groupings):
    """
    Compares the Turing groupings to the SS groupings and assigns a flag to each group as to whether they are correct or not.
    """
    ss_groupings = ss_groupings.add_prefix("ss_")
    turing_groupings.reset_index(inplace=True)
    turing_groupings.columns = turing_groupings.columns.get_level_values(1)
    turing_groupings.rename(columns={'':'group_id'}, inplace=True)
    ss_groupings.columns = ss_groupings.columns.get_level_values(1)
    matches = []
    count = 0
    for i, ss_row in ss_groupings.filter(like="ss_").iterrows():
        for j, t_row in turing_groupings.filter(like="turing_").iterrows():
            if any([ssc in t_row.values for ssc in ss_row.values]):
                matches.append([i] + ss_groupings.loc[i].to_list() + turing_groupings.loc[j].to_list())
        count += 1
        print_progress(count, len(ss_groupings.index))
    compare_groupings = pd.DataFrame(matches, columns=["ssid"] + ss_groupings.columns.to_list() + turing_groupings.columns.to_list())
    compare_groupings = compare_groupings.assign(failed_grouping=pd.NA)
    for i, row in compare_groupings.iterrows():
        if np.isnan(row.turing_1):
            compare_groupings.loc[i, 'failed_grouping'] = 1 #system missing in Turing set
        elif np.array_equal(row[row.notnull()].filter(like="ss_").sort_values().to_numpy(), row[row.notnull()].filter(like="turing_").sort_values().to_numpy()):
            compare_groupings.loc[i, 'failed_grouping'] = 0 #correct group
        elif row.filter(like="ss_").notnull().sum() == row.filter(like="turing_").notnull().sum():
            compare_groupings.loc[i, 'failed_grouping'] = 2 #group doesn't match, same number of matches
        elif row.filter(like="ss_").notnull().sum() < row.filter(like="turing_").notnull().sum():
            compare_groupings.loc[i, 'failed_grouping'] = 3 #group doesn't match, greedy
        else:
            compare_groupings.loc[i, 'failed_grouping'] = 4 #group doesn't match, not greedy enough
    compare_groupings = compare_groupings[["group_id", "ssid", "failed_grouping"]]
    compare_groupings = compare_groupings.sort_values(by=["group_id", "ssid"])
    compare_groupings = compare_groupings.reset_index(drop=True)
    return compare_groupings

def query_yes_no(question, default="yes"):
    """
    Ask a yes/no question via input() and return the answer as boolean.
    Parameters
    ----------
    `question` : string
        The question presented to the user.
    `default` : string
        The presumed answer if the user just hits <Enter>. It must be "yes" (the default), "no" or
        None (meaning an answer is required of the user).
    Returns
    -------
    boolean
        Return value is True for "yes" or False for "no".
    Notes
    -----
    See http://stackoverflow.com/a/3041990
    """
    valid = {"yes": True, "y": True, "ye": True,
             "no": False, "n": False}
    if default is None:
        prompt = " [y/n] "
    elif default == "yes":
        prompt = " [Y/n] "
    elif default == "no":
        prompt = " [y/N] "
    else:
        raise ValueError("invalid default answer: '%s'" % default)
    while True:
        sys.stdout.write(question + prompt)
        choice = input().lower()
        if default is not None and choice == '':
            return valid[default]
        elif choice in valid:
            return valid[choice]
        else:
            sys.stdout.write("Please respond with 'yes' or 'no' "
                             "(or 'y' or 'n').\n")

def parse_options():
    """Parse command line options."""
    parser = argparse.ArgumentParser(description=("This is a command line interface (CLI) for "
                                                  "the compare_repd_groups.py module"),
                                     epilog="Jamie Taylor & Ethan Jones, 2020-04-15")
    parser.add_argument("--ss-file", dest="ss_file", action="store", type=str,
                        required=True, metavar="</path/to/file>",
                        help="Specify the path to the ss CSV file.")
    parser.add_argument("--turing-file", dest="turing_file", action="store", type=str,
                        required=True, metavar="</path/to/file>",
                        help="Specify the path to the turing CSV file.")
    parser.add_argument("-o", "--out-file", dest="out_file", action="store", type=str,
                        required=True, metavar="</path/to/file>",
                        help="Specify the path to the output file.")
    options = parser.parse_args()
    if not os.path.isfile(options.ss_file):
        raise Exception(f"The ss file '{options.ss_file}' does not exist.")
    if not os.path.isfile(options.turing_file):
        raise Exception(f"The turing file '{options.turing_file}' does not exist.")
    if os.path.isfile(options.out_file):
        if not query_yes_no("The output file already exists, are you sure you want to overwrite?"):
            print("Exiting")
            sys.exit()
    return options
if __name__ == "__main__":
    OPTIONS = parse_options()
    main(OPTIONS.ss_file, OPTIONS.turing_file, OPTIONS.out_file)
