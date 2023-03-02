#!/usr/bin/env python
import glob
import os
import shutil
import subprocess

from energyplus_regressions.structures import ForceRunType

path = os.path.dirname(__file__)
script_dir = os.path.abspath(path)


class ExecutionArguments:
    def __init__(self, build_tree, entry_name, test_run_directory,
                 run_type, min_reporting_freq, this_parametric_file, weather_file_name):
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
    energyplus = e_args.build_tree['energyplus']
    basement = e_args.build_tree['basement']
    idd_path = e_args.build_tree['idd_path']
    slab = e_args.build_tree['slab']
    basementidd = e_args.build_tree['basementidd']
    slabidd = e_args.build_tree['slabidd']
    expandobjects = e_args.build_tree['expandobjects']
    epmacro = e_args.build_tree['epmacro']
    readvars = e_args.build_tree['readvars']
    parametric = e_args.build_tree['parametric']

    # Save the current path so we can go back here
    start_path = os.getcwd()

    std_out = b""
    std_err = b""

    try:

        new_idd_path = os.path.join(e_args.test_run_directory, 'Energy+.idd')
        shutil.copy(idd_path, new_idd_path)

        # Copy the weather file into the simulation directory
        if e_args.weather_file_name:
            shutil.copy(e_args.weather_file_name, os.path.join(e_args.test_run_directory, 'in.epw'))

        # Switch to the simulation directory
        os.chdir(e_args.test_run_directory)

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
            macro_run = subprocess.Popen(
                epmacro, shell=True, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
            o, e = macro_run.communicate()
            std_out += o
            std_err += e
            os.rename('out.idf', 'in.idf')

        # Run Preprocessor -- after EPMacro?
        if e_args.this_parametric_file:
            parametric_run = subprocess.Popen(
                parametric + ' in.idf', shell=True, stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
            o, e = parametric_run.communicate()
            std_out += o
            std_err += e
            candidate_files = glob.glob('in-*.idf')
            if len(candidate_files) > 0:
                file_to_run_here = sorted(candidate_files)[0]
                if os.path.exists('in.idf'):
                    os.remove('in.idf')
                os.rename(file_to_run_here, 'in.idf')
            else:
                return [e_args.build_tree['build_dir'], e_args.entry_name, False, False, "Issue with Parametrics"]

        # Run ExpandObjects and process as necessary, but not for epJSON files!
        if os.path.exists('in.idf'):
            expand_objects_run = subprocess.Popen(
                expandobjects, shell=True, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
            o, e = expand_objects_run.communicate()
            std_out += o
            std_err += e
            if os.path.exists('expanded.idf'):
                if os.path.exists('in.idf'):
                    os.remove('in.idf')
                os.rename('expanded.idf', 'in.idf')

                if os.path.exists('BasementGHTIn.idf'):
                    shutil.copy(basementidd, e_args.test_run_directory)
                    basement_environment = os.environ.copy()
                    basement_environment['CI_BASEMENT_NUMYEARS'] = '2'
                    basement_run = subprocess.Popen(
                        basement, shell=True, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE, env=basement_environment
                    )
                    o, e = basement_run.communicate()
                    std_out += o
                    std_err += e
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
                    shutil.copy(slabidd, e_args.test_run_directory)
                    slab_run = subprocess.Popen(
                        slab, shell=True, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE
                    )
                    o, e = slab_run.communicate()
                    std_out += o
                    std_err += e
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
        if e_args.run_type == ForceRunType.DD:
            os.environ["DDONLY"] = "Y"
            os.environ["REVERSEDD"] = ""
            os.environ["FULLANNUALRUN"] = ""
        elif e_args.run_type == ForceRunType.ANNUAL:
            os.environ["DDONLY"] = ""
            os.environ["REVERSEDD"] = ""
            os.environ["FULLANNUALRUN"] = "Y"
        elif e_args.run_type == ForceRunType.NONE:
            os.environ["DDONLY"] = ""
            os.environ["REVERSEDD"] = ""
            os.environ["FULLANNUALRUN"] = ""
        else:
            pass
            # nothing

        # use the user-entered minimum reporting frequency
        #  (useful for limiting to daily outputs for annual simulation, etc.)
        os.environ["MINREPORTFREQUENCY"] = e_args.min_reporting_freq.upper()

        # Execute EnergyPlus
        try:
            command_line = energyplus
            if os.path.exists('in.epJSON'):
                command_line = energyplus + ' in.epJSON'
            std_out += subprocess.check_output(
                command_line, shell=True, stdin=subprocess.DEVNULL, stderr=subprocess.PIPE
            )
        except subprocess.CalledProcessError as e:  # pragma: no cover
            ...
            # so I can verify that I hit this during the test_case_b_crash test, but if I just have the return in
            #  here alone, it shows as missing on the coverage...wonky
            return [e_args.build_tree['build_dir'], e_args.entry_name, False, False, str(e)]

        # Execute readvars
        if os.path.exists('in.rvi'):
            csv_run = subprocess.Popen(
                readvars + ' in.rvi', shell=True, stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
        else:
            csv_run = subprocess.Popen(
                readvars, shell=True, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        o, e = csv_run.communicate()
        std_out += o
        std_err += e
        if os.path.exists('in.mvi'):
            mtr_run = subprocess.Popen(
                readvars + ' in.mvi', shell=True, stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
        else:
            with open('in.mvi', 'w') as f:
                f.write("eplusout.mtr\n")
                f.write("eplusmtr.csv\n")
            mtr_run = subprocess.Popen(
                readvars + ' in.mvi', shell=True, stdin=subprocess.DEVNULL,
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

        os.remove(new_idd_path)
        return [e_args.build_tree['build_dir'], e_args.entry_name, True, False]

    except Exception as e:
        print("**" + str(e))
        return [e_args.build_tree['build_dir'], e_args.entry_name, False, False, str(e)]

    finally:
        os.chdir(start_path)
