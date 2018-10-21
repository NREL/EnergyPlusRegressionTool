Typical Workflow
================

Although every project will be different, some common things can be
identified in regards to using this test suite tool.

Overview
--------

An EnergyPlus project is typically a new feature being implemented or a
bug fix. In either case, once development is completed, testing must be
performed to ensure the new feature is working properly and that the
changes did not break anything. Ensuring that the new feature is working
properly is not a responsibility of this test suite engine at the
moment, and relies on the developer performing verification and/or
validation of the model.

Design/Development/Prototype
----------------------------

A project will typically start with a design phase, followed by a review
process before code is actually implemented. Code is then developed to
provide the new or improved capability. Once the code is satisfactory
and the results have been verified, regression testing must be
performed. This is the spot where the test suite tool can be of most
assistance, described in the next section.

Test
----

To perform regression testing with this tool, only a few steps are
required.

Identify Baseline
~~~~~~~~~~~~~~~~~

For regression testing, a baseline should be identified. This is likely
a snapshot of the develop branch of the development repository. If your code is
out of date develop, it is beneficial to update the
branch so that the regression testing represents the latest development
snapshot versus only your changes. In any case, the key is that the
difference between the baseline and the proposed changes are only the
changes related to this specific task.

Build Baseline and Proposed
~~~~~~~~~~~~~~~~~~~~~~~~~~~

A completed build, with ``BUILD_FORTRAN`` on, is needed for each of
the baseline and proposed versions.  Each build folder should have a
Products subdirectory with the binaries and all other needed material.

Select IDFs
~~~~~~~~~~~

Once the builds are completed, launch the test suite tool.
Configure which idfs are supposed to be run using the selection
and deselection buttons and options.

Test Suite Options
~~~~~~~~~~~~~~~~~~

Next configure the test suite options to point to the appropriate build
directories. Then configure which test suite run
configuration should be run. For a first pass, I would recommend doing
design-days only so that time won’t be wasted should an obvious problem
arise. Next verify the file structure. At this point, it would probably
be a good idea to *save the settings, using File->Save*.

Running Suites
~~~~~~~~~~~~~~

If all is well, run the test suite. At this point, the developer must
process the results to determine if changes need to be made and require
a rebuild. If so, the design day tests should be run again. A subset of
the example files may be run at this point just on problem files. Once
these results are satisfactory, a full annual simulation is useful
followed by a check of the composite error files to make sure new error
messages are not present.
