#!/bin/bash -e

pyinstaller --onefile --add-data "epregressions/diffs/math_diff.config;epregressions/diffs" eplus_regression_runner
mkdir deploy
/C/Program\ Files/7-zip/7z.exe a deploy/EnergyPlusRegressionTool-Win.zip ./dist/*
