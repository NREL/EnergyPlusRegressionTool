#!/bin/bash -e

pyinstaller --onefile eplus_regression_runner
mkdir deploy
tar -zcvf deploy/EnergyPlusRegressionTool-Ubuntu2004.tar.gz -C dist main
