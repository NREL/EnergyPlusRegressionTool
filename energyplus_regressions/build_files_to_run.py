#!/usr/bin/env python
from __future__ import print_function

import argparse
import csv
import glob
import json
import os
import random
import sys

# set up some things ahead of time
path = os.path.dirname(__file__)
script_dir = os.path.abspath(path)
slash = os.sep


class CsvFileEntry(object):

    def __init__(self, csv_row):
        self.filename = csv_row[0]
        self.weatherfilename = csv_row[1]
        self.has_weather_file = (self.weatherfilename != "")
        self.external_interface = (csv_row[2] == "Y")
        self.underscore = (self.filename[0] == '_')


class FileListBuilderArgs:
    """The FileListBuilder class accepts arguments in the form created by the argparse library, as this was originally
    called by the command line only.  This class provides an alternate way to create those arguments."""

    def __init__(self):
        # establish defaults
        self.all = False
        self.extinterface = False
        self.random = 0
        self.weatherless = True
        self.underscore = True
        self.verify = None
        self.check = False
        self.verify = None
        self.master_data_file = "full_file_set_details.csv"

        # some special things for GUI
        self.gui = True


class FileListBuilder(object):

    def __init__(self, _args):

        self.config = _args

        # if the 'all' argument is present, turn on all the rest
        if self.config.all:
            self.config.extinterface, self.config.underscore, self.config.weatherless = [True, True, True]

        # initialize callbacks to None
        self.callback_func_print = None
        self.callback_func_init = None
        self.callback_func_increment = None

        # initialize other variables to None
        self.selected_input_file_set = None
        self.input_files_eliminated = None
        self.input_files_found_not_listed = None

    def set_callbacks(self, callback_print, callback_init, callback_increment):  # pragma: no cover
        self.callback_func_print = callback_print
        self.callback_func_init = callback_init
        self.callback_func_increment = callback_increment

    def build_verified_list(self):

        self.my_print("Starting to build file list")

        # initialize the status flag to True
        success = True

        # then wrap the processes inside a try block to trap for any errors
        try:

            # create an empty list
            self.selected_input_file_set = []

            # for convenience, count the number of rows first, this should be a cheap operation anyway
            with open(self.config.master_data_file) as csvfile:
                num_lines_approx = csvfile.read().count('\n')
            self.my_init(num_lines_approx + 1)

            # get all rows of data
            with open(self.config.master_data_file) as csvfile:
                reader = csv.reader(csvfile)
                row_num = 0
                for row in reader:
                    self.my_increment()
                    row_num += 1
                    if row_num == 1:
                        continue
                    this_entry = CsvFileEntry(row)
                    self.selected_input_file_set.append(this_entry)

            # then sort it by filename
            self.selected_input_file_set.sort(key=lambda x: x.filename.lower())
            self.my_increment()

            # initialize a list of files that weren't found
            self.input_files_eliminated = set()
            self.input_files_found_not_listed = set()

            # if we are verifying using input file directories,
            if self.config.verify:

                self.my_print("Verifying idf list using directory: %s" % self.config.verify)

                # read in the files in the directory and remove the extensions
                files_in_this_dir = self.read_input_files_in_dir(self.config.verify)
                files_no_extensions = [os.path.splitext(infile)[0] for infile in files_in_this_dir]
                just_filenames = [infile.split(os.sep)[-1] for infile in files_no_extensions]

                # check all files in the main set and see if any are missing
                for infile in self.selected_input_file_set:

                    # if it is missing add it to the files to be eliminated
                    if infile.filename not in just_filenames:
                        # sets only include unique entities
                        self.input_files_eliminated.add(infile)

                # include a report of files found in the directory not represented in the file list
                just_filenames_from_csv = [x.filename for x in self.selected_input_file_set]
                for infile in just_filenames:

                    # if the file found by globbing is missing from the csv dataset
                    if infile not in just_filenames_from_csv:
                        # add it to the report
                        self.input_files_found_not_listed.add(infile)

                # now prune off files missing in the verification directories
                if len(self.input_files_eliminated) > 0:
                    for i in self.input_files_eliminated:
                        self.selected_input_file_set.remove(i)

            self.my_print("File list build completed successfully")

        except Exception as this_exception:
            self.my_print("An error occurred during file list build")
            self.my_print(this_exception)
            success = False

        return success, self.selected_input_file_set, self.input_files_eliminated, self.input_files_found_not_listed

    def print_file_list_to_file(self):

        # if we aren't running in the gui, we need to go ahead and down select and write to the output file
        if not self.config.gui:
            with open(self.config.output_file, 'w') as outfile:
                files = []
                for i in self.selected_input_file_set:
                    if i.has_weather_file:
                        object_to_add = {'file': i.filename, 'epw': i.weatherfilename}
                        # print("%s %s" % (i.filename, i.weatherfilename), file=outfile)
                    else:
                        object_to_add = {'file': i.filename}
                        # print("%s" % i.filename, file=outfile)
                    files.append(object_to_add)
                json_object = {'files_to_run': files}
                outfile.write(json.dumps(json_object, indent=2))
        self.my_print("File list build complete")

    @staticmethod
    def read_input_files_in_dir(directory):
        extensions_to_match = ['*.idf', '*.imf']
        files_in_dir = []
        for extension in extensions_to_match:
            files_in_dir.extend(glob.glob(directory + os.sep + extension))
        return files_in_dir

    def down_select_idf_list(self):

        idf_list = self.selected_input_file_set

        # now trim off any of the specialties if the switches are false (by default)
        if not self.config.extinterface:  # only include those without external interface dependencies
            idf_list = [idf for idf in idf_list if not idf.external_interface]
        if not self.config.weatherless:  # only include those that DO have weather files
            idf_list = [idf for idf in idf_list if idf.has_weather_file]
        if not self.config.underscore:  # only include those that don't start with an underscore
            idf_list = [idf for idf in idf_list if not idf.underscore]
        # do random down selection as necessary:
        if self.config.random > 0:
            if len(idf_list) <= self.config.random:  # just take all of them
                pass
            else:  # down select randomly
                indexes_to_take = sorted(random.sample(range(len(idf_list)), self.config.random))
                idf_list = [idf_list[i] for i in indexes_to_take]
        # return the trimmed list
        self.selected_input_file_set = idf_list
        return idf_list

    def my_init(self, num_files):  # pragma: no cover
        if self.callback_func_init:
            self.callback_func_init(num_files)

    def my_increment(self):  # pragma: no cover
        if self.callback_func_increment:
            self.callback_func_increment()

    def my_print(self, msg):  # pragma: no cover
        if self.callback_func_print:
            self.callback_func_print(msg)
        else:
            print(msg)


