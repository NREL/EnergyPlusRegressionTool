#!/usr/bin/env python3

# main entry point into my_app, for either command line operation or gui operation
# if no command line args are given, it is gui operation
# but don't try to import any Tk/Gui stuff unless we are doing GUI operation

# TODO: Add unit test coverage once we start adding more entry points, remove from omission block in .coveragerc

from multiprocessing import set_start_method
from platform import system
from sys import argv


def main_gui():
    from energyplus_regressions.tk_window import MyApp
    app = MyApp()
    app.run()


if __name__ == "__main__":
    if system() == 'Darwin':
        set_start_method('forkserver')
    if len(argv) == 1:  # GUI
        main_gui()
    else:  # Non-GUI operation, execute some command
        ...
