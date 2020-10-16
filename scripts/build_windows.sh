#!/bin/bash -e

pyinstaller --onefile eplus_regression_runner
mkdir deploy
/C/Program\ Files/7-zip/7z.exe a deploy/EnergyPlusRegressionTool-Win.zip ./dist/*