if __name__ == "__main__":  # pragma: no cover

    # parse command line arguments
    parser = argparse.ArgumentParser(
        description="""
Create EnergyPlus test file inputs for a specific configuration.  Can be executed in 2 ways:
  1: Arguments can be passed from the command line, such as `%s -r 3 -w' .. Most useful for scripting, or
  2: An argument class can be created using the FileListBuilderArgs class and
     passed into a FileListBuilder instance .. Most useful for UIs""" % sys.argv[0]
    )
    parser.add_argument(
        '-a', '--all', action='store_true',
        help='Includes all files found in the master, overrides other flags, can still down select with -r'
    )
    parser.add_argument('-e', '--extinterface', action='store_true', help='Include external interface test files')
    parser.add_argument('-r', '--random', nargs='?', default=0, type=int, metavar='N',
                        help='Get random selection of <N> files')
    parser.add_argument('-w', '--weatherless', action='store_true',
                        help='Include files that do not have a weather file')
    parser.add_argument('-u', '--underscore', action='store_true', help='Include files that start with an underscore')
    parser.add_argument(
        '-v', '--verify', metavar='<path>', nargs=1,
        help='''Performs verification that files exist in a directory.  Excludes those that do not.
             Argument is a path to a test file directory containing idfs and imfs.'''
    )
    args = parser.parse_args()

    # these were originally inputs, but that is really bulky
    # they are now hardwired and can be manipulated outside the script if needed
    args.master_data_file = os.path.join(script_dir, "full_file_set_details.csv")
    args.output_file = os.path.join(script_dir, "files_to_run.json")

    # backup the previous output file if one already exists and then delete it
    if os.path.isfile(args.output_file):
        b_file = os.path.join(os.path.dirname(args.output_file), "backup_%s" % os.path.basename(args.output_file))
        if os.path.isfile(b_file):
            try:
                os.remove(b_file)
            except Exception as exc:
                print(
                    "An error occurred trying to remove the previous backup output file: %s; aborting..." % b_file
                )
                print("Error message: " % exc)
        try:
            os.rename(args.output_file, b_file)
        except Exception as exc:
            print(
                "An error occurred trying to backup the previous output file: %s; aborting..." % args.output_file
            )
            print("Error message: " % exc)

    if args.verify:
        args.verify = args.verify[0]  # argparse insists on returning a list, even if just 1
        args.check = True
    else:
        args.check = False

    # for running this as a script, add some dummies:
    args.gui = False

    # instantiate the main class to run
    this_builder = FileListBuilder(args)

    # The following two calls will actually return values
    # In a GUI, we will capture these returns as desired to do further stuff with
    # In a script, we will just let the class instance hang on to the values and write out the list file

    # build a base file list verified with any directories requested
    this_builder.build_verified_list()

    # down select the idf list based on command line arguments
    this_builder.down_select_idf_list()

    # and go ahead and print to the output file
    this_builder.print_file_list_to_file()
