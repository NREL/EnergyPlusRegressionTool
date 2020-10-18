#!/bin/bash -e

pyinstaller --onefile --add-data "epregressions/diffs/math_diff.config:epregressions/diffs" eplus_regression_runner
mkdir deploy
tar -zcvf deploy/EnergyPlusRegressionTool-Ubuntu2004.tar.gz -C dist main
