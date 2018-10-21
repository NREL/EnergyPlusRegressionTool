File & Directory Structure
==========================

The program itself is set up to run directly from its repository, and operate
directly on EnergyPlus build folders.  There is no extra burden required to
move files around (anymore).  The build folder is expected to have the
entire set of binaries, including all Fortran tools.  So when configuring the
build, make sure to set up ``BUILD_FORTRAN``.

Test Directory
--------------

This program runs regression testing for 2 different builds of EnergyPlus
versions of an executable. The regression tool will verify that the build
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
