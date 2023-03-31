from os import chmod, stat
from pathlib import Path
from platform import system
from site import USER_BASE
from sys import exit
from sysconfig import get_path

import energyplus_regressions

r"""
# Installation

Make sure you have Python installed.
Then install this tool via Pip.
On Linux/Mac, the Pip binary should be on PATH, on Windows, it might be, but it might not, so I will assume it is not.
So on Windows, the Pip binary will be at %PythonInstall%\Scripts\pip.exe;
(that directory will be used as %scripts_dir% in the following steps):

- Library install
  - Windows: Run `%scripts_dir%\pip install energyplus_regressions`
  - Mac/Linux: Run `pip install energyplus_regressions`
  - You can optionally add a `--user` argument to pip install it into your local user without admin privileges
- At this point, the regression tool can be run from a terminal:
  - Windows: Run `%scripts_dir%\energyplus_regressions_runner`
  - Mac/Linux: Run `energyplus_regressions_runner`
- Configuration
  - On Windows, configure the install to create a desktop shortcut to the main GUI by running the following:
    - `%scripts_dir%\pip install energyplus_regressions_configure`
  - On Linux, configure the install to create a `.desktop` entry in the user profile
  - For most distributions, this will allow finding the application from the shell and adding it to the taskbar/dock
    - `pip install energyplus_regressions_configure`
  - On Mac, we currently don't support adding an entry to the Dock because it requires creating an .app bundle.
    - You can run the regression tool directly from the command line as above, or create your own method for execution
"""


def configure() -> int:
    regressions_lib_root = Path(energyplus_regressions.__file__)
    if system() == 'Windows':
        from winreg import OpenKey, QueryValueEx, CloseKey, HKEY_CURRENT_USER as HKCU, KEY_READ as READ
        scripts_dir = Path(get_path('scripts'))
        icon_file = regressions_lib_root.parent / 'ep.ico'
        target_exe = scripts_dir / 'energyplus_regression_runner.exe'
        link_name = energyplus_regressions.NAME + '.lnk'
        with OpenKey(HKCU, r'Software\Microsoft\Windows\CurrentVersion\Explorer\User Shell Folders', 0, READ) as key:
            desktop_value, _ = QueryValueEx(key, 'Desktop')
            CloseKey(key)
        desktop = Path(desktop_value)
        path_link = desktop / link_name
        from win32com.client import Dispatch
        shell = Dispatch('WScript.Shell')
        with shell.CreateShortCut(path_link) as s:
            s.Targetpath = str(target_exe)
            s.WorkingDirectory = str(scripts_dir)
            s.IconLocation = str(icon_file)
            s.save()
    elif system() == 'Linux':
        # try assuming user install
        user_exe = Path(get_path('scripts')) / 'energyplus_regression_runner'
        global_exe = Path(USER_BASE) / 'bin' / 'energyplus_regression_runner'
        if user_exe.exists() and global_exe.exists():
            print("Detected the energyplus_regression_runner binary in both user and global locations.")
            print("Due to this ambiguity, I cannot figure out to which one I should link.")
            print(f"User install location: {user_exe}")
            print(f"Global install location: {global_exe}")
            print("If you pip uninstall one of them, I can create a link to the remaining one!")
            return 1
        elif user_exe.exists():
            target_exe = user_exe
        elif global_exe.exists():
            target_exe = global_exe
        else:
            print("Could not find energyplus_regression_runner binary at either user or global location.")
            print("This is weird since you are running this script...did you actually pip install this tool?")
            print("Make sure to pip install energyplus_regressions and then retry")
            return 1
        icon_file = regressions_lib_root.parent / 'ep.png'
        desktop_file = Path.home() / '.local' / 'share' / 'applications' / 'energyplus_regression_runner.desktop'
        with open(desktop_file, 'w') as f:
            f.write(f"""[Desktop Entry]
Name=EnergyPlus Regression Tool
Comment=An EnergyPlus test suite utility
Exec={target_exe}
Icon={icon_file}
Type=Application
Terminal=false
StartupWMClass=energyplus_regression_runner""")
        mode = stat(desktop_file).st_mode
        mode |= (mode & 0o444) >> 2  # copy R bits to X
        chmod(desktop_file, mode)
    return 0


def configure_cli() -> int:
    return configure()


if __name__ == '__main__':
    exit(configure_cli())
