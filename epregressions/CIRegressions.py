#!/usr/bin/python

import json
import sys
import os, shutil
import subprocess
import random

from runtests import *
from Structures import *

if len(sys.argv) < 6:
    print("syntax: %s <num_processes> <base_install_dir> <base_src_dir> <mod_install_dir> <mod_src_dir> [count] [random]" % sys.argv[0])
    sys.exit(1)

path = os.path.dirname(__file__)
script_dir = os.path.abspath(path)

num_processes = sys.argv[1]
base_test_dir = sys.argv[2]
base_src_dir = sys.argv[3]
mod_test_dir = sys.argv[4]
mod_src_dir = sys.argv[5]

do_random = False
randomcount = -1

if len(sys.argv) >= 7:
    randomcount = int(sys.argv[6])

if len(sys.argv) == 8:
    do_random = sys.argv[7].lower() == "true"

if not os.path.isdir(os.path.join(base_test_dir, "InputFiles")):
    shutil.copytree(os.path.join(base_src_dir, "testfiles"), os.path.join(base_test_dir, "InputFiles"))

if not os.path.isdir(os.path.join(mod_test_dir, "InputFiles")):
    shutil.copytree(os.path.join(mod_src_dir, "testfiles"), os.path.join(mod_test_dir, "InputFiles"))

# For ALL runs use BuildA
base   = SingleBuildDirectory(directory_path     = base_test_dir, 
                              executable_name    = "EnergyPlus", 
                              run_this_directory = True)
# If using ReverseDD, buildB can just be None
mod    = SingleBuildDirectory(directory_path     = mod_test_dir, 
                              executable_name    = "EnergyPlus", 
                              run_this_directory = True)

# Build the list of files to run here:
print("Processing file list")
entries = []
with open(os.path.join(script_dir, "files_to_run.txt")) as f:  
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


if do_random:
    random.shuffle(entries)

if randomcount > -1:
    entries = entries[0:randomcount]

# Build the run configuration
print("Instantiating arguments for runtests")

# TODO Let each build dir provide its own tools
ep_install_path = mod_test_dir

RunConfig = TestRunConfiguration(run_mathdiff       = True, 
                                 do_composite_err   = True, 
                                 force_run_type     = ForceRunType.DD, #ANNUAL, DD, NONE, REVERSEDD
                                 single_test_run    = True, 
                                 eplus_install_path = ep_install_path,
                                 num_threads        = num_processes,
                                 report_freq        = ReportingFreq.DAILY,
                                 buildA = base, 
                                 buildB = mod)

# instantiate the test suite
print("Instantiating runtests")
Runner = TestSuiteRunner(RunConfig, entries)

# Run it
print("Running test suite")
Runner.run_test_suite()

print("ALL DONE")

f = open('results.json', 'w')
f.write(json.dumps(entries, default=lambda o: o.__dict__, sort_keys=True, indent=4))

idfskiplist = ['HAMT_DailyProfileReport', 'HAMT_HourlyProfileReport', 'HVACTemplate-5ZoneBaseboardHeat', 'HVACTemplate-5ZoneConstantVolumeChillerBoiler', 'HVACTemplate-5ZoneDualDuct', 'HVACTemplate-5ZoneFanCoil-DOAS', 'HVACTemplate-5ZoneFanCoil', 'HVACTemplate-5ZoneFurnaceDX', 'HVACTemplate-5ZonePTAC-DOAS', 'HVACTemplate-5ZonePTAC', 'HVACTemplate-5ZonePTHP', 'HVACTemplate-5ZonePackagedVAV', 'HVACTemplate-5ZonePurchAir', 'HVACTemplate-5ZoneUnitaryHeatPump', 'HVACTemplate-5ZoneUnitarySystem', 'HVACTemplate-5ZoneVAVFanPowered', 'HVACTemplate-5ZoneVAVWaterCooled-ObjectReference', 'HVACTemplate-5ZoneVAVWaterCooled', 'HVACTemplate-5ZoneVRF', 'HVACTemplate-5ZoneWaterToAirHeatPumpTowerBoiler', 'LBuilding-G000', 'LBuilding-G090', 'LBuilding-G180', 'LBuilding-G270', 'LBuildingAppGRotPar', 'EMSTestMathAndKill', '1ZoneParameterAspect', 'ParametricInsulation-5ZoneAirCooled', '1ZoneUncontrolled_win_1', '1ZoneUncontrolled_win_2', '5ZoneTDV', '5ZoneAirCooledWithSlab', 'LgOffVAVusingBasement', 'DElight-Detailed-Comparison', 'DElightCFSLightShelf', 'DElightCFSWindow', '_ExternalInterface-actuator', '_ExternalInterface-functionalmockupunit-to-actuator']

for test in entries:
    time = 0

    msg = ""

    if test.has_summary_result:
        time = test.summary_result.run_time_seconds
        if test.summary_result.simulation_status_case1 != EndErrSummary.STATUS_SUCCESS or test.summary_result.simulation_status_case2 != EndErrSummary.STATUS_SUCCESS:
            status = "failed"
            msg += "Simulation Failed."

    if test.basename in idfskiplist:
        print("%s;%s;%s;%s" % (test.basename, "info", str(time), "Test results skipped, test requires tools not yet provided"));
        continue


    if test.has_bnd_diffs and (test.bnd_diffs.diff_type != TextDifferences.EQUAL):
        msg += "Has bnd diffs. "

    if test.has_eio_diffs and (test.eio_diffs.diff_type != TextDifferences.EQUAL):
        msg += "Has eio diffs. "

    if test.has_eso_diffs and (test.eso_diffs.diff_type != TextDifferences.EQUAL):
        msg += "Has eso diffs. "

    if test.has_mtr_diffs and (test.mtr_diffs.diff_type != TextDifferences.EQUAL):
        msg += "Has mtr diffs. "

    if test.has_ssz_diffs and (test.ssz_diffs.diff_type != TextDifferences.EQUAL):
        msg += "Has ssz diffs. "

    if test.has_table_diffs and test.table_diffs.bigdiff_count > 0:
        msg += "Has big table differences. "

    if test.has_zsz_diffs and (test.zsz_diffs.diff_type != TextDifferences.EQUAL):
        msg += "Has zsz diffs. "


    status = "passed"

    if msg != "":
        status = "warning"


    print("%s;%s;%s;%s" % (test.basename, status, str(time), msg));
        


    
