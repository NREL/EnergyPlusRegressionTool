import sys

platform = ''
if "linux" in sys.platform:
    platform = "linux"
elif "darwin" in sys.platform:
    platform = "mac"
elif "win" in sys.platform:
    platform = "windows"

exe_extension = ''
if platform == 'windows':
    exe_extension = '.exe'
