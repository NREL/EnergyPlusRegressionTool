#!/bin/bash -e

/Users/travis/Library/Python/3.7/bin/pyinstaller --onefile eplus_regression_runner
mkdir deploy
tar -zcvf deploy/EnergyPlusRegressionTool-Mac.tar.gz -C dist main
