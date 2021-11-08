#!/bin/bash -e

BUILD_CONFIG=$1

VERSION_STRING=$(grep VERSION epregressions/__init__.py | cut -d= -f2 | xargs)

case ${BUILD_CONFIG} in

  Ubuntu20)
    pyinstaller --onefile --add-data "epregressions/diffs/math_diff.config:epregressions/diffs" epregressions/runner.py
    tar -zcvf deploy/EnergyPlusRegressionTool-"${VERSION_STRING}"-Ubuntu20.04.tar.gz -C dist runner
    ;;

  Mac)
    pyinstaller --onefile --noconsole --add-data "epregressions/diffs/math_diff.config:epregressions/diffs" epregressions/runner.py
    tar -zcvf deploy/EnergyPlusRegressionTool-"${VERSION_STRING}"-Mac.tar.gz -C dist runner.app
    ;;

  Windows)
    pyinstaller --onefile --noconsole --add-data "epregressions/diffs/math_diff.config;epregressions/diffs" epregressions/runner.py
    7z.exe a deploy/EnergyPlusRegressionTool-"${VERSION_STRING}"-Windows.zip ./dist/*
    ;;

  *)
    echo "Unknown config passed to packaging script!"
    ;;

esac
