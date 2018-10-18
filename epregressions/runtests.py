#!/usr/bin/env python
# -*- coding: utf-8 -*- 
from __future__ import unicode_literals

# then os and shutil which provide file operations and others
import os
import shutil
# python's own diff library
from difflib import *
# add stuff to either make series calls, or multithreading
from multiprocessing import Process, Queue, freeze_support

from epregressions import MathDiff
from epregressions import TableDiff
from epregressions import ThreshDict
from epregressions import epsim
# import the files related to this script
from epregressions.Structures import *

# always import sys first

# get the current file path for convenience
path = os.path.dirname(__file__)
script_dir = os.path.abspath(path)


# the actual main test suite run class
class TestSuiteRunner():

    def __init__(self, run_config, entries):

        # initialize callbacks
        self.print_callback = None
        self.starting_callback = None
        self.casecompleted_callback = None
        self.simulationscomplete_callback = None
        self.enderrcompleted_callback = None
        self.diffcompleted_callback = None
        self.alldone_callback = None
        self.cancel_callback = None
        self.id_like_to_stop_now = False

        # User configuration; read from the run_configuration
        self.force_run_type = run_config.force_run_type
        self.TestOneFile = run_config.TestOneFile
        self.number_of_threads = int(run_config.num_threads)
        self.min_reporting_freq = run_config.report_freq

        # File list brought in separately
        self.entries = entries

        # Main test configuration here
        self.buildA = run_config.buildA.build
        self.executableA = run_config.buildA.executable
        self.runA = run_config.buildA.run
        self.buildB = run_config.buildB.build
        self.executableB = run_config.buildB.executable
        self.runB = run_config.buildB.run

        # For the other tools
        self.eplus_install_path = run_config.eplus_install

        # Settings/paths defined relative to this script
        self.path_to_file_list = os.path.join(script_dir, "files_to_run.txt")
        self.thresh_dict_file = os.path.join(script_dir, "MathDiff.config")
        self.math_diff_executable = os.path.join(script_dir, "MathDiff.py")
        self.table_diff_executable = os.path.join(script_dir, "TableDiff.py")
        self.ep_run_executable = os.path.join(script_dir, "epsim.py")
        self.weather_data_dir = os.path.join(script_dir, "..", "WeatherData")
        self.datasets_dirname = "DataSets"
        self.datasets_dir = os.path.join(script_dir, "..", self.datasets_dirname)
        self.input_files_dir = "InputFiles"

        # Settings/paths defined relative to the buildA/buildB test directories
        # the tests directory will be different based on forceRunType
        if self.force_run_type == ForceRunType.ANNUAL:
            self.test_output_dir = "Tests-Annual"
        elif self.force_run_type == ForceRunType.DD:
            self.test_output_dir = "Tests-DDOnly"
        elif self.force_run_type == ForceRunType.REVERSEDD:
            self.my_print(
                "ReverseDD not currently supported by runtests.py. A separate tool will be available soon. Aborting...")
            self.my_alldone(self.entries)
        elif self.force_run_type == ForceRunType.NONE:
            self.test_output_dir = "Tests"

        # Filename specification, not path specific
        self.eplus_in_filename = "in.idf"
        self.time_log_filename = "runtimes.csv"

        # For files that don't have a specified weather file, use Chicago
        self.default_weather_filename = "USA_IL_Chicago-OHare.Intl.AP.725300_TMY3.epw"

        # Required to avoid stalls
        if self.number_of_threads == 1:
            freeze_support()

    def run_test_suite(self):

        # reset this flag
        self.id_like_to_stop_now = False

        # some shorthand conveniences
        bA = self.buildA
        bB = self.buildB
        dTest = self.test_output_dir

        # do some preparation
        self.prepare_dir_structure(bA, bB, dTest)

        if self.id_like_to_stop_now:
            self.my_cancelled()
            return

        numBuilds = 2
        self.my_starting(numBuilds, len(self.entries))

        # run the energyplus script
        if self.runA:
            self.copy_and_run_for_build(bA, self.executableA)
            if self.id_like_to_stop_now:
                self.my_cancelled()
                return
        if self.runB:
            self.copy_and_run_for_build(bB, self.executableB)
            if self.id_like_to_stop_now:
                self.my_cancelled()
                return
        self.my_simulationscomplete()

        if bA and bB:
            self.diff_logs_for_build(bA, bB)

        self.my_print("Test suite complete for directories:")
        self.my_print("\t%s" % bA)
        self.my_print("\t%s" % bB)
        self.my_print("Test suite complete")

        self.my_alldone(self.entries)

    def prepare_dir_structure(self, bA, bB, dTest):

        # make tests directory as needed
        for build in [bA, bB]:
            if build:
                if not os.path.exists(os.path.join(build, dTest)):
                    os.mkdir(os.path.join(build, dTest))

    def copy_and_run_for_build(self, build, executable):

        this_test_dir = self.test_output_dir
        local_run_type = self.force_run_type

        # Create queues for threaded operation
        task_queue = Queue()
        done_queue = Queue()

        # Create a job list
        EnergyPlusRuns = []

        # loop over all entries
        for entry in self.entries:

            # first remove the previous test directory for this file and rename it
            if os.path.exists(os.path.join(build, this_test_dir, entry.basename)):
                shutil.rmtree(os.path.join(build, this_test_dir, entry.basename))
            os.mkdir(os.path.join(build, this_test_dir, entry.basename))

            # establish the absolute path to the idf or imf, and append .idf or .imf as necessary
            idf_base = os.path.join(build, self.input_files_dir, entry.basename)
            idf_base = idf_base.strip()
            idf_path = ''
            imf_path = ''
            if idf_base[-4:] == ".idf":
                idf_path = idf_base
            elif idf_base[-4:] == ".imf":
                imf_path = idf_base
            else:
                idf_path = idf_base + ".idf"
                imf_path = idf_base + ".imf"

            parametric_file = False
            if os.path.exists(idf_path):

                # copy the idf into the test directory, renaming to in.idf
                shutil.copy(idf_path, os.path.join(build, this_test_dir, entry.basename, self.eplus_in_filename))

                # read in the entire text of the idf to do some special operations; could put in one line, but the with block ensures the file handle is closed
                idf_text = ''
                with open(os.path.join(build, this_test_dir, entry.basename, self.eplus_in_filename)) as f:
                    idf_text = f.read()
                    idf_text = unicode(idf_text, errors='ignore')

                # if the file requires the window 5 dataset file, bring it into the test run directory
                if 'Window5DataFile.dat' in idf_text:
                    os.mkdir(os.path.join(build, this_test_dir, entry.basename, self.datasets_dirname))
                    shutil.copy(os.path.join(self.datasets_dir, 'Window5DataFile.dat'),
                                os.path.join(build, this_test_dir, entry.basename, self.datasets_dirname))

                # if the file requires the TDV dataset file, bring it into the test run directory, right now I think it's broken
                if 'DataSets\TDV' in idf_text:
                    os.mkdir(os.path.join(build, this_test_dir, entry.basename, self.datasets_dirname))
                    os.mkdir(os.path.join(build, this_test_dir, entry.basename, self.datasets_dirname, 'TDV'))
                    source_dir = os.path.join(self.datasets_dir, 'TDV')
                    src_files = os.listdir(source_dir)
                    for file_name in src_files:
                        full_file_name = os.path.join(source_dir, file_name)
                        if (os.path.isfile(full_file_name)):
                            shutil.copy(full_file_name,
                                        os.path.join(build, this_test_dir, entry.basename, self.datasets_dirname,
                                                     'TDV'))

                if 'Parametric:' in idf_text:
                    parametric_file = True

                # if the file requires the FMUs dataset file, bring it into the test run directory, right now I think it's broken
                if 'ExternalInterface:' in idf_text:
                    os.mkdir(os.path.join(build, this_test_dir, entry.basename, self.datasets_dirname))
                    os.mkdir(os.path.join(build, this_test_dir, entry.basename, self.datasets_dirname, 'FMUs'))
                    source_dir = os.path.join(self.datasets_dir, 'FMUs')
                    src_files = os.listdir(source_dir)
                    for file_name in src_files:
                        full_file_name = os.path.join(source_dir, file_name)
                        if (os.path.isfile(full_file_name)):
                            shutil.copy(full_file_name,
                                        os.path.join(build, this_test_dir, entry.basename, self.datasets_dirname,
                                                     'FMUs'))

                # rewrite the idf with the (potentially) modified idf text
                with open(os.path.join(build, this_test_dir, entry.basename, self.eplus_in_filename), 'w') as f:
                    f.write("%s\n" % idf_text)

            elif os.path.exists(imf_path):

                shutil.copy(imf_path, os.path.join(build, this_test_dir, entry.basename, 'in.imf'))
                # find the rest of the imf files and copy them into the test directory
                source_dir = os.path.join(build, self.input_files_dir)
                source_files = os.listdir(source_dir)
                for file_name in source_files:
                    if file_name[-4:] == '.imf':
                        full_file_name = os.path.join(source_dir, file_name)
                        shutil.copy(full_file_name, os.path.join(build, this_test_dir, entry.basename))

            else:

                # if the file doesn't exist, just move along
                self.my_print("Input file doesn't exist in either idf or imf form:")
                self.my_print("   IDF: %s" % idf_path)
                self.my_print("   IMF: %s" % imf_path)
                self.my_casecompleted(TestCaseCompleted(this_test_dir, entry.basename, False, False, ""))
                continue

            rvi = os.path.join(build, self.input_files_dir, entry.basename) + '.rvi'
            if os.path.exists(rvi):
                shutil.copy(rvi, os.path.join(build, this_test_dir, entry.basename, 'in.rvi'))

            mvi = os.path.join(build, self.input_files_dir, entry.basename) + '.mvi'
            if os.path.exists(mvi):
                shutil.copy(mvi, os.path.join(build, this_test_dir, entry.basename, 'in.mvi'))

            if entry.epw:
                if (local_run_type != ForceRunType.DD) and (
                not os.path.exists(os.path.join(self.weather_data_dir, entry.epw + '.epw'))):
                    self.my_print("Weather file doesn't exist: %s .. skipping this input file" % (
                        os.path.join(self.weather_data_dir, entry.epw)))
                    self.my_casecompleted(TestCaseCompleted(this_test_dir, entry.basename, False, True, ""))
                    continue
                else:
                    EnergyPlusRuns.append((epsim.execute_energyplus, (
                    build, entry.basename, os.path.join(build, this_test_dir, entry.basename), executable,
                    local_run_type, self.min_reporting_freq, parametric_file,
                    os.path.join(self.weather_data_dir, entry.epw + '.epw'), self.eplus_install_path)))
            else:
                EnergyPlusRuns.append((epsim.execute_energyplus, (
                build, entry.basename, os.path.join(build, this_test_dir, entry.basename), executable, local_run_type,
                self.min_reporting_freq, parametric_file,
                os.path.join(self.weather_data_dir, self.default_weather_filename), self.eplus_install_path)))

        if self.number_of_threads == 1:
            for task in EnergyPlusRuns:
                # when I get a chance, I'll look at how to squash the args down, for now just fill a temp array as needed
                tmparr = []
                for val in task[1]:
                    tmparr.append(val)
                if self.id_like_to_stop_now:
                    return  # self.my_cancelled() is called in parent function
                ret = epsim.execute_energyplus(*tmparr)
                self.my_casecompleted(TestCaseCompleted(ret[0], ret[1], ret[2], ret[3], ret[4]))
        else:
            # Submit tasks
            for task in EnergyPlusRuns:
                task_queue.put(task)

            # Start worker processes
            for i in range(self.number_of_threads):
                p = Process(target=self.threaded_worker, args=(task_queue, done_queue))
                p.daemon = True
                p.start()

            # Get and print results
            for i in range(len(EnergyPlusRuns)):
                ret = done_queue.get()
                self.my_casecompleted(TestCaseCompleted(ret[0], ret[1], ret[2], ret[3], ret[4]))

            # Tell child processes to stop
            for i in range(self.number_of_threads):
                task_queue.put('STOP')

    def threaded_worker(self, input, output):
        for func, args in iter(input.get, 'STOP'):
            if self.id_like_to_stop_now:
                print("I'd like to stop now.")
                return
            return_val = func(*args)
            output.put(return_val)  # something needs to be put into the output queue for everything to work

    def both_files_exist(self, base_path_a, base_path_b, common_relative_path):
        if os.path.exists(os.path.join(base_path_a, common_relative_path)):
            if os.path.exists(os.path.join(base_path_b, common_relative_path)):
                return True
        return False

    def diff_text_files(self, fileA, fileB, diffFile):
        # instantiate the diff class; could put this outside the function if its heavy
        d = Differ()
        # read the contents of the two files into a list, could read it into text first
        txt1 = open(fileA).readlines()
        txt2 = open(fileB).readlines()
        # remove any lines that have "Program Version,EnergyPlus" in it
        txt1_cleaned = []
        for line in txt1:
            if "Program Version,EnergyPlus" in line or "EnergyPlus Completed" in line or "EnergyPlus Terminated" in line or "DElight input generated" in line or "(idf)=" in line or "(user input)=" in line or "(input file)=" in line:
                pass
            else:
                txt1_cleaned.append(line)
        txt2_cleaned = []
        for line in txt2:
            if "Program Version,EnergyPlus" in line or "EnergyPlus Completed" in line or "EnergyPlus Terminated" in line or "DElight input generated" in line or "(idf)=" in line or "(user input)=" in line or "(input file)=" in line:
                pass
            else:
                txt2_cleaned.append(line)
        # compare for equality, if it is faster to compare strings then lists, may want to refactor
        if txt1_cleaned == txt2_cleaned:
            return TextDifferences.EQUAL
        # if we aren't equal, compute the comparison and write to the output file, return that diffs occurred
        cmp = d.compare(txt1_cleaned, txt2_cleaned)
        cmp = unified_diff(txt1_cleaned, txt2_cleaned)
        outFile = open(diffFile, 'w')
        outFile.writelines(list(cmp))
        return TextDifferences.DIFFS

    def process_diffs_for_one_case(self, entry, case_result_dir_1, case_result_dir_2, out_dir=None):
        if out_dir is None:
            out_dir = case_result_dir_1

        # we aren't using mathdiff and tablediffs summary csv files, so use blanks
        path_to_mathdiff_log = ""
        path_to_tablediff_log = ""

        # shortcut
        fpath = os.path.join

        # process the end files first
        status_case1 = EndErrSummary.STATUS_MISSING
        status_case2 = EndErrSummary.STATUS_MISSING
        runtime_case1 = 0
        runtime_case2 = 0
        end_path = fpath(case_result_dir_1, 'eplusout.end')
        if os.path.exists(end_path):
            [status_case1, runtime_case1] = self.process_end_file(end_path)
        end_path = fpath(case_result_dir_2, 'eplusout.end')
        if os.path.exists(end_path):
            [status_case2, runtime_case2] = self.process_end_file(end_path)
        entry.add_summary_result(EndErrSummary(status_case1, runtime_case1, status_case2, runtime_case2))

        # Handle the results of the end file before doing anything with diffs
        # Case 1: Both end files existed, so E+ did complete
        if not any(x == EndErrSummary.STATUS_MISSING for x in [status_case1, status_case2]):
            # Case 1a: Both files are successful
            if sum(x == EndErrSummary.STATUS_SUCCESS for x in [status_case1, status_case2]) == 2:
                # Just continue to process diffs
                self.my_print("Processing (Diffs) : %s" % entry.basename)
            # Case 1b: Both completed, but both failed: report that it failed in both cases and return early
            elif sum(x == EndErrSummary.STATUS_SUCCESS for x in [status_case1, status_case2]) == 0:
                self.my_print(
                    "Skipping an entry because it appears to have a fatal error in both base and mod cases: %s" % entry.basename)
                return entry
            # Case 1c: Both completed, but one failed: report that it failed in one case and return early
            elif sum(x == EndErrSummary.STATUS_SUCCESS for x in [status_case1, status_case2]) == 1:
                self.my_print(
                    "Skipping an entry because it appears to have a fatal error in one case: %s" % entry.basename)
                return entry
        # Case 2: Both end files DID NOT exist
        elif all(x == EndErrSummary.STATUS_MISSING for x in [status_case1, status_case2]):
            self.my_print(
                "Skipping an entry because it appears to have failed (crashed) in both base and mod cases: %s" % entry.basename)
            return entry
        # Case 3: Both end files DID NOT exist
        elif sum(x == EndErrSummary.STATUS_MISSING for x in [status_case1, status_case2]) == 1:
            self.my_print(
                "Skipping an entry because it appears to have failed (crashed) in one case: %s" % entry.basename)
            return entry
        # Case 4: Unhandled combination
        else:
            self.my_print("Skipping an entry because it has an unknown end status: %s" % entry.basename)
            return entry

        # Load diffing threshold dictionary
        thresh_dict = ThreshDict.ThreshDict(self.thresh_dict_file)

        # Do Math (CSV) Diffs
        if self.both_files_exist(case_result_dir_1, case_result_dir_1, 'eplusout.csv'):
            entry.add_math_differences(MathDifferences(MathDiff.math_diff(
                thresh_dict,
                fpath(case_result_dir_1, 'eplusout.csv'),
                fpath(case_result_dir_2, 'eplusout.csv'),
                fpath(out_dir, 'eplusout.csv.absdiff.csv'),
                fpath(out_dir, 'eplusout.csv.percdiff.csv'),
                fpath(out_dir, 'eplusout.csv.diffsummary.csv'),
                path_to_mathdiff_log)), MathDifferences.ESO)
        if self.both_files_exist(case_result_dir_1, case_result_dir_2, 'eplusmtr.csv'):
            entry.add_math_differences(MathDifferences(MathDiff.math_diff(
                thresh_dict,
                fpath(case_result_dir_1, 'eplusmtr.csv'),
                fpath(case_result_dir_2, 'eplusmtr.csv'),
                fpath(out_dir, 'eplusmtr.csv.absdiff.csv'),
                fpath(out_dir, 'eplusmtr.csv.percdiff.csv'),
                fpath(out_dir, 'eplusmtr.csv.diffsummary.csv'),
                path_to_mathdiff_log)), MathDifferences.MTR)

        if self.both_files_exist(case_result_dir_1, case_result_dir_2, 'epluszsz.csv'):
            entry.add_math_differences(MathDifferences(MathDiff.math_diff(
                thresh_dict,
                fpath(case_result_dir_1, 'epluszsz.csv'),
                fpath(case_result_dir_2, 'epluszsz.csv'),
                fpath(out_dir, 'epluszsz.csv.absdiff.csv'),
                fpath(out_dir, 'epluszsz.csv.percdiff.csv'),
                fpath(out_dir, 'epluszsz.csv.diffsummary.csv'),
                path_to_mathdiff_log)), MathDifferences.ZSZ)

        if self.both_files_exist(case_result_dir_1, case_result_dir_2, 'eplusssz.csv'):
            entry.add_math_differences(MathDifferences(MathDiff.math_diff(
                thresh_dict,
                fpath(case_result_dir_1, 'eplusssz.csv'),
                fpath(case_result_dir_2, 'eplusssz.csv'),
                fpath(out_dir, 'eplusssz.csv.absdiff.csv'),
                fpath(out_dir, 'eplusssz.csv.percdiff.csv'),
                fpath(out_dir, 'eplusssz.csv.diffsummary.csv'),
                path_to_mathdiff_log)), MathDifferences.SSZ)

        # Do Tabular (HTML) Diffs
        if self.both_files_exist(case_result_dir_1, case_result_dir_2, 'eplustbl.htm'):
            entry.add_table_differences(TableDifferences(TableDiff.table_diff(
                thresh_dict,
                fpath(case_result_dir_1, 'eplustbl.htm'),
                fpath(case_result_dir_2, 'eplustbl.htm'),
                fpath(out_dir, 'eplustbl.htm.absdiff.htm'),
                fpath(out_dir, 'eplustbl.htm.percdiff.htm'),
                fpath(out_dir, 'eplustbl.htm.summarydiff.htm'),
                path_to_tablediff_log)))

        # Do Textual Diffs
        if self.both_files_exist(case_result_dir_1, case_result_dir_2, 'eplusout.audit'):
            entry.add_text_differences(TextDifferences(self.diff_text_files(
                fpath(case_result_dir_1, 'eplusout.audit'),
                fpath(case_result_dir_2, 'eplusout.audit'),
                fpath(out_dir, 'eplusout.audit.diff'))), TextDifferences.AUD)
        if self.both_files_exist(case_result_dir_1, case_result_dir_2, 'eplusout.bnd'):
            entry.add_text_differences(TextDifferences(self.diff_text_files(
                fpath(case_result_dir_1, 'eplusout.bnd'),
                fpath(case_result_dir_2, 'eplusout.bnd'),
                fpath(out_dir, 'eplusout.bnd.diff'))), TextDifferences.BND)
        if self.both_files_exist(case_result_dir_1, case_result_dir_2, 'eplusout.dxf'):
            entry.add_text_differences(TextDifferences(self.diff_text_files(
                fpath(case_result_dir_1, 'eplusout.dxf'),
                fpath(case_result_dir_2, 'eplusout.dxf'),
                fpath(out_dir, 'eplusout.dxf.diff'))), TextDifferences.DXF)
        if self.both_files_exist(case_result_dir_1, case_result_dir_2, 'eplusout.eio'):
            entry.add_text_differences(TextDifferences(self.diff_text_files(
                fpath(case_result_dir_1, 'eplusout.eio'),
                fpath(case_result_dir_2, 'eplusout.eio'),
                fpath(out_dir, 'eplusout.eio.diff'))), TextDifferences.EIO)
        if self.both_files_exist(case_result_dir_1, case_result_dir_2, 'eplusout.mdd'):
            entry.add_text_differences(TextDifferences(self.diff_text_files(
                fpath(case_result_dir_1, 'eplusout.mdd'),
                fpath(case_result_dir_2, 'eplusout.mdd'),
                fpath(out_dir, 'eplusout.mdd.diff'))), TextDifferences.MDD)
        if self.both_files_exist(case_result_dir_1, case_result_dir_2, 'eplusout.mtd'):
            entry.add_text_differences(TextDifferences(self.diff_text_files(
                fpath(case_result_dir_1, 'eplusout.mtd'),
                fpath(case_result_dir_2, 'eplusout.mtd'),
                fpath(out_dir, 'eplusout.mtd.diff'))), TextDifferences.MTD)
        if self.both_files_exist(case_result_dir_1, case_result_dir_2, 'eplusout.rdd'):
            entry.add_text_differences(TextDifferences(self.diff_text_files(
                fpath(case_result_dir_1, 'eplusout.rdd'),
                fpath(case_result_dir_2, 'eplusout.rdd'),
                fpath(out_dir, 'eplusout.rdd.diff'))), TextDifferences.RDD)
        if self.both_files_exist(case_result_dir_1, case_result_dir_2, 'eplusout.shd'):
            entry.add_text_differences(TextDifferences(self.diff_text_files(
                fpath(case_result_dir_1, 'eplusout.shd'),
                fpath(case_result_dir_2, 'eplusout.shd'),
                fpath(out_dir, 'eplusout.shd.diff'))), TextDifferences.SHD)
        if self.both_files_exist(case_result_dir_1, case_result_dir_2, 'eplusout.err'):
            entry.add_text_differences(TextDifferences(self.diff_text_files(
                fpath(case_result_dir_1, 'eplusout.err'),
                fpath(case_result_dir_2, 'eplusout.err'),
                fpath(out_dir, 'eplusout.err.diff'))), TextDifferences.ERR)
        if self.both_files_exist(case_result_dir_1, case_result_dir_2, 'eplusout.delightin'):
            entry.add_text_differences(TextDifferences(self.diff_text_files(
                fpath(case_result_dir_1, 'eplusout.delightin'),
                fpath(case_result_dir_2, 'eplusout.delightin'),
                fpath(out_dir, 'eplusout.delightin.diff'))), TextDifferences.DLIN)
        if self.both_files_exist(case_result_dir_1, case_result_dir_2, 'eplusout.delightout'):
            entry.add_text_differences(TextDifferences(self.diff_text_files(
                fpath(case_result_dir_1, 'eplusout.delightout'),
                fpath(case_result_dir_2, 'eplusout.delightout'),
                fpath(out_dir, 'eplusout.delightout.diff'))), TextDifferences.DLOUT)

        # return the updated entry
        return entry

    def process_end_file(self, end_path):

        # The end file contains enough info to determine the simulation completion status and runtime
        # success:
        #     EnergyPlus Completed Successfully-- 1 Warning; 0 Severe Errors; Elapsed Time=00hr 00min  1.42sec
        # fatal:
        #     EnergyPlus Terminated--Fatal Error Detected. 0 Warning; 4 Severe Errors; Elapse
        #      d Time=00hr 00min  0.59sec
        # A NEWLINE?? Gotta sanitize it.
        with open(end_path) as f:
            end_contents = f.read().replace("\n", "")

        status = EndErrSummary.STATUS_UNKNOWN
        if "Successfully" in end_contents:
            status = EndErrSummary.STATUS_SUCCESS
        elif "Fatal" in end_contents:
            status = EndErrSummary.STATUS_FATAL
        else:
            return [EndErrSummary.STATUS_UNKNOWN, 0]

        # now process the time string, which is located after a singular equals sign, in the form: 00hr 00min  2.80sec
        # hours and minutes are fixed to 2 decimal points...not sure what happens if it takes over a day...
        # seconds is a floating point that can have 1 or 2 digits before the decimal
        time_string = end_contents.split('=')[1]
        time_string_tokens = time_string.split(' ')
        # remove any blank entries due to duplicated tokens
        time_string_tokens = [x for x in time_string_tokens if x]
        hours = float(time_string_tokens[0][0:2])
        minutes = float(time_string_tokens[1][0:2])
        seconds_term = time_string_tokens[2]
        seconds_index = seconds_term.index('s')
        seconds = float(seconds_term[0:(seconds_index - 1)])
        total_runtime_seconds = hours * 3600.0 + minutes * 60.0 + seconds

        # return results from this end file
        return [status, total_runtime_seconds]

    # diff_logs_for_build creates diff logs between simulations in two build directories
    def diff_logs_for_build(self, buildA, buildB):

        for entry in self.entries:
            try:
                case_result_dir_1 = os.path.join(self.buildA, self.test_output_dir, entry.basename)
                case_result_dir_2 = os.path.join(self.buildB, self.test_output_dir, entry.basename)
                entry = self.process_diffs_for_one_case(entry, case_result_dir_1, case_result_dir_2)
            except Exception as e:
                self.my_print(
                    "Unexpected error occurred in processing diffs for %s, could indicate an E+ crash caused corrupted files" % entry.basename)
                self.my_print("Message: %s" % e)
            finally:
                self.my_diffcompleted(entry.basename)

    def print_summary_of_entries(self):
        # for entry in self.entries:
        # self.my_print("Providing summary for: %s" % entry.basename)

        # if entry.has_summary_result:
        # self.my_print(" File HAS a summary result:")
        # self.my_print("  Simulation Completed as: %s" % EndErrSummary.s_status(entry.summary_result.simulation_status))
        # self.my_print("  Simulation took %s seconds" % entry.summary_result.run_time_seconds)
        # else:
        # self.my_print(" File DOES NOT HAVE a summary result.")

        # if entry.has_eso_diffs:
        # self.my_print(" File HAS eso diff summary:")
        # self.my_print("  Diff type: %s" % (entry.eso_diffs.diff_type))
        # self.my_print("  Big diffs? %s" % (entry.eso_diffs.count_of_big_diff > 0))
        # self.my_print("  Small diffs? %s" % (entry.eso_diffs.count_of_small_diff > 0))
        # self.my_print("  # Records: %s" % (entry.eso_diffs.num_records))
        # else:
        # self.my_print(" File DOES NOT HAVE eso diff summary.")

        # if entry.has_mtr_diffs:
        # self.my_print(" File HAS mtr diff summary:")
        # self.my_print("  Diff type: %s" % (entry.mtr_diffs.diff_type))
        # self.my_print("  Big diffs? %s" % (entry.mtr_diffs.count_of_big_diff > 0))
        # self.my_print("  Small diffs? %s" % (entry.mtr_diffs.count_of_small_diff > 0))
        # self.my_print("  # Records: %s" % (entry.mtr_diffs.num_records))
        # else:
        # self.my_print(" File DOES NOT HAVE mtr diff summary.")

        # if entry.has_zsz_diffs:
        # self.my_print(" File HAS zsz diff summary:")
        # self.my_print("  Diff type: %s" % (entry.zsz_diffs.diff_type))
        # self.my_print("  Big diffs? %s" % (entry.zsz_diffs.count_of_big_diff > 0))
        # self.my_print("  Small diffs? %s" % (entry.zsz_diffs.count_of_small_diff > 0))
        # self.my_print("  # Records: %s" % (entry.zsz_diffs.num_records))
        # else:
        # self.my_print(" File DOES NOT HAVE zsz diff summary.")

        # if entry.has_ssz_diffs:
        # self.my_print(" File HAS ssz diff summary:")
        # self.my_print("  Diff type: %s" % (entry.ssz_diffs.diff_type))
        # self.my_print("  Big diffs? %s" % (entry.ssz_diffs.count_of_big_diff > 0))
        # self.my_print("  Small diffs? %s" % (entry.ssz_diffs.count_of_small_diff > 0))
        # self.my_print("  # Records: %s" % (entry.ssz_diffs.num_records))
        # else:
        # self.my_print(" File DOES NOT HAVE ssz diff summary.")

        # if entry.has_table_diffs:
        # self.my_print(" File HAS table diff summary:")
        # self.my_print("  Message: %s" % (entry.table_diffs.msg))
        # self.my_print("  Table count: %s" % (entry.table_diffs.table_count))
        # self.my_print("  Big diffs?: %s" % (entry.table_diffs.bigdiff_count > 0))
        # self.my_print("  Small diffs: %s" % (entry.table_diffs.smalldiff_count > 0))
        # self.my_print("  Equal count: %s" % (entry.table_diffs.equal_count))
        # self.my_print("  String diff count: %s" % (entry.table_diffs.stringdiff_count))
        # self.my_print("  Size error: %s" % (entry.table_diffs.sizeerr_count))
        # self.my_print("  In 2 not 1: %s" % (entry.table_diffs.notin1_count))
        # self.my_print("  In 1 not 2: %s" % (entry.table_diffs.notin2_count))
        # else:
        # self.my_print(" File DOES NOT HAVE table diff summary.")
        pass

    def add_callbacks(self, print_callback, simstarting_callback, casecompleted_callback, simulationscomplete_callback,
                      enderrcompleted_callback, diffcompleted_callback, alldone_callback, cancel_callback):
        self.print_callback = print_callback
        self.starting_callback = simstarting_callback
        self.casecompleted_callback = casecompleted_callback
        self.simulationscomplete_callback = simulationscomplete_callback
        self.enderrcompleted_callback = enderrcompleted_callback
        self.diffcompleted_callback = diffcompleted_callback
        self.alldone_callback = alldone_callback
        self.cancel_callback = cancel_callback

    def my_print(self, msg):
        if self.print_callback:
            self.print_callback(msg)
            # print(msg) #can uncomment to debug
        else:
            print(msg)

    def my_starting(self, number_of_builds, number_of_cases_per_build):
        if self.starting_callback:
            self.starting_callback(number_of_builds, number_of_cases_per_build)
        else:
            self.my_print("Starting runtests, # builds = %i, # cases per build = %i" % (
            number_of_builds, number_of_cases_per_build))

    def my_casecompleted(self, test_case_completed_instance):
        if self.casecompleted_callback:
            self.casecompleted_callback(test_case_completed_instance)
        else:
            self.my_print("Case complete: %s : %s" % (
            test_case_completed_instance.run_directory, test_case_completed_instance.case_name))

    def my_simulationscomplete(self):
        if self.simulationscomplete_callback:
            self.simulationscomplete_callback()
        else:
            self.my_print("Completed all simulations")

    def my_enderrcompleted(self, build_name, case_name):
        if self.enderrcompleted_callback:
            self.enderrcompleted_callback(build_name, case_name)
        else:
            self.my_print("Completed end/err processing: %s : %s" % (build_name, case_name))

    def my_diffcompleted(self, case_name):
        if self.diffcompleted_callback:
            self.diffcompleted_callback(case_name)
        else:
            self.my_print("Completed diffing case: %s" % case_name)

    def my_alldone(self, results):
        if self.alldone_callback:
            self.alldone_callback(results)
        else:
            self.my_print("Completed runtests")

    def my_cancelled(self):
        if self.cancel_callback:
            self.cancel_callback()
        else:
            self.my_print("Cancelling runtests...")

    def interrupt_please(self):
        self.id_like_to_stop_now = True


