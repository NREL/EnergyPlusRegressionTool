This folder contains a bunch of resources for running tests.
These are extremely lightweight executable scripts that mimic the actual E+ toolchain.
There are also other files in here such as example weather files and E+ run files.

The windows versions of these are prebuilt using pyinstaller and placed in the `dist/` directory
To rebuild them, ensure you have pyinstaller on Windows, change dir into the `energyplus_regressions/tests/resources` directory, and run:

```
PYTHONPATH=. ../../../venv/Scripts/pyinstaller.exe --onefile --log-level=WARN -n basement dummy.basement.py
PYTHONPATH=. ../../../venv/Scripts/pyinstaller.exe --onefile --log-level=WARN -n energyplus dummy.energyplus.py
PYTHONPATH=. ../../../venv/Scripts/pyinstaller.exe --onefile --log-level=WARN -n epmacro dummy.epmacro.py
PYTHONPATH=. ../../../venv/Scripts/pyinstaller.exe --onefile --log-level=WARN -n expandobjects dummy.expandobjects.py
PYTHONPATH=. ../../../venv/Scripts/pyinstaller.exe --onefile --log-level=WARN -n parametric dummy.parametric.py
PYTHONPATH=. ../../../venv/Scripts/pyinstaller.exe --onefile --log-level=WARN -n readvars dummy.readvars.py
PYTHONPATH=. ../../../venv/Scripts/pyinstaller.exe --onefile --log-level=WARN -n slab dummy.slab.py
```
