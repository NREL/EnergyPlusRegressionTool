#!/usr/bin/env python
import glob
import os
import shutil
import subprocess

from epregressions.structures import ForceRunType

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


def test_dir_path(test_path, rel_path):
    return os.path.join(test_path, rel_path)


# noinspection PyBroadException
def execute_energyplus(e_args: ExecutionArguments):
    # setup a few paths
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

    d = e_args.test_run_directory

    std_out = b""

    try:

        new_idd_path = test_dir_path(d, 'Energy+.idd')
        shutil.copy(idd_path, new_idd_path)

        # Copy the weather file into the simulation directory
        if e_args.run_type != ForceRunType.DD:
            shutil.copy(e_args.weather_file_name, test_dir_path(d, 'in.epw'))

        # Run EPMacro as necessary
        imf_path = test_dir_path(d, 'in.imf')
        if os.path.exists(imf_path):
            with open(imf_path, 'rb') as f:
                lines = f.readlines()
            newlines = []
            for line in lines:
                encoded_line = line.decode('UTF-8', 'ignore')
                if '##fileprefix' in encoded_line:
                    newlines.append('')
                else:
                    newlines.append(encoded_line)
            with open(imf_path, 'w') as f:
                for line in newlines:
                    f.write(line)
            try:
                std_out += subprocess.check_output([epmacro], cwd=d)
            except subprocess.CalledProcessError:
                ...  # it wasn't doing anything before, so not catching anything here for now
            os.rename(test_dir_path(d, 'out.idf'), test_dir_path(d, 'in.idf'))

        # Run Preprocessor -- after EPMacro?
        if e_args.this_parametric_file:
            try:
                std_out += subprocess.check_output([parametric, 'in.idf'], cwd=e_args.test_run_directory)
            except subprocess.CalledProcessError:
                ...  # it wasn't doing anything before, so not catching anything here for now
            candidate_files = glob.glob(test_dir_path(d, 'in-*.idf'))
            if len(candidate_files) > 0:
                file_to_run_here = sorted(candidate_files)[0]
                idf_path = test_dir_path(d, 'in.idf')
                if os.path.exists(idf_path):
                    os.remove(idf_path)
                os.rename(file_to_run_here, idf_path)
            else:
                return [e_args.build_tree['build_dir'], e_args.entry_name, False, False]

        # Run ExpandObjects and process as necessary
        try:
            std_out += subprocess.check_output([expandobjects], cwd=e_args.test_run_directory)
        except subprocess.CalledProcessError:
            ...  # it wasn't doing anything before, so not catching anything for now
        expanded_idf_path = test_dir_path(d, 'expanded.idf')
        idf_path = test_dir_path(d, 'in.idf')
        if os.path.exists(expanded_idf_path):
            if os.path.exists(idf_path):
                os.remove(idf_path)
            os.rename(expanded_idf_path, idf_path)

            if os.path.exists(test_dir_path(d, 'BasementGHTIn.idf')):
                shutil.copy(basementidd, e_args.test_run_directory)
                basement_environment = os.environ.copy()
                basement_environment['CI_BASEMENT_NUMYEARS'] = '2'
                try:
                    std_out += subprocess.check_output(
                        [basement], env=basement_environment, cwd=e_args.test_run_directory
                    )
                except subprocess.CalledProcessError:
                    ...  # it wasn't catching anything before, so not catching anything for now
                with open(test_dir_path(d, 'EPObjects.TXT')) as f:
                    append_text = f.read()
                with open(idf_path, 'a') as f:
                    f.write("\n%s\n" % append_text)
                files_to_remove = [
                    'RunINPUT.TXT', 'RunDEBUGOUT.TXT', 'EPObjects.TXT',
                    'BasementGHTIn.idf', 'MonthlyResults.csv', 'BasementGHT.idd'
                ]
                for file_to_remove in files_to_remove:
                    os.remove(test_dir_path(d, file_to_remove))

            if os.path.exists(test_dir_path(d, 'GHTIn.idf')):
                shutil.copy(slabidd, e_args.test_run_directory)
                try:
                    std_out += subprocess.check_output([slab], cwd=e_args.test_run_directory)
                except subprocess.CalledProcessError:
                    ...  # it wasn't doing anything before, so not catching anything for now
                with open(test_dir_path(d, 'SLABSurfaceTemps.TXT')) as f:
                    append_text = f.read()
                with open(test_dir_path(d, 'in.idf'), 'a') as f:
                    f.write("\n%s\n" % append_text)
                files_to_remove = [
                    'SLABINP.TXT', 'GHTIn.idf', 'SLABSurfaceTemps.TXT', 'SLABSplit Surface Temps.TXT', 'SlabGHT.idd'
                ]
                for file_to_remove in files_to_remove:
                    os.remove(test_dir_path(d, file_to_remove))

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
            std_out += subprocess.check_output([energyplus], cwd=e_args.test_run_directory)
        except subprocess.CalledProcessError:  # pragma: no cover
            ...
            # so I can verify that I hit this during the test_case_b_crash test, but if I just have the return in
            #  here alone, it shows as missing on the coverage...wonky
            return [e_args.build_tree['build_dir'], e_args.entry_name, False, False]

        # Execute readvars
        if os.path.exists(test_dir_path(d, 'in.rvi')):
            try:
                std_out += subprocess.check_output([readvars, 'in.rvi'], cwd=e_args.test_run_directory)
            except subprocess.CalledProcessError:
                ...  # it wasn't catching anything before, so not catching anything for now
        else:
            try:
                std_out += subprocess.check_output([readvars], cwd=e_args.test_run_directory)
            except subprocess.CalledProcessError:
                ...  # it wasn't doing anything before, so not catching anything for now
        if os.path.exists(test_dir_path(d, 'in.mvi')):
            try:
                std_out += subprocess.check_output([readvars, 'in.mvi'], cwd=e_args.test_run_directory)
            except subprocess.CalledProcessError:
                ...  # it wasn't doing anything before, so not catching anything for now
        else:
            with open(test_dir_path(d, 'in.mvi'), 'w') as f:
                f.write("eplusout.mtr\n")
                f.write("eplusmtr.csv\n")
            try:
                std_out += subprocess.check_output([readvars, 'in.mvi'])
            except subprocess.CalledProcessError:
                ...  # it wasn't doing anything before, so not catching anything for now
        with open(test_dir_path(d, 'eplusout.stdout'), 'w') as f:
            f.write(std_out.decode(encoding='utf-8', errors='ignore'))
        os.remove(new_idd_path)

        return [e_args.build_tree['build_dir'], e_args.entry_name, True, False]

    except Exception:
        return [e_args.build_tree['build_dir'], e_args.entry_name, False, False]