if __name__ == "__main__":

    # For ALL runs use BuildA
    base = SingleBuildDirectory(directory_path="/home/elee/EnergyPlus/Builds/Releases/8.1.0.009",
                                executable_name="8.1.0.009_ifort_release",
                                run_this_directory=True)

    # If using ReverseDD, builB can just be None
    mod = SingleBuildDirectory(directory_path="/home/elee/EnergyPlus/Builds/Releases/8.2.0.001",
                               executable_name="8.2.0.001_ifort_release",
                               run_this_directory=True)

    # Do a single test run...
    DoASingleTestRun = False

    # Build the list of files to run here:
    entries = []
    with open('Scripts/files_to_run.txt') as f:  # need to ask for this name separately
        for entry in f:
            if entry.strip() == "":
                continue
            if entry[0] == '!':
                continue
            basename, epw = '', ''
            tokens = entry.split(' ')
            basename = tokens[0].strip()
            if len(tokens) > 1:
                epw = tokens[1].strip()
            else:
                epw = None
            entries.append(TestEntry(basename, epw))
            if DoASingleTestRun:
                break

    # Build the run configuration
    RunConfig = TestRunConfiguration(run_mathdiff=True,
                                     do_composite_err=True,
                                     force_run_type=ForceRunType.NONE,  # ANNUAL, DD, NONE, REVERSEDD
                                     single_test_run=DoASingleTestRun,
                                     eplus_install_path='/home/elee/EnergyPlus/EnergyPlus-8-1-0',
                                     num_threads=3,
                                     report_freq=ReportingFreq.HOURLY,
                                     buildA=base,
                                     buildB=mod)

    # instantiate the test suite
    Runner = TestSuiteRunner(RunConfig, entries)

    # Run it
    Runner.run_test_suite()
