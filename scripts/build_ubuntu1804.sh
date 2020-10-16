#!/bin/bash -e

pyinstaller --onefile eplus_regression_runner
mkdir deploy
tar -zcvf deploy/EnergyPlusRegressionTool-Ubuntu1804.tar.gz -C dist main
