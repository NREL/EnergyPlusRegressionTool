from datetime import datetime
import os
from pathlib import Path
import random
from threading import Thread
from tkinter import (
    Tk, ttk,  # Core pieces
    Button, Frame, Label, LabelFrame, Listbox, Menu, OptionMenu, Scrollbar, Spinbox,  # Widgets
    StringVar,  # Special Types
    messagebox,  # Dialog boxes
    E, W,  # Cardinal directions N, S,
    X, Y, BOTH,  # Orthogonal directions (for fill)
    END, LEFT, TOP,  # relative directions (RIGHT, TOP)
    filedialog, simpledialog,  # system dialogs
)
from typing import Set

from pubsub import pub

from epregressions.runtests import TestRunConfiguration, SuiteRunner
from epregressions.structures import (
    ForceRunType,
    ReportingFreq,
    TestEntry,
)
from epregressions.builds.base import KnownBuildTypes, autodetect_build_dir_type
from epregressions.builds.makefile import CMakeCacheMakeFileBuildDirectory
from epregressions.builds.visualstudio import CMakeCacheVisualStudioBuildDirectory
from epregressions.builds.install import EPlusInstallDirectory


class ResultsTreeRoots:
    AllFiles = "All Files Run"
    Case1Success = "Case 1 Successful Runs"
    Case1Fail = "Case 1 Failed Runs"
    Case2Success = "Case 2 Successful Runs"
    Case2Fail = "Case 2 Failed Runs"
    AllCompared = "All Files Compared"
    BigMathDiff = "Big Math Diffs"
    SmallMathDiff = "Small Math Diffs"
    BigTableDiff = "Big Table Diffs"
    SmallTableDiff = "Small Table Diffs"
    TextDiff = "Text Diffs"

    @staticmethod
    def get_all():
        return [
            ResultsTreeRoots.AllFiles,
            ResultsTreeRoots.Case1Success,
            ResultsTreeRoots.Case1Fail,
            ResultsTreeRoots.Case2Success,
            ResultsTreeRoots.Case2Fail,
            ResultsTreeRoots.AllCompared,
            ResultsTreeRoots.BigMathDiff,
            ResultsTreeRoots.SmallMathDiff,
            ResultsTreeRoots.BigTableDiff,
            ResultsTreeRoots.SmallTableDiff,
            ResultsTreeRoots.TextDiff,
        ]


class PubSubMessageTypes:
    PRINT = '10'
    STARTING = '20'
    CASE_COMPLETE = '30'
    SIMULATIONS_DONE = '40'
    DIFF_COMPLETE = '50'
    ALL_DONE = '60'
    CANCELLED = '70'


def dummy_get_idfs_in_dir(idf_dir: Path) -> Set[Path]:
    idf_path = Path(idf_dir)
    all_idfs_absolute_path = list(idf_path.rglob('*.idf'))
    all_idfs_relative_path = set([idf.relative_to(idf_path) for idf in all_idfs_absolute_path])
    return all_idfs_relative_path


