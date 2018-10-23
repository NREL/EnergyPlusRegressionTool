import os
import stat
import sys

# this is pretty simple to run actually:
#  make sure you run it from the version of Python that has all the Gtk libs and such installed
#    (so if you are already developing on EpRegressions, just use that one)
#  this will find the current python, find the repo directory, and add all that to the desktop template file
#  then the template file will be dropped into ~/.local/share/applications
# you should be able to run EnergyPlus Regression Tool by pressing the super (Windows) button and searching for it
# you can then right click and save it in the favorites if you want


# I am sort-of assuming some things about the OS here, which I think can be summarized as pushing to a Debian-based OS
# So I could get away with more hardwired paths instead of using os.path.join, but whatever.
path = os.path.dirname(__file__)
script_dir = os.path.abspath(path)
repo_root = os.path.dirname(script_dir)
runner_script = os.path.join(repo_root, 'eplus_regression_runner')
which_python = sys.executable
template_desktop_file = os.path.join(script_dir, 'ep-testsuite.desktop')
main_window_file = os.path.join(script_dir, 'main_window.py')
icon_file = os.path.join(script_dir, 'ep_icon.png')
target_desktop_file = os.path.join(os.environ['HOME'], '.local', 'share', 'applications', 'ep-regressions.desktop')
file_content = open(template_desktop_file, 'r').read()
replacements = {
    '{RUNNER_SCRIPT}': runner_script,
    '{PATH_TO_PYTHON}': which_python,
    '{ICON_PATH}': icon_file,
}
for replacement in replacements:
    file_content = file_content.replace(replacement, replacements[replacement])
with open(target_desktop_file, 'w') as f:
    f.write(file_content)
st = os.stat(target_desktop_file)
os.chmod(target_desktop_file, st.st_mode | stat.S_IEXEC)
