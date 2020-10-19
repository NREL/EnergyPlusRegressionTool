# EnergyPlus Regressions

[![Documentation Status](https://readthedocs.org/projects/energyplusregressiontool/badge/?version=latest)](https://energyplusregressiontool.readthedocs.io/en/latest/?badge=latest)
[![Build Status](https://travis-ci.org/NREL/EnergyPlusRegressionTool.svg?branch=master)](https://travis-ci.org/NREL/EnergyPlusRegressionTool)
[![Coverage Status](https://coveralls.io/repos/github/NREL/EnergyPlusRegressionTool/badge.svg?branch=master)](https://coveralls.io/github/NREL/EnergyPlusRegressionTool?branch=master)

## Overview

This library provides tools for performing regressions between EnergyPlus builds.
Developers often propose changes to EnergyPlus for:

 - New feature development
 - Defect repair
 - Refactoring for structure or performance
 - etc.

When a developer proposes these changes, they must be tested.
The continuous integration system over on EnergyPlus handles this, and provides results, but there can be a long time delay waiting on those results, depending on how busy CI is at that moment.
This tool provides a way to run these regressions locally.

## Platform Support

This tool is written to be functional on all three major platforms.
Travis is testing the underlying code on all the platforms, and the developer regularly tests the graphical engine on all three as well.
Packages are provided for two LTS versions of Ubuntu (18.04 and 20.04) as well as Windows and Mac.

## Installation

Ultimately there will be two ways to install this tool:
 - Downloading a pre-built (by Travis) binary package through a Github release page, and
 - Installing the library into an existing Python install using Pip.
 
Right now the Pip implementation is not yet done, so the core method will be to download the binary.
You should not need any outside tools to run the downloaded package, not even Python.

## Development

For setting up a development environment to actually _work_ on this tool, the steps are pretty minimal:
 - Install Python, if needed
 - Clone this repository (`git clone https://github.com/NREL/EnergyPlusRegressionTool`)
 - Install dependencies (`pip3 install -r requirements.txt`)

## Documentation

Further program documentation, including user guide and typical workflows, are available in the documentation.
This documentation is written using RST with Sphinx, and published on [ReadTheDocs](https://energyplusregressiontool.readthedocs.io/en/latest/).

## Testing

Exhaustive unit tests have been added to the "underneath the hood" code, like the functions that calculate diffs and run builds.
GUI code is not unit tested, but tested manually on all platforms periodically.
The unit tests are run by [Travis](https://travis-ci.org/NREL/EnergyPlusRegressionTool).
