#!/usr/bin/env python
from __future__ import print_function

import glob
import os
import shutil
import subprocess
from multiprocessing import current_process

from epregressions.structures import ForceRunType

path = os.path.dirname(__file__)
script_dir = os.path.abspath(path)


def execute_energyplus(build_tree, entry_name, test_run_directory,
                       run_type, min_reporting_freq, this_parametric_file, weather_file_name):

    # setup a few paths
    energyplus = build_tree['energyplus']
    basement = build_tree['basement']
    idd_path = build_tree['idd_path']
    slab = build_tree['slab']
    basementidd = build_tree['basementidd']
    slabidd = build_tree['slabidd']
    expandobjects = build_tree['expandobjects']
    epmacro = build_tree['epmacro']
    readvars = build_tree['readvars']
    parametric = build_tree['parametric']

    # Save the current path so we can go back here
    start_path = os.getcwd()

    try:
        shutil.copy(idd_path, os.path.join(test_run_directory, 'Energy+.idd'))

        # Copy the weather file into the simulation directory
        if run_type != ForceRunType.DD:
            shutil.copy(weather_file_name, os.path.join(test_run_directory, 'in.epw'))

        # Switch to the simulation directory
        os.chdir(test_run_directory)

        # Run EPMacro as necessary
        if os.path.exists('in.imf'):
            with open('in.imf', 'rb') as f:
                lines = f.readlines()
            newlines = []
            for line in lines:
                encoded_line = line.decode('UTF-8', 'ignore')
                if '##fileprefix' in encoded_line:
                    newlines.append('')
                else:
                    newlines.append(encoded_line)
            with open('in.imf', 'w') as f:
                for line in newlines:
                    f.write(line)
            macro_run = subprocess.Popen(epmacro, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            macro_run.communicate()
            os.rename('out.idf', 'in.idf')

        # Run Preprocessor -- after EPMacro?
        if this_parametric_file:
            parametric_run = subprocess.Popen(parametric + ' in.idf', shell=True, stdout=subprocess.PIPE,
                                              stderr=subprocess.PIPE)
            parametric_run.communicate()
            candidate_files = glob.glob('in-*.idf')
            if len(candidate_files) > 0:
                file_to_run_here = sorted(candidate_files)[0]
                if os.path.exists('in.idf'):
                    os.remove('in.idf')
                os.rename(file_to_run_here, 'in.idf')
            else:
                return [build_tree['build_dir'], entry_name, False, False, current_process().name]

        # Run ExpandObjects and process as necessary
        expand_objects_run = subprocess.Popen(expandobjects, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        expand_objects_run.communicate()
        if os.path.exists('expanded.idf'):
            if os.path.exists('in.idf'):
                os.remove('in.idf')
            os.rename('expanded.idf', 'in.idf')

            if os.path.exists('BasementGHTIn.idf'):
                shutil.copy(basementidd, test_run_directory)
                basement_environment = os.environ.copy()
                basement_environment['CI_BASEMENT_NUMYEARS'] = '2'
                basement_run = subprocess.Popen(
                    basement, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=basement_environment
                )
                basement_run.communicate()
                with open('EPObjects.TXT') as f:
                    append_text = f.read()
                with open('in.idf', 'a') as f:
                    f.write("\n%s\n" % append_text)
                os.remove('RunINPUT.TXT')
                os.remove('RunDEBUGOUT.TXT')
                os.remove('EPObjects.TXT')
                os.remove('BasementGHTIn.idf')
                os.remove('MonthlyResults.csv')
                os.remove('BasementGHT.idd')

            if os.path.exists('GHTIn.idf'):
                shutil.copy(slabidd, test_run_directory)
                slab_run = subprocess.Popen(slab, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                slab_run.communicate()
                with open('SLABSurfaceTemps.TXT') as f:
                    append_text = f.read()
                with open('in.idf', 'a') as f:
                    f.write("\n%s\n" % append_text)
                os.remove('SLABINP.TXT')
                os.remove('GHTIn.idf')
                os.remove('SLABSurfaceTemps.TXT')
                os.remove('SLABSplit Surface Temps.TXT')
                os.remove('SlabGHT.idd')

        # Set up environment
        os.environ["DISPLAYADVANCEDREPORTVARIABLES"] = "YES"
        os.environ["DISPLAYALLWARNINGS"] = "YES"
        if run_type == ForceRunType.DD:
            os.environ["DDONLY"] = "Y"
            os.environ["REVERSEDD"] = ""
            os.environ["FULLANNUALRUN"] = ""
        elif run_type == ForceRunType.ANNUAL:
            os.environ["DDONLY"] = ""
            os.environ["REVERSEDD"] = ""
            os.environ["FULLANNUALRUN"] = "Y"
        elif run_type == ForceRunType.NONE:
            os.environ["DDONLY"] = ""
            os.environ["REVERSEDD"] = ""
            os.environ["FULLANNUALRUN"] = ""
        else:
            pass
            # nothing

        # use the user-entered minimum reporting frequency
        #  (useful for limiting to daily outputs for annual simulation, etc.)
        os.environ["MINREPORTFREQUENCY"] = min_reporting_freq.upper()

        # Execute EnergyPlus
        eplus_run = subprocess.Popen(energyplus, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        eplus_run.communicate()

        # Execute readvars
        if os.path.exists('in.rvi'):
            csv_run = subprocess.Popen(readvars + ' in.rvi', shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        else:
            csv_run = subprocess.Popen(readvars, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        csv_run.communicate()
        if os.path.exists('in.mvi'):
            mtr_run = subprocess.Popen(readvars + ' in.mvi', shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        else:
            with open('in.mvi', 'w') as f:
                f.write("eplusout.mtr\n")
                f.write("eplusmtr.csv\n")
            mtr_run = subprocess.Popen(readvars + ' in.mvi', shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        mtr_run.communicate()

        os.remove('Energy+.idd')
        return [build_tree['build_dir'], entry_name, True, False, current_process().name]

    except Exception as e:
        with open("aa_testSuite_error.txt", 'w') as f:
            print(e, file=f)
        return [build_tree['build_dir'], entry_name, False, False, current_process().name]

    finally:
        os.chdir(start_path)
