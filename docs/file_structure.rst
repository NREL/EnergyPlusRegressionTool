File & Directory Structure
==========================

The program itself is set up to run directly from its repository, and operate
directly on EnergyPlus build or install folders.  There is no extra steps
required to move files around.  The build folder is expected to have the
entire set of binaries, including all Fortran tools.  So when configuring the
build, make sure to set up ``BUILD_FORTRAN``.  If these tools are not
built, the regressions will emit a warning that you can accept, but note that
the program has minimal value if it cannot find and run the Fortran tools.

Test Directory
--------------

This program runs regression testing for 2 different builds or installs of
EnergyPlus. The regression tool will verify that the build
folder looks satisfactory before starting the runs.

When the test is completed, test results will be contained in a Tests
directory in the base case folder.  The folder name will be one of the following:

Tests
    This will be created if the test suite run did not force a specific
    run configuration

Tests-DDOnly
    This will be created if the test suite forced all input files to run
    sizing periods only

Tests-Annual
    This will be created if the test suite forced all input files to run
    annual simulations
