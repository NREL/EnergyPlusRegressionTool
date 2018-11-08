Introduction
============

This file documents the operations required to utilize EnergyPlusRegressions in
doing development and testing. The program consists of a series of
python scripts, that can be utilized in both a command
line/scripted/non-interactive environment, as well as in a graphical
user interface mode.

The current testing includes regression testing of the example files
that are included in EnergyPlus development.

History/Credits
---------------

This program was based on a test suite used at the National Renewable
Energy Laboratory (NREL) that was developed by Kyle Benne and Jason
Turner, and consisted of both ruby and python scripts, including a job
manager to allow multiple threads to run concurrently. Although this
script was at the heart of the inspiration for creating this current
tool, very little of the original code exists.

The mathematical comparisons performed on the EnergyPlus output files
(MathDiff and TableDiff) were developed originally by Santosh Philip and
improved by Amir Roth. Modifications were made to improve interaction
with the test suite tool and to support Python 3, but the core of the
mathematical comparisons remains.

Basic Dependencies
------------------

Before discussing software dependencies, some other dependencies can be
described.

Master CSV file
~~~~~~~~~~~~~~~

In order to determine the list of all idfs available for testing, and
capture details about those files, a master csv file is currently used.
Currently, this file is named “full_file_set_details.csv”, and resides in
the same directory as the run scripts. This csv file currently contains
8 columns that describe features of this input file. Table
[tbl:mastercsvcolumns] describes these columns.

+----------------+--------------------------------+----------------------------------------------------------------------------+
| Column Index   | Column Contents                | Notes                                                                      |
+================+================================+============================================================================+
| 1              | Input file name                | Does not include file extension                                            |
+----------------+--------------------------------+----------------------------------------------------------------------------+
| 2              | Weather file name              | Does not include epw extension                                             |
+----------------+--------------------------------+----------------------------------------------------------------------------+
| 3              | External interface flag        | “Y” if file includes external interface dependence, otherwise blank        |
+----------------+--------------------------------+----------------------------------------------------------------------------+
| 4              | “Ground HT” flag               | “Y” if file includes ground HT preprocessor dependence, otherwise blank    |
+----------------+--------------------------------+----------------------------------------------------------------------------+
| 5              | External dataset flag          | “Y” if file includes external dataset dependence, otherwise blank          |
+----------------+--------------------------------+----------------------------------------------------------------------------+
| 6              | Parametric preprocessor flag   | “Y” if file includes parametric preprocessor dependence, otherwise blank   |
+----------------+--------------------------------+----------------------------------------------------------------------------+
| 7              | Macro flag                     | “Y” if file includes EPMacro definitions, otherwise blank                  |
+----------------+--------------------------------+----------------------------------------------------------------------------+
| 8              | DeLight flag                   | “Y” if file includes DeLight dependence, otherwise blank                   |
+----------------+--------------------------------+----------------------------------------------------------------------------+

Table: Column details in the master csv file used for idf selection

File & Directory Structure
~~~~~~~~~~~~~~~~~~~~~~~~~~

This program operates on EnergyPlus build folders.  It relies on the
build folders having been set up by CMake, as it parses the CMakeCache
to get access to the base source directory.  With the build and source
directories available, the program has everything it needs to run.

Software Dependencies
---------------------

The program requires python, gtk, and pygtk.

Python Version
~~~~~~~~~~~~~~

This script was originally developed to be cross-python-version.
However, handling differences in some libraries led to a higher amount
of maintenance, and so it was originally locked at Python 2.7.  HOWEVER,
in 2018, the program was updated and is now locked at Python 3.6.  It
should be compatible with any 3.x as far as I know. This
program has ONLY been tested on Ubuntu 18.04 at this point.  I have
intentions on looking at getting it working on Windows, but it won't be
soon.  Any developer who wants to use this should just build/test on
an Ubuntu VM.

Installation: Ubuntu
~~~~~~~~~~~~~~~~~~~~

PyGTK has awesome installation instructions for setting up a PyGTK
development environment `here <https://pygobject.readthedocs.io/en/latest/getting_started.html>`_.
I won't be replicating instructions here.  Just follow the Ubuntu
instructions and you'll be all set.

Once you have that installed, run ``pip3 install requirements.txt`` at
the root of this repo and it will install the Python packages needed.

If you are running a VM, and this is the only project you'll work on with
that VM, then you are done.  If you want to set up a virtual environment
to avoid package clashing with other projects, getting PyGTK to play well there
is a bit funny.  But again, PyGTK has great instructions for it.  Follow
them `at this site <https://pygobject.readthedocs.io/en/latest/devguide/dev_environ.html#devenv>`_.

Installation: Windows 7
~~~~~~~~~~~~~~~~~~~~~~~

PyGTK has instructions for all three platforms, so probably just
follow the links in the Ubuntu section.  But I have not confirmed it.

Regression Testing Note
-----------------------

For EnergyPlus regression testing, two different executables are
utilized in comparing a set of example files. The output of each run is
then compared mathematically for numerical results, as well as other
comparison methods including error file differences and run time
changes. In regression testing, the 2 executables may depend on
different versions of the input files (IDFs). Anytime an
input change is present, this is a likely scenario. As such, the test
suite tool is set up to utilize a different run directory for each
executable.

Known issues
------------

Known issues for this tool are found on the
`issue list <https://github.com/NREL/EnergyPlusRegressionTool/issues>`_.
