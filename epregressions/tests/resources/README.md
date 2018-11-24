This folder contains a bunch of resources for running tests.
These are extremely lightweight executable scripts that mimic the actual E+ toolchain.
There are also other files in here such as example weather files and E+ run files.

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
