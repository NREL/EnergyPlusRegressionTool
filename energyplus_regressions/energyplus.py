#!/usr/bin/env python
import glob
from os import chdir, getcwd, rename, environ
from pathlib import Path
import shutil
import subprocess

from energyplus_regressions.builds.base import BuildTree
from energyplus_regressions.structures import ForceRunType

script_dir = Path(__file__).resolve().parent


class ExecutionArguments:
    def __init__(self, build_tree: BuildTree, entry_name: str, test_run_directory: Path,
                 run_type, min_reporting_freq, this_parametric_file, weather_file_name: str):
        self.build_tree = build_tree
        self.entry_name = entry_name
        self.test_run_directory = test_run_directory
        self.run_type = run_type
        self.min_reporting_freq = min_reporting_freq
        self.this_parametric_file = this_parametric_file
        self.weather_file_name = weather_file_name


# noinspection PyBroadException
def execute_energyplus(e_args: ExecutionArguments):
    # set up a few paths
    energyplus = e_args.build_tree.energyplus
    basement = e_args.build_tree.basement
    idd_path = e_args.build_tree.idd_path
    slab = e_args.build_tree.slab
    basementidd = e_args.build_tree.basementidd
    slabidd = e_args.build_tree.slabidd
    expandobjects = e_args.build_tree.expandobjects
    epmacro = e_args.build_tree.epmacro
    readvars = e_args.build_tree.readvars
    parametric = e_args.build_tree.parametric

    # Save the current path so we can go back here
    start_path = getcwd()

    std_out = b""
    std_err = b""

    try:

        new_idd_path = e_args.test_run_directory / 'Energy+.idd'
        shutil.copy(idd_path, new_idd_path)

        # Copy the weather file into the simulation directory
        if e_args.weather_file_name:
            shutil.copy(e_args.weather_file_name, e_args.test_run_directory / 'in.epw')

        # Switch to the simulation directory
        chdir(e_args.test_run_directory)

        # Run EPMacro as necessary
        idf_file = e_args.test_run_directory / 'in.idf'
        expanded_file = e_args.test_run_directory / 'expanded.idf'
        imf_path = e_args.test_run_directory / 'in.imf'
        ght_file = e_args.test_run_directory / 'GHTIn.idf'
        basement_file = e_args.test_run_directory / 'BasementGHTIn.idf'
        epjson_file = e_args.test_run_directory / 'in.epJSON'
        rvi_file = e_args.test_run_directory / 'in.rvi'
        mvi_file = e_args.test_run_directory / 'in.mvi'

        if imf_path.exists():
            with imf_path.open('rb') as f:
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
            macro_run = subprocess.Popen(
                str(epmacro), shell=True, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
            o, e = macro_run.communicate()
            std_out += o
            std_err += e
            rename('out.idf', 'in.idf')

        # Run Preprocessor -- after EPMacro?
        if e_args.this_parametric_file:
            parametric_run = subprocess.Popen(
                str(parametric) + ' in.idf', shell=True, stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
            o, e = parametric_run.communicate()
            std_out += o
            std_err += e
            candidate_files = glob.glob('in-*.idf')
            if len(candidate_files) > 0:
                file_to_run_here = sorted(candidate_files)[0]
                if idf_file.exists():
                    idf_file.unlink()
                rename(file_to_run_here, idf_file)
            else:
                return [e_args.build_tree.build_dir, e_args.entry_name, False, False, "Issue with Parametrics"]

        # Run ExpandObjects and process as necessary, but not for epJSON files!
        if idf_file.exists():
            expand_objects_run = subprocess.Popen(
                str(expandobjects), shell=True, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
            o, e = expand_objects_run.communicate()
            std_out += o
            std_err += e
            if expanded_file.exists():
                if idf_file.exists():
                    idf_file.unlink()
                rename(expanded_file, idf_file)

                if basement_file.exists():
                    shutil.copy(basementidd, e_args.test_run_directory)
                    basement_environment = environ.copy()
                    basement_environment['CI_BASEMENT_NUMYEARS'] = '2'
                    basement_run = subprocess.Popen(
                        str(basement), shell=True, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE, env=basement_environment
                    )
                    o, e = basement_run.communicate()
                    std_out += o
                    std_err += e
                    with open('EPObjects.TXT') as f:
                        append_text = f.read()
                    with open('in.idf', 'a') as f:
                        f.write("\n%s\n" % append_text)
                    (e_args.test_run_directory / 'RunINPUT.TXT').unlink()
                    (e_args.test_run_directory / 'RunDEBUGOUT.TXT').unlink()
                    (e_args.test_run_directory / 'EPObjects.TXT').unlink()
                    (e_args.test_run_directory / 'BasementGHTIn.idf').unlink()
                    (e_args.test_run_directory / 'MonthlyResults.csv').unlink()
                    (e_args.test_run_directory / 'BasementGHT.idd').unlink()

                if ght_file.exists():
                    shutil.copy(slabidd, e_args.test_run_directory)
                    slab_run = subprocess.Popen(
                        str(slab), shell=True, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE
                    )
                    o, e = slab_run.communicate()
                    std_out += o
                    std_err += e
                    with open('SLABSurfaceTemps.TXT') as f:
                        append_text = f.read()
                    with open('in.idf', 'a') as f:
                        f.write("\n%s\n" % append_text)
                    (e_args.test_run_directory / 'SLABINP.TXT').unlink()
                    (e_args.test_run_directory / 'GHTIn.idf').unlink()
                    (e_args.test_run_directory / 'SLABSurfaceTemps.TXT').unlink()
                    (e_args.test_run_directory / 'SLABSplit Surface Temps.TXT').unlink()
                    (e_args.test_run_directory / 'SlabGHT.idd').unlink()

        # Set up environment
        environ["DISPLAYADVANCEDREPORTVARIABLES"] = "YES"
        environ["DISPLAYALLWARNINGS"] = "YES"
        if e_args.run_type == ForceRunType.DD:
            environ["DDONLY"] = "Y"
            environ["REVERSEDD"] = ""
            environ["FULLANNUALRUN"] = ""
        elif e_args.run_type == ForceRunType.ANNUAL:
            environ["DDONLY"] = ""
            environ["REVERSEDD"] = ""
            environ["FULLANNUALRUN"] = "Y"
        elif e_args.run_type == ForceRunType.NONE:
            environ["DDONLY"] = ""
            environ["REVERSEDD"] = ""
            environ["FULLANNUALRUN"] = ""
        else:  # pragma: no cover
            # it feels weird to try to test this path...have to set run_type to something invalid?
            # should we just eliminate this else?
            pass  # do nothing?

        # use the user-entered minimum reporting frequency
        #  (useful for limiting to daily outputs for annual simulation, etc.)
        environ["MINREPORTFREQUENCY"] = e_args.min_reporting_freq.upper()

        # Execute EnergyPlus
        try:
            command_line = str(energyplus)
            if epjson_file.exists():
                command_line += ' in.epJSON'
            std_out += subprocess.check_output(
                command_line, shell=True, stdin=subprocess.DEVNULL, stderr=subprocess.PIPE
            )
        except subprocess.CalledProcessError as e:  # pragma: no cover
            ...
            # so I can verify that I hit this during the test_case_b_crash test, but if I just have the return in
            #  here alone, it shows as missing on the coverage...wonky
            return [e_args.build_tree.build_dir, e_args.entry_name, False, False, str(e)]

        # Execute readvars
        if rvi_file.exists():
            csv_run = subprocess.Popen(
                str(readvars) + ' in.rvi', shell=True, stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
        else:
            csv_run = subprocess.Popen(
                str(readvars), shell=True, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        o, e = csv_run.communicate()
        std_out += o
        std_err += e
        if mvi_file.exists():
            mtr_run = subprocess.Popen(
                str(readvars) + ' in.mvi', shell=True, stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
        else:
            with mvi_file.open('w') as f:
                f.write("eplusout.mtr\n")
                f.write("eplusmtr.csv\n")
            mtr_run = subprocess.Popen(
                str(readvars) + ' in.mvi', shell=True, stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
        o, e = mtr_run.communicate()
        std_out += o
        std_err += e

        if len(std_out) > 0:
            with open('eplusout.stdout', 'w') as f:
                f.write(std_out.decode('utf-8'))
        if len(std_err) > 0:
            with open('eplusout.stderr', 'w') as f:
                f.write(std_err.decode('utf-8'))

        new_idd_path.unlink()
        return [e_args.build_tree.build_dir, e_args.entry_name, True, False]

    except Exception as e:
        print("**" + str(e))
        return [e_args.build_tree.build_dir, e_args.entry_name, False, False, str(e)]

    finally:
        chdir(start_path)