class MyApp(Frame):

    def __init__(self):
        self.root = Tk()
        Frame.__init__(self, self.root)

        # high level GUI configuration
        self.root.geometry('800x600')
        self.root.resizable(width=1, height=1)
        self.root.option_add('*tearOff', False)  # keeps file menus from looking weird

        # members related to the background thread and operator instance
        self.long_thread = None
        self.background_operator = None

        # tk variables we can access later
        self.label_string = StringVar()
        self.build_dir_1_var = StringVar()
        self.build_dir_2_var = StringVar()
        self.run_period_option = StringVar()
        self.run_period_option.set(ForceRunType.NONE)
        self.reporting_frequency = StringVar()
        self.reporting_frequency.set(ReportingFreq.HOURLY)

        # widgets that we might want to access later
        self.build_dir_1_button = None
        self.build_dir_2_button = None
        self.run_button = None
        self.stop_button = None
        self.build_dir_1_label = None
        self.build_dir_1_var.set('/eplus/repos/1eplus/builds')  # "<Select build dir 1>")
        self.build_dir_2_label = None
        self.build_dir_2_var.set('/eplus/repos/1eplus/builds')  # "<Select build dir 2>")
        self.progress = None
        self.log_message_listbox = None
        self.results_tree = None
        self.num_threads_spinner = None
        self.full_idf_listbox = None
        self.move_idf_to_active_button = None
        self.active_idf_listbox = None
        self.remove_idf_from_active_button = None
        self.idf_select_all_button = None
        self.idf_deselect_all_button = None
        self.idf_select_n_random_button = None
        self.run_period_option_menu = None
        self.reporting_frequency_option_menu = None

        # some data holders
        self.tree_folders = dict()
        self.valid_idfs_in_listing = False
        self.run_button_color = '#008000'
        self.build_1 = None
        self.build_2 = None

        # initialize the GUI
        self.init_window()

        # wire up the background thread
        pub.subscribe(self.print_handler, PubSubMessageTypes.PRINT)
        pub.subscribe(self.starting_handler, PubSubMessageTypes.STARTING)
        pub.subscribe(self.case_completed_handler, PubSubMessageTypes.CASE_COMPLETE)
        pub.subscribe(self.runs_complete_handler, PubSubMessageTypes.SIMULATIONS_DONE)
        pub.subscribe(self.diff_complete_handler, PubSubMessageTypes.DIFF_COMPLETE)
        pub.subscribe(self.done_handler, PubSubMessageTypes.ALL_DONE)
        pub.subscribe(self.cancelled_handler, PubSubMessageTypes.CANCELLED)

    def init_window(self):
        # changing the title of our master widget
        self.root.title("EnergyPlus Regression Tool 2")
        self.root.protocol("WM_DELETE_WINDOW", self.client_exit)

        # create the menu
        menu = Menu(self.root)
        self.root.config(menu=menu)
        file_menu = Menu(menu)
        file_menu.add_command(label="Exit", command=self.client_exit)
        menu.add_cascade(label="File", menu=file_menu)

        # main notebook holding everything
        main_notebook = ttk.Notebook(self.root)

        # run configuration
        pane_run = Frame(main_notebook)
        group_build_dir_1 = LabelFrame(pane_run, text="Build Directory 1")
        group_build_dir_1.pack(fill=X, padx=5)
        self.build_dir_1_button = Button(group_build_dir_1, text="Change...", command=self.client_build_dir_1)
        self.build_dir_1_button.grid(row=1, column=1, sticky=W)
        self.build_dir_1_label = Label(group_build_dir_1, textvariable=self.build_dir_1_var)
        self.build_dir_1_label.grid(row=1, column=2, sticky=E)
        group_build_dir_2 = LabelFrame(pane_run, text="Build Directory 2")
        group_build_dir_2.pack(fill=X, padx=5)
        self.build_dir_2_button = Button(group_build_dir_2, text="Change...", command=self.client_build_dir_2)
        self.build_dir_2_button.grid(row=1, column=1, sticky=W)
        self.build_dir_2_label = Label(group_build_dir_2, textvariable=self.build_dir_2_var)
        self.build_dir_2_label.grid(row=1, column=2, sticky=E)
        group_run_options = LabelFrame(pane_run, text="Run Options")
        group_run_options.pack(fill=X, padx=5)
        Label(group_run_options, text="Number of threads for suite: ").grid(row=1, column=1, sticky=E)
        self.num_threads_spinner = Spinbox(group_run_options, from_=1, to_=48)  # validate later
        self.num_threads_spinner.grid(row=1, column=2, sticky=W)
        Label(group_run_options, text="Test suite run configuration: ").grid(row=2, column=1, sticky=E)
        self.run_period_option_menu = OptionMenu(group_run_options, self.run_period_option, *ForceRunType.get_all())
        self.run_period_option_menu.grid(row=2, column=2, sticky=W)
        Label(group_run_options, text="Minimum reporting frequency: ").grid(row=3, column=1, sticky=E)
        self.reporting_frequency_option_menu = OptionMenu(
            group_run_options, self.reporting_frequency, *ReportingFreq.get_all()
        )
        self.reporting_frequency_option_menu.grid(row=3, column=2, sticky=W)
        main_notebook.add(pane_run, text='Configuration')

        # now let's set up a list of checkboxes for selecting IDFs to run
        pane_idfs = Frame(main_notebook)
        group_idf_tools = LabelFrame(pane_idfs, text="IDF Selection Tools")
        group_idf_tools.pack(fill=X, padx=5)
        self.idf_select_all_button = Button(
            group_idf_tools, text="Refresh", command=self.client_idf_refresh
        )
        self.idf_select_all_button.pack(side=LEFT, expand=1)
        self.idf_select_all_button = Button(
            group_idf_tools, text="Select All", command=self.idf_select_all
        )
        self.idf_select_all_button.pack(side=LEFT, expand=1)
        self.idf_deselect_all_button = Button(
            group_idf_tools, text="Deselect All", command=self.idf_deselect_all
        )
        self.idf_deselect_all_button.pack(side=LEFT, expand=1)
        self.idf_select_n_random_button = Button(
            group_idf_tools, text="Select N Random", command=self.idf_select_random
        )
        self.idf_select_n_random_button.pack(side=LEFT, expand=1)

        group_full_idf_list = LabelFrame(pane_idfs, text="Full IDF List")
        group_full_idf_list.pack(fill=X, padx=5)
        scrollbar = Scrollbar(group_full_idf_list)
        self.full_idf_listbox = Listbox(group_full_idf_list, yscrollcommand=scrollbar.set)
        self.full_idf_listbox.bind('<Double-1>', self.idf_move_to_active)
        self.full_idf_listbox.pack(fill=BOTH, side=LEFT, expand=True)
        scrollbar.pack(fill=Y, side=LEFT)
        scrollbar.config(command=self.full_idf_listbox.yview)

        self.move_idf_to_active_button = Button(
            pane_idfs, text="↓ Add to Active List ↓", command=self.idf_move_to_active
        )
        self.move_idf_to_active_button.pack(side=TOP, fill=X, expand=True)

        self.remove_idf_from_active_button = Button(
            pane_idfs, text="↑ Remove from Active List ↑", command=self.idf_remove_from_active
        )
        self.remove_idf_from_active_button.pack(side=TOP, fill=X, expand=True)

        group_active_idf_list = LabelFrame(pane_idfs, text="Active IDF List")
        group_active_idf_list.pack(fill=X, padx=5)
        scrollbar = Scrollbar(group_active_idf_list)
        self.active_idf_listbox = Listbox(group_active_idf_list, yscrollcommand=scrollbar.set)
        self.active_idf_listbox.bind('<Double-1>', self.idf_remove_from_active)
        self.active_idf_listbox.pack(fill=BOTH, side=LEFT, expand=True)
        scrollbar.pack(fill=Y, side=LEFT)
        scrollbar.config(command=self.active_idf_listbox.yview)

        self.build_idf_listing(initialize=True)

        main_notebook.add(pane_idfs, text="IDF Selection")

        # set up a scrolled listbox for the log messages
        frame_log_messages = Frame(main_notebook)
        group_log_messages = LabelFrame(frame_log_messages, text="Log Message Tools")
        group_log_messages.pack(fill=X, padx=5)
        Button(group_log_messages, text="Clear Log Messages", command=self.clear_log).pack(side=LEFT, expand=1)
        Button(group_log_messages, text="Copy Log Messages", command=self.copy_log).pack(side=LEFT, expand=1)
        scrollbar = Scrollbar(frame_log_messages)
        self.log_message_listbox = Listbox(frame_log_messages, yscrollcommand=scrollbar.set)
        self.add_to_log("Program started!")
        self.log_message_listbox.pack(fill=BOTH, side=LEFT, expand=True)
        scrollbar.pack(fill=Y, side=LEFT)
        scrollbar.config(command=self.log_message_listbox.yview)
        main_notebook.add(frame_log_messages, text="Log Messages")

        # set up a tree-view for the results
        frame_results = Frame(main_notebook)
        scrollbar = Scrollbar(frame_results)
        self.results_tree = ttk.Treeview(frame_results, columns=("Base File", "Mod File", "Diff File"))
        self.results_tree.heading("#0", text="Results")
        self.results_tree.column('#0', minwidth=200, width=200)
        self.results_tree.heading("Base File", text="Base File")
        self.results_tree.column("Base File", minwidth=100, width=100)
        self.results_tree.heading("Mod File", text="Mod File")
        self.results_tree.column("Mod File", minwidth=100, width=100)
        self.results_tree.heading("Diff File", text="Diff File")
        self.results_tree.column("Diff File", minwidth=100, width=100)
        self.build_results_tree()
        self.results_tree.pack(fill=BOTH, side=LEFT, expand=True)
        scrollbar.pack(fill=Y, side=LEFT)
        scrollbar.config(command=self.results_tree.yview)
        main_notebook.add(frame_results, text="Run Control and Results")

        # pack the main notebook on the window
        main_notebook.pack(fill=BOTH, expand=1)

        # status bar at the bottom
        frame_status = Frame(self.root)
        self.run_button = Button(frame_status, text="Run", bg=self.run_button_color, command=self.client_run)
        self.run_button.pack(side=LEFT, expand=0)
        self.stop_button = Button(frame_status, text="Stop", command=self.client_stop, state='disabled')
        self.stop_button.pack(side=LEFT, expand=0)
        self.progress = ttk.Progressbar(frame_status)
        self.progress.pack(side=LEFT, expand=0)
        label = Label(frame_status, textvariable=self.label_string)
        self.label_string.set("Initialized")
        label.pack(side=LEFT, anchor=W)
        frame_status.pack(fill=X)

    def run(self):
        self.root.mainloop()

    def build_idf_listing(self, initialize=False, desired_selected_idfs=None):
        # clear any existing ones
        self.active_idf_listbox.delete(0, END)
        self.full_idf_listbox.delete(0, END)

        # now rebuild them
        self.valid_idfs_in_listing = False
        path_1 = Path(self.build_dir_1_var.get())
        path_2 = Path(self.build_dir_2_var.get())
        if self.build_1 and path_1.exists() and self.build_2 and path_2.exists():
            idf_dir_1 = self.build_1.get_idf_directory()
            idfs_dir_1 = dummy_get_idfs_in_dir(idf_dir_1)
            idf_dir_2 = self.build_2.get_idf_directory()
            idfs_dir_2 = dummy_get_idfs_in_dir(idf_dir_2)
            common_idfs = idfs_dir_1.intersection(idfs_dir_2)
            if len(common_idfs) == 0:
                self.full_idf_listbox.insert(END, "No common IDFs found between build folders")
                self.full_idf_listbox.insert(END, "Select valid build folders to fill listing")
                return
            for idf in sorted(common_idfs):
                self.full_idf_listbox.insert(END, str(idf))
            self.valid_idfs_in_listing = True
        elif initialize:
            self.full_idf_listbox.insert(END, "This will be the master list")
            self.full_idf_listbox.insert(END, "Select build folders to fill listing")
        elif path_1.exists():
            self.full_idf_listbox.insert(END, "Cannot update master list master list")
            self.full_idf_listbox.insert(END, "Build folder path #2 is invalid")
            self.full_idf_listbox.insert(END, "Select build folders to fill listing")
        elif path_2.exists():
            self.full_idf_listbox.insert(END, "Cannot update master list master list")
            self.full_idf_listbox.insert(END, "Build folder path #1 is invalid")
            self.full_idf_listbox.insert(END, "Select build folders to fill listing")
        else:
            self.full_idf_listbox.insert(END, "Cannot update master list master list")
            self.full_idf_listbox.insert(END, "Both build folders are invalid")
            self.full_idf_listbox.insert(END, "Select build folders to fill listing")

        if desired_selected_idfs is None:
            ...
            # add things to the listbox

    def build_results_tree(self, results=None):
        self.results_tree.delete(*self.results_tree.get_children())
        for root in ResultsTreeRoots.get_all():
            self.tree_folders[root] = self.results_tree.insert(
                parent="", index=END, text=root, values=("", "", "")
            )
            if results:
                self.results_tree.insert(
                    parent=self.tree_folders[root], index=END, text="Pretend",
                    values=("These", "Are", "Real")
                )
            else:
                self.results_tree.insert(
                    parent=self.tree_folders[root], index=END, text="Run test for results",
                    values=("", "", "")
                )

    def add_to_log(self, message):
        self.log_message_listbox.insert(END, f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}]: {message}")

    def clear_log(self):
        self.log_message_listbox.delete(0, END)

    def copy_log(self):
        messages = self.log_message_listbox.get(0, END)
        message_string = '\n'.join(messages)
        self.root.clipboard_clear()
        self.root.clipboard_append(message_string)

    def client_idf_refresh(self):
        self.build_idf_listing()

    def idf_move_to_active(self, _=None):
        if not self.valid_idfs_in_listing:
            simpledialog.messagebox.showerror("IDF Selection Error", "Invalid build folders or IDF list")
            return
        current_selection = self.full_idf_listbox.curselection()
        if not current_selection:
            simpledialog.messagebox.showerror("IDF Selection Error", "No IDF Selected")
            return
        currently_selected_idf = self.full_idf_listbox.get(current_selection)
        try:
            self.active_idf_listbox.get(0, END).index(currently_selected_idf)
            simpledialog.messagebox.showwarning("IDF Selection Warning", "IDF already exists in active list")
            return
        except ValueError:
            pass  # the value error indicates it was _not_ found, so this is success
        self.active_idf_listbox.insert(END, currently_selected_idf)
        self.idf_refresh_count_status(currently_selected_idf, True)

    def idf_remove_from_active(self, event=None):
        if not self.valid_idfs_in_listing:
            simpledialog.messagebox.showerror("IDF Selection Error", "Invalid build folders or IDF list")
            return
        current_selection = self.active_idf_listbox.curselection()
        if not current_selection:
            if event:
                return
            simpledialog.messagebox.showerror("IDF Selection Error", "No IDF Selected")
            return
        self.active_idf_listbox.delete(current_selection)
        self.idf_refresh_count_status(current_selection, False)

    def idf_select_all(self):
        self.idf_deselect_all()
        if not self.valid_idfs_in_listing:
            simpledialog.messagebox.showerror("IDF Selection Error", "Invalid build folders or IDF list")
            return
        all_idfs = self.full_idf_listbox.get(0, END)
        for idf in all_idfs:
            self.active_idf_listbox.insert(END, idf)
        self.idf_refresh_count_status()

    def idf_deselect_all(self):
        if not self.valid_idfs_in_listing:
            simpledialog.messagebox.showerror("IDF Selection Error", "Invalid build folders or IDF list")
            return
        self.active_idf_listbox.delete(0, END)
        self.idf_refresh_count_status()

    def idf_select_random(self):
        if not self.valid_idfs_in_listing:
            simpledialog.messagebox.showerror("IDF Selection Error", "Invalid build folders or IDF list")
            return
        potential_number_to_select = simpledialog.askinteger("Input Amount", "How many would you like to select?")
        if not potential_number_to_select:
            return
        self.idf_deselect_all()
        number_to_select = int(potential_number_to_select)
        number_of_idf_files = self.full_idf_listbox.size()
        if number_of_idf_files <= number_to_select:  # just take all of them
            self.idf_select_all()
        else:  # down select randomly
            indices_to_take = random.sample(range(number_of_idf_files), number_to_select)
            idfs_to_take = list()
            for i in indices_to_take:
                idf_to_get = self.full_idf_listbox.get(i)
                idfs_to_take.append(idf_to_get)
            for idf_to_get in sorted(idfs_to_take):
                self.active_idf_listbox.insert(END, idf_to_get)
        self.idf_refresh_count_status()

    def idf_refresh_count_status(self, test_case=None, checked=False):
        if not self.valid_idfs_in_listing:
            return
        num_total = self.full_idf_listbox.size()
        num_active = self.active_idf_listbox.size()
        if test_case:
            chk_string = "Checked" if checked else "Unchecked"
            if checked:
                self.label_string.set(f"{chk_string} {test_case} ({num_active}/{num_total} selected)")
        else:
            self.label_string.set(f"{num_active}/{num_total} selected")

    def set_gui_status_for_run(self, is_running: bool):
        if is_running:
            run_button_state = 'disabled'
            stop_button_state = 'normal'
        else:
            run_button_state = 'normal'
            stop_button_state = 'disabled'
        self.build_dir_1_button.configure(state=run_button_state)
        self.build_dir_2_button.configure(state=run_button_state)
        self.run_button.configure(state=run_button_state)
        self.idf_select_all_button.configure(state=run_button_state)
        self.idf_deselect_all_button.configure(state=run_button_state)
        self.idf_select_n_random_button.configure(state=run_button_state)
        self.move_idf_to_active_button.configure(state=run_button_state)
        self.remove_idf_from_active_button.configure(state=run_button_state)
        self.run_period_option_menu.configure(state=run_button_state)
        self.reporting_frequency_option_menu.configure(state=run_button_state)
        self.num_threads_spinner.configure(state=run_button_state)
        self.stop_button.configure(state=stop_button_state)

    def client_build_dir_1(self):
        selected_dir = filedialog.askdirectory()
        if not selected_dir:
            return
        probable_build_dir_type = autodetect_build_dir_type(selected_dir)
        if probable_build_dir_type == KnownBuildTypes.Unknown:
            simpledialog.messagebox.showerror("Could not determine build type!")
            return
        elif probable_build_dir_type == KnownBuildTypes.Installation:
            self.build_1 = EPlusInstallDirectory()
            self.build_1.set_build_directory(selected_dir)
        elif probable_build_dir_type == KnownBuildTypes.VisualStudio:
            self.build_1 = CMakeCacheVisualStudioBuildDirectory()
            self.build_1.set_build_directory(selected_dir)
        elif probable_build_dir_type == KnownBuildTypes.Makefile:
            self.build_1 = CMakeCacheMakeFileBuildDirectory()
            self.build_1.set_build_directory(selected_dir)
        self.build_dir_1_var.set(selected_dir)
        self.build_idf_listing()

    def client_build_dir_2(self):
        selected_dir = filedialog.askdirectory()
        if not selected_dir:
            return
        probable_build_dir_type = autodetect_build_dir_type(selected_dir)
        if probable_build_dir_type == KnownBuildTypes.Unknown:
            simpledialog.messagebox.showerror("Could not determine build type!")
            return
        elif probable_build_dir_type == KnownBuildTypes.Installation:
            self.build_2 = EPlusInstallDirectory()
            self.build_2.set_build_directory(selected_dir)
        elif probable_build_dir_type == KnownBuildTypes.VisualStudio:
            self.build_2 = CMakeCacheVisualStudioBuildDirectory()
            self.build_2.set_build_directory(selected_dir)
        elif probable_build_dir_type == KnownBuildTypes.Makefile:
            self.build_2 = CMakeCacheMakeFileBuildDirectory()
            self.build_2.set_build_directory(selected_dir)
        self.build_dir_2_var.set(selected_dir)
        self.build_idf_listing()

    def client_run(self):
        if self.long_thread:
            messagebox.showerror("Cannot run another thread, wait for the current to finish -- how'd you get here?!?")
            return
        potential_num_threads = self.num_threads_spinner.get()
        try:
            num_threads = int(potential_num_threads)
        except ValueError:
            messagebox.showerror("Invalid Configuration", "Number of threads must be an integer")
            return
        if not self.build_1:
            messagebox.showerror("Build folder 1 problem", "Select a valid build folder 1 prior to running")
            return
        build_1_valid = self.build_1.verify()
        if any([not b[2] for b in build_1_valid]):
            messagebox.showerror("Build folder 1 problem", "Problem with build 1!")
            return
        if not self.build_2:
            messagebox.showerror("Build folder 2 problem", "Select a valid build folder 2 prior to running")
            return
        build_2_valid = self.build_2.verify()
        if any([not b[2] for b in build_2_valid]):
            messagebox.showerror("Build folder 2 problem", "Problem with build 2!")
            return
        run_configuration = TestRunConfiguration(
            force_run_type=self.run_period_option.get(),
            num_threads=num_threads,
            report_freq=self.reporting_frequency.get(),
            build_a=self.build_1,
            build_b=self.build_2
        )
        idfs_to_run = list()
        for this_file in self.active_idf_listbox.get(0, END):
            idfs_to_run.append(
                TestEntry(os.path.splitext(this_file), None)
            )
        if len(idfs_to_run) == 0:
            messagebox.showwarning("Nothing to run", "No IDFs were activated, so nothing to run")
            return
        self.background_operator = SuiteRunner(run_configuration, idfs_to_run)
        self.background_operator.add_callbacks(print_callback=MyApp.print_listener,
                                               simstarting_callback=MyApp.starting_listener,
                                               casecompleted_callback=MyApp.case_completed_listener,
                                               simulationscomplete_callback=MyApp.runs_complete_listener,
                                               diffcompleted_callback=MyApp.diff_complete_listener,
                                               alldone_callback=MyApp.done_listener,
                                               cancel_callback=MyApp.cancelled_listener)
        self.set_gui_status_for_run(True)
        self.long_thread = Thread(target=self.background_operator.run_test_suite)
        self.long_thread.setDaemon(True)
        self.add_to_log("Starting a new set of tests")
        self.long_thread.start()

    @staticmethod
    def print_listener(msg):
        pub.sendMessage(PubSubMessageTypes.PRINT, msg=msg)

    def print_handler(self, msg):
        self.add_to_log(msg)

    @staticmethod
    def starting_listener():
        pub.sendMessage(PubSubMessageTypes.STARTING, ...)

    def starting_handler(self):
        ...

    @staticmethod
    def case_completed_listener():
        pub.sendMessage(PubSubMessageTypes.CASE_COMPLETE, ...)

    def case_completed_handler(self):
        ...
        # self.add_to_log(object_completed)
        # self.progress['value'] = percent_complete
        # self.label_string.set(f"Hey, status update: {str(status)}")

    @staticmethod
    def runs_complete_listener():
        pub.sendMessage(PubSubMessageTypes.SIMULATIONS_DONE, ...)

    def runs_complete_handler(self):
        ...

    @staticmethod
    def diff_complete_listener():
        pub.sendMessage(PubSubMessageTypes.DIFF_COMPLETE, ...)

    def diff_complete_handler(self):
        ...

    @staticmethod
    def done_listener():
        pub.sendMessage(PubSubMessageTypes.ALL_DONE, ...)

    def done_handler(self):
        ...
        # self.add_to_log("All done, finished")
        #         self.label_string.set("Hey, all done!")
        #         self.build_results_tree(results)
        #         self.client_done()

    @staticmethod
    def cancelled_listener():
        pub.sendMessage(PubSubMessageTypes.CANCELLED)

    def cancelled_handler(self):
        self.add_to_log("Cancelled!")
        self.label_string.set("Properly cancelled!")
        self.client_done()

    def client_stop(self):
        self.add_to_log("Attempting to cancel")
        self.label_string.set("Attempting to cancel...")
        self.background_operator.please_stop()

    def client_exit(self):
        if self.long_thread:
            messagebox.showerror("Uh oh!", "Cannot exit program while operations are running; abort them then exit")
            return
        exit()

    def client_done(self):
        self.set_gui_status_for_run(False)
        self.long_thread = None
