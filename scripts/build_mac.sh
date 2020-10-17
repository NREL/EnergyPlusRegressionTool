#!/bin/bash -e

/Users/travis/Library/Python/3.7/bin/pyinstaller --add-data "epregressions/diffs/math_diff.config;epregressions/diffs" --onefile eplus_regression_runner
mkdir deploy
tar -zcvf deploy/EnergyPlusRegressionTool-Mac.tar.gz -C dist main
