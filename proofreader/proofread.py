#!/usr/bin/env python

#
# Use to test column and row names for conformity, since we're only human!
# --autocorrect-whitespace will strip spaces and newlines before processing
#

import sys
import csv
import glob
import argparse
import shutil
import re
from tempfile import NamedTemporaryFile

VARIABLE_COL_NAMES = ["Description", "Variable", "variable"]
DATE_COL_NAMES = ["Date", "date"]
# Compute the Levenshtein edit distance between two strings
# From http://en.wikibooks.org/wiki/Algorithm_Implementation
#          /Strings/Levenshtein_distance#Python
def levenshtein(s1, s2):
    if len(s1) < len(s2):
        return levenshtein(s2, s1)

    # len(s1) >= len(s2)
    if len(s2) == 0:
        return len(s1)

    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row

    return previous_row[-1]


# Tests for whitespace - should probably regex this for tabs etc
def whitespace_test(items, descriptor, verbose=True):
    error_free = True
    if verbose:
        print "\n\033[1m## Testing %ss for whitespace\033[0m" % descriptor

    for idx, item in enumerate(items):
        if item != item.strip() or "\n" in item or "  " in item:
            error_free = False
            if verbose:
                print "line:%i: Whitespace found in %s '\033[30;43m%s\033[0m'" % \
                      (idx + 2, descriptor, item)

    return error_free


# Compares passed items vs. passed knowns, calling out anything not matching
def unknowns_test(items, knowns, descriptor, verbose=True):
    error_free = True
    if verbose:
        print "\n\033[1m## Testing %ss for known values\033[0m" % descriptor

    unknowns_and_indexes = [(idx + 2, item) for idx, item in
                            enumerate(items) if item not in knowns]

    for unknown in unknowns_and_indexes:
        error_free = False
        # Sort based on edit distance to suggest alternatives
        possibles = sorted(knowns,
                           key=lambda known: levenshtein(unknown[1], known))
        if verbose:
            print "line:%i: Unknown %s '\033[30;43m%s\033[0m', maybe you meant '\033[30;42m%s\033[0m' or '\033[30;42m%s\033[0m'?" % \
                (unknown[0], descriptor, unknown[1], possibles[0], possibles[1])

    return error_free


def autocorrect_whitespace(filename):
    tempfile = NamedTemporaryFile(delete=False)

    with open(filename, 'rU') as csvFile, tempfile:
        reader = csv.reader(csvFile)
        writer = csv.writer(tempfile, lineterminator='\n')

        for index, row in enumerate(reader):
            # Remove newlines, duplicate spaces,
            # and beginning/trailing whitespace
            trimmed_row = [re.sub(r' +',
                                  ' ',
                                  cell.replace("\n", "").strip())
                           for cell in row]
            writer.writerow(trimmed_row)

    shutil.move(tempfile.name, filename)
    tempfile.close()

def proofread(filename, verbose=True):
    # Let's read in the canonical rows and columns
    # Should probably move this elsewhere
    with open('canonical_columns.csv', 'rU') as cols_file:
        col_names = [row['name'] for row in csv.DictReader(cols_file)]

    with open('canonical_variables.csv', 'rU') as vars_file:
        var_names = [row['name'] for row in csv.DictReader(vars_file)]
    
    # In what column can we possibly find the variable (aka row) name?
    # Description = Guinea
    # Variable = Liberia
    # variable = Sierra Leone

    error_free = True
    with open(filename, 'rU') as csvfile:
        reader = csv.DictReader(csvfile)

        headers = reader.fieldnames

        whitespace_test(headers, 'header', verbose=verbose)
        unknowns_test(headers, col_names, 'header', verbose=verbose)

        # Is the row variable called 'Description' or 'name' or what?
        # We do a set intersection and take the first match.
        matches = (set(VARIABLE_COL_NAMES) & set(headers))

        if matches:
            col_name = matches.pop()

            variables = [row[col_name] for row in reader]
            error_free = whitespace_test(variables, 'variable', verbose=verbose) and error_free
            error_free = unknowns_test(variables, var_names, 'variable', verbose=verbose) \
                and error_free
        else:
            if verbose:
                print "Could not identify variable column name"
            error_free = False
    return error_free

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Collect proofread options')

    # --autocorrect-whitespace will automatically trim whitespace in csv's
    parser.add_argument('--autocorrect-whitespace',
                        dest='autocorrect_whitespace',
                        action='store_true',
                        default=False)
    parser.add_argument('filenames', nargs='*')  # This is it!!

    args = parser.parse_args()

    exit_code = 0
    # Grab the filename from passed arguments
    for filename in args.filenames:
        print "\033[1mProcessing file: %s...\033[0m" % filename
        if args.autocorrect_whitespace:
            autocorrect_whitespace(filename)
        # Will exit with 0 with no errors, 1 with errors
        # proofread returns True (1) if no problems, so must negate it
        exit_code = not proofread(filename) or exit_code

    exit(exit_code)
