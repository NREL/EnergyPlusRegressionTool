#!/usr/bin/env python

import datetime  # datetime allows us to generate timestamps for the log
import subprocess  # subprocess allows us to spawn the help pdf separately
import threading  # threading allows for the test suite to run multiple E+ runs concurrently
import webbrowser
from datetime import datetime  # get datetime to do date/time calculations for timestamps, etc.

# import the supporting python modules for this script
from epregressions.build_files_to_run import *
from epregressions.runtests import *
from epregressions.structures import SingleCaseInformation

# graphics stuff
import gi

gi.require_version('Gdk', '3.0')  # unfortunately these have to go before the import
gi.require_version("Gtk", "3.0")
from gi.repository import Gdk, Gtk, GObject

platform = ''
if "linux" in sys.platform:
    platform = "linux"
elif "darwin" in sys.platform:
    platform = "mac"
elif "win" in sys.platform:
    platform = "windows"
path = os.path.dirname(__file__)
script_dir = os.path.abspath(path)

box_spacing = 2
force_none = "Don't force anything"
force_dd = "Force design day simulations only"
force_annual = "Force annual run-period simulations"


class IDFListViewColumnIndex:
    RUN = 0
    IDF = 1
    EPW = 2


# noinspection PyUnusedLocal
class PyApp(Gtk.Window):

    def __init__(self):

        # initialize the parent class
        super(PyApp, self).__init__()

        # connect signals for the GUI
        self.connect("destroy", self.go_away)

        # initialize member variables here
        self.idf_list_store = None
        self.idf_selection_table = None
        self.file_list_num_files = None
        self.case_1_check = None
        self.case_2_check = None
        self.suite_option_num_threads = None
        self.run_type_combo_box = None
        self.report_frequency_combo_box = None
        self.suite_dir_struct_info = None
        self.suite_option_handler_runtime_report_check = None
        self.suite_option_runtime_file_label = None
        self.btn_run_suite = None
        self.verify_list_store = None
        self.verify_tree_view = None
        self.results_list_store = None
        self.results_parent_num_run = None
        self.results_parent_success = None
        self.results_parent_not_success = None
        self.results_parent_success_2 = None
        self.results_parent_not_success_2 = None
        self.results_parent_files_compared = None
        self.results_parent_big_math = None
        self.results_parent_small_math = None
        self.results_parent_big_table = None
        self.results_parent_small_table = None
        self.results_parent_textual = None
        self.results_child_num_run = None
        self.results_child_success = None
        self.results_child_not_success = None
        self.results_child_success_2 = None
        self.results_child_not_success_2 = None
        self.results_child_files_compared = None
        self.results_child_big_math = None
        self.results_child_small_math = None
        self.results_child_big_table = None
        self.results_child_small_table = None
        self.results_child_textual = None
        self.tree_view = None
        self.tree_selection = None
        self.last_run_heading = None
        self.log_scroll_notebook_page = None
        self.log_store = None
        self.notebook = None
        self.progress = None
        self.status_bar = None
        self.status_bar_context_id = None
        self.last_run_context = None
        self.last_run_context_copy = None
        self.last_run_context_nocopy = None
        self.file_list_builder_configuration = None
        self.current_progress_value = None
        self.progress_maximum_value = None
        self.do_runtime_report = None  # EDWIN: Always do runtime report and formalize this
        self.runtime_report_file = None
        self.suiteargs = None
        self.runner = None
        self.work_thread = None
        self.results_list_selected_entry_root_index = None
        self.results_lists_to_copy = None
        self.case_1_build_dir_label = None
        self.case_2_build_dir_label = None
        self.try_to_restore_files = None

        # set up default arguments for the idf list builder and the test suite engine
        # NOTE the GUI will set itself up according to these defaults, so do this before gui_build()
        self.init_file_list_builder_args()
        self.init_suite_args()

        # build the GUI
        self.gui_build()

        # override the init if an auto-saved file exists by passing None here
        self.load_settings(None)

        # then actually fill the GUI with settings
        self.gui_fill_with_data()

        # initialize other one-time stuff here
        self.last_folder_path = None
        self.missing_weather_file_key = "<no_weather_file>"
        self.idf_files_have_been_built = False
        self.test_suite_is_running = False
        self.currently_saving = False

        # start the auto-save timer
        GObject.timeout_add(300000, self.save_settings,
                            None)  # milliseconds, and a function pointer, and an argument to be passed to the function

        # build the idf selection
        self.build_button(None)

        # after the IDF list has been built, try to restore the IDF selection from the IDFs in settings
        if self.try_to_restore_files:
            self.restore_file_selection(self.try_to_restore_files)

    def go_away(self, what_else_goes_in_gtk_main_quit):
        try:
            self.save_settings(None)
        except Exception as this_exception:
            print(this_exception)
        Gtk.main_quit()

    def gui_build(self):

        # put the window in the center of the (primary? current?) screen
        self.set_position(Gtk.WindowPosition.CENTER)

        # make a nice border around the outside of the window
        self.set_border_width(10)

        # set the window title
        self.set_title("EnergyPlus Regressions")

        # set the window icon
        self.set_icon_from_file(os.path.join(script_dir, 'ep_icon.png'))

        # build the last run context menu
        self.last_run_context = Gtk.Menu()
        self.last_run_context_copy = Gtk.MenuItem("Copy files from this node to the clipboard")
        self.last_run_context.append(self.last_run_context_copy)
        self.last_run_context_copy.connect("activate", self.handle_results_list_copy)
        self.last_run_context_copy.hide()
        self.last_run_context_nocopy = Gtk.MenuItem("No files on this node to copy to the clipboard")
        self.last_run_context.append(self.last_run_context_nocopy)
        self.last_run_context_nocopy.show()

        # create a v-box to start laying out the geometry of the form
        this_v_box = Gtk.VBox(False, box_spacing)

        # add the menu to the v-box
        this_v_box.pack_start(self.gui_build_menu_bar(), False, False, box_spacing)

        # add the notebook to the v-box
        this_v_box.pack_start(self.gui_build_notebook(), True, True, box_spacing)

        # and finally add the status section at the bottom
        this_v_box.pack_end(self.gui_build_messaging(), False, False, box_spacing)

        # now add the entire v-box to the main form
        self.add(this_v_box)

        # shows all child widgets recursively
        self.show_all()

    def gui_build_menu_bar(self):

        # create the menu bar itself to hold the menus;
        # this is what is added to the v-box, or in the case of Ubuntu the global menu
        mb = Gtk.MenuBar()

        menu_item_file_load = Gtk.MenuItem("Load Settings from File")
        menu_item_file_load.connect("activate", self.load_settings, "from_menu")
        menu_item_file_load.show()

        menu_item_file_save = Gtk.MenuItem("Save Settings to File")
        menu_item_file_save.connect("activate", self.save_settings, "from_menu")
        menu_item_file_save.show()

        # create an exit button
        menu_item_file_exit = Gtk.MenuItem("Exit")
        menu_item_file_exit.connect("activate", Gtk.main_quit)
        menu_item_file_exit.show()

        # create the base root menu item for FILE
        menu_item_file = Gtk.MenuItem("File")

        # create a menu to hold FILE items and put them in there
        file_menu = Gtk.Menu()
        file_menu.append(menu_item_file_load)
        file_menu.append(menu_item_file_save)
        file_menu.append(Gtk.SeparatorMenuItem())
        file_menu.append(menu_item_file_exit)
        menu_item_file.set_submenu(file_menu)

        # attach the FILE menu to the main menu bar
        mb.append(menu_item_file)

        menu_item_help_pdf = Gtk.MenuItem("Open Online Documentation")
        menu_item_help_pdf.connect("activate", self.open_documentation)
        menu_item_help_pdf.show()

        menu_item_help = Gtk.MenuItem("Help")
        help_menu = Gtk.Menu()
        help_menu.append(menu_item_help_pdf)
        menu_item_help.set_submenu(help_menu)

        # attach the HELP menu to the main menu bar
        mb.append(menu_item_help)

        return mb

    def load_settings(self, widget, from_menu=False):

        # auto-save when closing if from_menu is False
        settings_file = os.path.join(os.path.expanduser("~"), ".saved-epsuite-settings")
        if from_menu:
            sure_dialog = Gtk.MessageDialog(
                self, flags=0, type=Gtk.MessageType.QUESTION, buttons=Gtk.ButtonsType.YES_NO,
                message_format="Are you sure you want to load a new configuration?"
            )
            response = sure_dialog.run()
            sure_dialog.destroy()
            if response == Gtk.ResponseType.NO:
                return
            dialog = Gtk.FileChooserDialog(title="Select settings file", buttons=(
                Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_OPEN, Gtk.ResponseType.OK))
            dialog.set_select_multiple(False)
            if self.last_folder_path:
                dialog.set_current_folder(self.last_folder_path)
            a_filter = Gtk.FileFilter()
            a_filter.set_name("EPT Files")
            a_filter.add_pattern("*.ept")
            dialog.add_filter(a_filter)
            response = dialog.run()
            if response == Gtk.ResponseType.OK:
                self.last_folder_path = dialog.get_current_folder()
                settings_file = dialog.get_filename()
                dialog.destroy()
            else:
                dialog.destroy()
                return
        else:
            if not os.path.exists(settings_file):
                # abort early because there isn't an auto-saved file
                return

        file_content = open(settings_file, 'r').read()
        try:
            project_tree = json.loads(file_content)
        except json.decoder.JSONDecodeError:
            print("Could not process settings save file, may be an old XML version")
            return

        if "idfselection" in project_tree:
            idf_select_data = project_tree['idfselection']
            if "masterfile" in idf_select_data:
                self.file_list_builder_configuration.master_data_file = idf_select_data["masterfile"]
            if 'selectedfiles' in idf_select_data:
                self.try_to_restore_files = idf_select_data['selectedfiles']
            if 'randomnumber' in idf_select_data:
                self.file_list_num_files.set_value(int(idf_select_data['randomnumber']))
        if 'suiteoptions' in project_tree:
            suite_data = project_tree['suiteoptions']
            if 'case_a' in suite_data:
                case_a = suite_data['case_a']
                self.suiteargs.buildA.run = case_a['selected']
                self.suiteargs.buildA.build_directory = case_a['build_directory']
            if 'case_b' in suite_data:
                case_b = suite_data['case_b']
                self.suiteargs.buildB.run = case_b['selected']
                self.suiteargs.buildB.build_directory = case_b["build_directory"]
            if 'runconfig' in suite_data:
                run_config_option = suite_data['runconfig']
                if run_config_option == "NONE":
                    self.suiteargs.force_run_type = ForceRunType.NONE
                elif run_config_option == "DDONLY":
                    self.suiteargs.force_run_type = ForceRunType.DD
                elif run_config_option == "ANNUAL":
                    self.suiteargs.force_run_type = ForceRunType.ANNUAL
            if 'reportfreq' in suite_data:
                self.suiteargs.report_freq = suite_data['reportfreq']
            if 'numthreads' in suite_data:
                self.suiteargs.num_threads = suite_data['numthreads']
        if from_menu:
            self.gui_fill_with_data()

    def gui_fill_with_data(self):

        self.case_1_check.set_active(self.suiteargs.buildA.run)
        if self.suiteargs.buildA.build_directory:
            self.case_1_build_dir_label.set_text(self.suiteargs.buildA.build_directory)

        self.case_2_check.set_active(self.suiteargs.buildB.run)
        if self.suiteargs.buildB.build_directory:
            self.case_2_build_dir_label.set_text(self.suiteargs.buildB.build_directory)

        # num threads here
        if self.suiteargs.force_run_type:
            if self.suiteargs.force_run_type == ForceRunType.NONE:
                self.run_type_combo_box.set_active(0)
            elif self.suiteargs.force_run_type == ForceRunType.DD:
                self.run_type_combo_box.set_active(1)
            elif self.suiteargs.force_run_type == ForceRunType.ANNUAL:
                self.run_type_combo_box.set_active(2)
        if self.suiteargs.report_freq:
            if self.suiteargs.report_freq == ReportingFreq.DETAILED:
                self.report_frequency_combo_box.set_active(0)
            elif self.suiteargs.report_freq == ReportingFreq.TIMESTEP:
                self.report_frequency_combo_box.set_active(1)
            elif self.suiteargs.report_freq == ReportingFreq.HOURLY:
                self.report_frequency_combo_box.set_active(2)
            elif self.suiteargs.report_freq == ReportingFreq.DAILY:
                self.report_frequency_combo_box.set_active(3)
            elif self.suiteargs.report_freq == ReportingFreq.MONTHLY:
                self.report_frequency_combo_box.set_active(4)
            elif self.suiteargs.report_freq == ReportingFreq.RUNPERIOD:
                self.report_frequency_combo_box.set_active(5)
            elif self.suiteargs.report_freq == ReportingFreq.ENVIRONMENT:
                self.report_frequency_combo_box.set_active(6)
            elif self.suiteargs.report_freq == ReportingFreq.ANNUAL:
                self.report_frequency_combo_box.set_active(7)

    def save_settings(self, widget, from_menu=False):

        # if we are already saving, don't do it again at the same time, just get out! :)
        # this could cause a - uh - problem if the user attempts to save during an auto-save
        # but what are the chances, meh, we can issue a log message that might show up long enough in the status bar
        if self.currently_saving:
            self.status_bar.push(
                self.status_bar_context_id,
                "Attempted a (perhaps auto-) save while another (perhaps auto-) save was in progress; try again now"
            )
            return

        # now trigger the flag
        self.currently_saving = True

        # auto-save when closing if from_menu is False
        save_file = os.path.join(os.path.expanduser("~"), ".saved-epsuite-settings")
        if from_menu:
            dialog = Gtk.FileChooserDialog(
                title="Select settings file save name", action=Gtk.FileChooserAction.SAVE,
                buttons=(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_OPEN, Gtk.ResponseType.OK)
            )
            dialog.set_select_multiple(False)
            if self.last_folder_path:
                dialog.set_current_folder(self.last_folder_path)
            a_filter = Gtk.FileFilter()
            a_filter.set_name("EPT Files")
            a_filter.add_pattern("*.ept")
            dialog.add_filter(a_filter)
            response = dialog.run()
            if response == Gtk.ResponseType.OK:
                self.last_folder_path = dialog.get_current_folder()
                save_file = dialog.get_filename()
                dialog.destroy()
            else:
                dialog.destroy()
                # reset the flag
                self.currently_saving = False
                return

        output_object = dict()
        output_object['idfselection'] = {}
        output_object['idfselection']['masterfile'] = self.file_list_builder_configuration.master_data_file
        output_object['idfselection']['selectedfiles'] = []
        for idf_entry in self.idf_list_store:
            if idf_entry[IDFListViewColumnIndex.RUN]:
                output_object['idfselection']['selectedfiles'].append(idf_entry[IDFListViewColumnIndex.IDF])
        output_object['idfselection']['randomnumber'] = self.file_list_num_files.get_value()
        output_object['suiteoptions'] = {}
        output_object['suiteoptions']['case_a'] = {
            'selected': self.suiteargs.buildA.run,
            'build_directory': self.suiteargs.buildA.build_directory
        }
        output_object['suiteoptions']['case_b'] = {
            'selected': self.suiteargs.buildB.run,
            'build_directory': self.suiteargs.buildB.build_directory
        }
        if self.suiteargs.force_run_type == ForceRunType.NONE:
            output_object['suiteoptions']['runconfig'] = "NONE"
        elif self.suiteargs.force_run_type == ForceRunType.DD:
            output_object['suiteoptions']['runconfig'] = "DDONLY"
        elif self.suiteargs.force_run_type == ForceRunType.ANNUAL:
            output_object['suiteoptions']['runconfig'] = "ANNUAL"
        output_object['suiteoptions']['reportfreq'] = self.suiteargs.report_freq
        output_object['suiteoptions']['numthreads'] = self.suiteargs.num_threads

        with open(save_file, 'w') as f_save:
            f_save.write(json.dumps(output_object, indent=2))

        # reset the flag
        self.currently_saving = False

        # since this is included in auto-save, return True to the timeout_add function
        # for normal (manual) saving, this will return to nothingness most likely
        return True

    def restore_file_selection(self, file_list):
        for idf_entry in self.idf_list_store:
            idf_entry[IDFListViewColumnIndex.RUN] = False
        for filename in self.try_to_restore_files:
            for idf_entry in file_list:
                if idf_entry[IDFListViewColumnIndex.IDF] == filename:  # if it matches
                    idf_entry[IDFListViewColumnIndex.RUN] = True

    def gui_build_notebook_page_test_suite(self):

        notebook_page_suite = Gtk.HPaned()
        notebook_page_suite_options = Gtk.VBox(False, box_spacing)

        notebook_page_suite_options.pack_start(self.add_frame(Gtk.HSeparator(), True), False, True, box_spacing)

        heading = Gtk.Label(None)
        heading.set_markup("<b>Test Suite Directories:</b>")
        alignment = Gtk.Alignment(xalign=0.0, xscale=0.0)
        alignment.add(heading)
        this_h_box = Gtk.HBox(False, box_spacing)
        this_h_box.pack_start(alignment, False, False, box_spacing)
        notebook_page_suite_options.pack_start(this_h_box, False, False, box_spacing)

        h_box_1 = Gtk.HBox(False, box_spacing)
        this_label = Gtk.Label("Case 1: ")
        alignment = Gtk.Alignment(xalign=0.0, yalign=0.5, xscale=0.0, yscale=0.0)
        alignment.add(this_label)
        h_box_1.pack_start(alignment, False, False, box_spacing)
        self.case_1_check = Gtk.CheckButton("Run Case 1?", use_underline=False)
        self.case_1_check.set_active(self.suiteargs.buildA.run)
        self.case_1_check.connect("toggled", self.suite_option_handler_basedir_check)
        alignment = Gtk.Alignment(xalign=0.0, yalign=0.5, xscale=0.0, yscale=0.0)
        alignment.add(self.case_1_check)
        h_box_1.pack_start(alignment, False, False, box_spacing)
        notebook_page_suite_options.pack_start(h_box_1, False, False, box_spacing)

        h_box_case_1_build = Gtk.HBox(False, box_spacing)
        button1 = Gtk.Button("Build Directory: ")
        button1.connect("clicked", self.suite_option_handler_base_build_dir)
        alignment = Gtk.Alignment(xalign=0.0, yalign=0.5, xscale=0.2, yscale=0.0)
        alignment.add(button1)
        h_box_case_1_build.pack_start(alignment, False, False, box_spacing)
        self.case_1_build_dir_label = Gtk.Label("<select_build_dir>")
        alignment = Gtk.Alignment(xalign=0.0, yalign=0.5, xscale=0.0, yscale=0.0)
        alignment.add(self.case_1_build_dir_label)
        h_box_case_1_build.pack_start(alignment, False, False, box_spacing)
        notebook_page_suite_options.pack_start(h_box_case_1_build, False, False, box_spacing)

        h_box_2 = Gtk.HBox(False, box_spacing)
        this_label = Gtk.Label("Case 2: ")
        alignment = Gtk.Alignment(xalign=0.0, yalign=0.5, xscale=0.0, yscale=0.0)
        alignment.add(this_label)
        h_box_2.pack_start(alignment, False, False, box_spacing)
        self.case_2_check = Gtk.CheckButton("Run Case 2?", use_underline=False)
        self.case_2_check.set_active(self.suiteargs.buildB.run)
        self.case_2_check.connect("toggled", self.suite_option_handler_mod_dir_check)
        alignment = Gtk.Alignment(xalign=0.0, yalign=0.5, xscale=0.0, yscale=0.0)
        alignment.add(self.case_2_check)
        h_box_2.pack_start(alignment, False, False, box_spacing)
        notebook_page_suite_options.pack_start(h_box_2, False, False, box_spacing)

        h_box_case_2_build = Gtk.HBox(False, box_spacing)
        button1 = Gtk.Button("Build Directory: ")
        button1.connect("clicked", self.suite_option_handler_mod_build_dir)
        alignment = Gtk.Alignment(xalign=0.0, yalign=0.5, xscale=0.2, yscale=0.0)
        alignment.add(button1)
        h_box_case_2_build.pack_start(alignment, False, False, box_spacing)
        self.case_2_build_dir_label = Gtk.Label("<select_build_dir>")
        alignment = Gtk.Alignment(xalign=0.0, yalign=0.5, xscale=0.0, yscale=0.0)
        alignment.add(self.case_2_build_dir_label)
        h_box_case_2_build.pack_start(alignment, False, False, box_spacing)
        notebook_page_suite_options.pack_start(h_box_case_2_build, False, False, box_spacing)

        notebook_page_suite_options.pack_start(self.add_frame(Gtk.HSeparator(), True), False, True, box_spacing)

        heading = Gtk.Label(None)
        heading.set_markup("<b>IDF Selection:</b>")
        alignment = Gtk.Alignment(xalign=0.0, xscale=0.0)
        alignment.add(heading)
        this_h_box = Gtk.HBox(False, box_spacing)
        this_h_box.pack_start(alignment, False, False, box_spacing)
        notebook_page_suite_options.pack_start(this_h_box, False, False, box_spacing)

        h_box_select_1 = Gtk.HBox(False, box_spacing)
        button = Gtk.Button("Select All")
        button.connect("clicked", self.idf_selection_all, "select")
        alignment = Gtk.Alignment(xalign=0.0, yalign=0.5, xscale=1.0, yscale=0.0)
        alignment.add(button)
        h_box_select_1.pack_start(alignment, True, True, box_spacing)
        button = Gtk.Button("Deselect All")
        button.connect("clicked", self.idf_selection_all, "deselect")
        alignment = Gtk.Alignment(xalign=0.0, yalign=0.5, xscale=1.0, yscale=0.0)
        alignment.add(button)
        h_box_select_1.pack_start(alignment, True, True, box_spacing)
        notebook_page_suite_options.pack_start(h_box_select_1, False, False, box_spacing)

        h_box_select_2 = Gtk.HBox(False, box_spacing)
        self.file_list_num_files = Gtk.SpinButton()
        self.file_list_num_files.set_range(0, 1000)
        self.file_list_num_files.set_increments(1, 10)
        self.file_list_num_files.spin(Gtk.SpinType.PAGE_FORWARD, 1)
        alignment = Gtk.Alignment(xalign=0.0, yalign=0.5, xscale=1.0, yscale=0.0)
        alignment.add(self.file_list_num_files)
        h_box_select_2.pack_start(alignment, True, True, box_spacing)
        button = Gtk.Button("Select N Random Files")
        button.connect("clicked", self.idf_selection_random, "select")
        alignment = Gtk.Alignment(xalign=0.0, yalign=0.5, xscale=1.0, yscale=0.0)
        alignment.add(button)
        h_box_select_2.pack_start(alignment, True, True, box_spacing)
        notebook_page_suite_options.pack_start(h_box_select_2, False, False, box_spacing)

        h_box_select_3 = Gtk.HBox(False, box_spacing)
        button = Gtk.Button("Select from List")
        button.connect("clicked", self.idf_selection_list)
        alignment = Gtk.Alignment(xalign=0.0, yalign=0.5, xscale=1.0, yscale=0.0)
        alignment.add(button)
        h_box_select_3.pack_start(alignment, True, True, box_spacing)
        button = Gtk.Button("Select from Folder")
        button.connect("clicked", self.idf_selection_dir)
        alignment = Gtk.Alignment(xalign=0.0, yalign=0.5, xscale=1.0, yscale=0.0)
        alignment.add(button)
        h_box_select_3.pack_start(alignment, True, True, box_spacing)
        notebook_page_suite_options.pack_start(h_box_select_3, False, False, box_spacing)

        notebook_page_suite_options.pack_start(self.add_frame(Gtk.HSeparator(), True), False, True, box_spacing)

        heading = Gtk.Label(None)
        heading.set_markup("<b>Options:</b>")
        alignment = Gtk.Alignment(xalign=0.0, xscale=0.0)
        alignment.add(heading)
        this_h_box = Gtk.HBox(False, box_spacing)
        this_h_box.pack_start(alignment, False, False, box_spacing)
        notebook_page_suite_options.pack_start(this_h_box, False, False, box_spacing)

        # multi-threading in the GUI doesn't works in windows, so don't add the spin-button if we are on windows
        if platform != "windows":
            num_threads_box = Gtk.HBox(False, box_spacing)
            self.suite_option_num_threads = Gtk.SpinButton()
            self.suite_option_num_threads.set_range(1, 8)
            self.suite_option_num_threads.set_increments(1, 4)
            self.suite_option_num_threads.spin(Gtk.SpinType.PAGE_FORWARD, 1)  # EDWIN: Had to add a 1 here
            self.suite_option_num_threads.connect("value-changed", self.suite_option_handler_num_threads)
            num_threads_label = Gtk.Label("Number of threads to use for suite: ")
            num_threads_label_aligner = Gtk.Alignment(xalign=0.0, yalign=0.5, xscale=1.0, yscale=0.0)
            num_threads_label_aligner.add(num_threads_label)
            num_threads_box.pack_start(num_threads_label_aligner, False, False, box_spacing)
            num_threads_box.pack_start(self.suite_option_num_threads, True, True, box_spacing)
            notebook_page_suite_options.pack_start(num_threads_box, False, False, box_spacing)

        h_box_1 = Gtk.HBox(False, box_spacing)
        label1 = Gtk.Label("Select a test suite run configuration: ")
        alignment = Gtk.Alignment(xalign=0.0, yalign=0.5, xscale=1.0, yscale=0.0)
        alignment.add(label1)
        h_box_1.pack_start(alignment, False, False, box_spacing)
        self.run_type_combo_box = Gtk.ComboBoxText()
        self.run_type_combo_box.append_text(force_none)
        self.run_type_combo_box.append_text(force_dd)
        self.run_type_combo_box.append_text(force_annual)
        self.run_type_combo_box.connect("changed", self.suite_option_handler_force_run_type)
        alignment = Gtk.Alignment(xalign=0.0, yalign=0.5, xscale=1.0, yscale=0.0)
        alignment.add(self.run_type_combo_box)
        h_box_1.pack_start(alignment, True, True, box_spacing)
        notebook_page_suite_options.pack_start(h_box_1, False, False, box_spacing)

        h_box_1 = Gtk.HBox(False, box_spacing)
        label1 = Gtk.Label("Select a minimum reporting frequency: ")
        alignment = Gtk.Alignment(xalign=0.0, yalign=0.5, xscale=1.0, yscale=0.0)
        alignment.add(label1)
        h_box_1.pack_start(alignment, False, False, box_spacing)
        self.report_frequency_combo_box = Gtk.ComboBoxText()
        self.report_frequency_combo_box.append_text(ReportingFreq.DETAILED)
        self.report_frequency_combo_box.append_text(ReportingFreq.TIMESTEP)
        self.report_frequency_combo_box.append_text(ReportingFreq.HOURLY)
        self.report_frequency_combo_box.append_text(ReportingFreq.DAILY)
        self.report_frequency_combo_box.append_text(ReportingFreq.MONTHLY)
        self.report_frequency_combo_box.append_text(ReportingFreq.RUNPERIOD)
        self.report_frequency_combo_box.append_text(ReportingFreq.ENVIRONMENT)
        self.report_frequency_combo_box.append_text(ReportingFreq.ANNUAL)
        self.report_frequency_combo_box.connect("changed", self.suite_option_handler_report_frequency)
        alignment = Gtk.Alignment(xalign=0.0, yalign=0.5, xscale=1.0, yscale=0.0)
        alignment.add(self.report_frequency_combo_box)
        h_box_1.pack_start(alignment, True, True, box_spacing)
        notebook_page_suite_options.pack_start(h_box_1, False, False, box_spacing)

        this_h_box = Gtk.HBox(False, box_spacing)
        self.suite_option_handler_runtime_report_check = Gtk.CheckButton("Create Runtime Summary?", use_underline=False)
        self.suite_option_handler_runtime_report_check.set_active(True)
        self.suite_option_handler_runtime_report_check.connect("toggled", self.suite_option_handler_runtime_check)
        alignment = Gtk.Alignment(xalign=0.0, xscale=0.0)
        alignment.add(self.suite_option_handler_runtime_report_check)
        this_h_box.pack_start(alignment, False, False, box_spacing)
        button1 = Gtk.Button("Choose Runtime File...")
        button1.connect("clicked", self.suite_option_handler_runtime_file)
        alignment = Gtk.Alignment(xalign=0.0, yalign=0.5, xscale=0.0, yscale=0.0)
        alignment.add(button1)
        this_h_box.pack_start(alignment, False, False, box_spacing)
        self.suite_option_runtime_file_label = Gtk.Label(self.runtime_report_file)
        alignment = Gtk.Alignment(xalign=0.0, yalign=0.5, xscale=0.0, yscale=0.0)
        alignment.add(self.suite_option_runtime_file_label)
        this_h_box.pack_start(alignment, False, False, box_spacing)
        notebook_page_suite_options.pack_start(this_h_box, False, False, box_spacing)

        notebook_page_suite_options.pack_start(self.add_frame(Gtk.HSeparator(), True), False, True, box_spacing)

        heading = Gtk.Label(None)
        heading.set_markup("<b>Ready to Run:</b>")
        alignment = Gtk.Alignment(xalign=0.0, xscale=0.0)
        alignment.add(heading)
        this_h_box = Gtk.HBox(False, box_spacing)
        this_h_box.pack_start(alignment, False, False, box_spacing)
        notebook_page_suite_options.pack_start(this_h_box, False, False, box_spacing)

        self.suite_dir_struct_info = Gtk.Label("<Test suite run directory structure information>")
        self.gui_update_label_for_run_config()
        aligner = Gtk.Alignment(xalign=0.0, yalign=0.5, xscale=0.0, yscale=0.0)
        aligner.add(self.suite_dir_struct_info)
        this_h_box = Gtk.HBox(False, box_spacing)
        this_h_box.pack_start(aligner, False, False, box_spacing)
        notebook_page_suite_options.pack_start(this_h_box, False, False, box_spacing)

        h_box_1 = Gtk.HBox(False, box_spacing)
        button1 = Gtk.Button("Validate Test Suite Structure")
        button1.connect("clicked", self.suite_option_handler_suite_validate)
        alignment = Gtk.Alignment(xalign=0.0, yalign=0.5, xscale=1.0, yscale=0.0)
        alignment.add(button1)
        h_box_1.pack_start(alignment, True, True, box_spacing)
        self.btn_run_suite = Gtk.Button("Run Suite")
        self.btn_run_suite.connect("clicked", self.run_button)
        self.btn_run_suite.set_size_request(120, -1)
        # green = self.btn_run_suite.get_colormap().alloc_color("green")  # EDWIN: Commented this out because no
        # style = self.btn_run_suite.get_style().copy()
        # style.bg[Gtk.STATE_NORMAL] = green
        # self.btn_run_suite.set_style(style)
        alignment = Gtk.Alignment(xalign=0.0, yalign=0.5, xscale=1.0, yscale=0.0)
        alignment.add(self.btn_run_suite)
        h_box_1.pack_start(alignment, True, True, box_spacing)
        notebook_page_suite_options.pack_start(h_box_1, False, False, box_spacing)

        v_box_right = Gtk.VPaned()

        # PAGE: IDF LIST RESULTS
        listview_window = Gtk.ScrolledWindow()
        listview_window.set_size_request(750, -1)
        listview_window.set_shadow_type(Gtk.ShadowType.ETCHED_IN)
        listview_window.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)

        self.idf_list_store = Gtk.ListStore(bool, str, str)
        self.idf_list_store.append([False, "-- Re-build idf list --", "-- to see results --"])
        tree_view = Gtk.TreeView(self.idf_list_store)
        tree_view.set_rules_hint(True)
        # make the columns for the tree view; could add more columns including a checkbox
        # column: selected for run
        renderer_toggle = Gtk.CellRendererToggle()
        renderer_toggle.connect("toggled", self.file_list_handler_toggle_listview, self.idf_list_store)
        column = Gtk.TreeViewColumn("Run?", renderer_toggle, active=IDFListViewColumnIndex.RUN)
        column.set_sort_column_id(0)
        tree_view.append_column(column)
        # column: idf name
        renderer_text = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn("IDF Base name", renderer_text, text=IDFListViewColumnIndex.IDF)
        column.set_sort_column_id(1)
        column.set_resizable(True)
        tree_view.append_column(column)
        # column: epw name
        renderer_text = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn("EPW Base name", renderer_text, text=IDFListViewColumnIndex.EPW)
        column.set_sort_column_id(2)
        column.set_resizable(True)
        tree_view.append_column(column)

        listview_window.add(tree_view)
        aligner = Gtk.Alignment(xalign=0, yalign=0, xscale=1, yscale=1)
        aligner.add(listview_window)
        v_box_right.pack1(aligner)

        listview_window = Gtk.ScrolledWindow()
        listview_window.set_size_request(-1, 475)
        listview_window.set_shadow_type(Gtk.ShadowType.ETCHED_IN)
        listview_window.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        # make the list store and the treeview
        self.verify_list_store = Gtk.ListStore(str, str, bool, str)
        self.verify_list_store.append(["Press \"Validate Test Suite Structure\" to see results", "", True, None])
        self.verify_tree_view = Gtk.TreeView(self.verify_list_store)
        self.verify_tree_view.set_rules_hint(True)
        # make the columns for the treeview; could add more columns including a checkbox
        # column: idf name
        renderer_text = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn("Verified Parameter", renderer_text, text=0)
        column.set_sort_column_id(0)
        column.set_resizable(True)
        self.verify_tree_view.append_column(column)
        # column: selected for run
        renderer_text = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn("Verified?", renderer_text, text=2, foreground=3)
        column.set_sort_column_id(1)
        self.verify_tree_view.append_column(column)
        # column: epw name
        renderer_text = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn("Parameter Value", renderer_text, text=1)
        column.set_sort_column_id(2)
        column.set_resizable(True)
        self.verify_tree_view.append_column(column)
        listview_window.add(self.verify_tree_view)
        v_box_right.pack2(listview_window)
        v_box_right.set_position(int(listview_window.get_size_request()[1] / 2))

        notebook_page_suite.pack1(self.add_shadow_frame(notebook_page_suite_options))
        notebook_page_suite.pack2(self.add_shadow_frame(v_box_right))
        return notebook_page_suite

    def gui_build_notebook_page_last_run(self):

        # PAGE 4: LAST RUN SUMMARY
        notebook_page_results = Gtk.ScrolledWindow()
        notebook_page_results.set_size_request(-1, 475)
        notebook_page_results.set_shadow_type(Gtk.ShadowType.ETCHED_IN)
        notebook_page_results.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)

        self.results_list_store = Gtk.TreeStore(str)
        self.results_parent_num_run = self.results_list_store.append(None, ["Cases run:"])
        self.results_parent_success = self.results_list_store.append(None, ["Case 1 Successful runs:"])
        self.results_parent_not_success = self.results_list_store.append(None, ["Case 1 Unsuccessful run:"])
        self.results_parent_success_2 = self.results_list_store.append(None, ["Case 2 Successful runs:"])
        self.results_parent_not_success_2 = self.results_list_store.append(None, ["Case 2 Unsuccessful run:"])
        self.results_parent_files_compared = self.results_list_store.append(None, ["Files compared:"])
        self.results_parent_big_math = self.results_list_store.append(None, ["Files with BIG mathdiffs:"])
        self.results_parent_small_math = self.results_list_store.append(None, ["Files with small mathdiffs:"])
        self.results_parent_big_table = self.results_list_store.append(None, ["Files with BIG tablediffs:"])
        self.results_parent_small_table = self.results_list_store.append(None, ["Files with small tablediffs:"])
        self.results_parent_textual = self.results_list_store.append(None, ["Files with textual diffs:"])

        self.results_child_num_run = None
        self.results_child_success = None
        self.results_child_not_success = None
        self.results_child_success_2 = None
        self.results_child_not_success_2 = None
        self.results_child_files_compared = None
        self.results_child_big_math = None
        self.results_child_small_math = None
        self.results_child_big_table = None
        self.results_child_small_table = None
        self.results_child_textual = None

        self.tree_view = Gtk.TreeView(self.results_list_store)
        self.tree_view.set_rules_hint(True)
        tree_view_column = Gtk.TreeViewColumn('Results Summary')
        cell = Gtk.CellRendererText()
        tree_view_column.pack_start(cell, True)
        tree_view_column.add_attribute(cell, 'text', 0)
        self.tree_view.append_column(tree_view_column)

        self.tree_view.connect_object("button-release-event", self.handle_tree_view_context_menu, self.last_run_context)
        self.tree_view.connect("row-activated", self.handle_tree_view_row_activated)
        self.tree_selection = self.tree_view.get_selection()

        self.last_run_heading = Gtk.Label(None)
        self.last_run_heading.set_markup(
            "<b>Hint:</b> Try double-clicking on a filename to launch a file browser to that folder.")
        alignment = Gtk.Alignment(xalign=0.0, xscale=0.0)
        alignment.add(self.last_run_heading)
        this_hbox = Gtk.HBox(False, box_spacing)
        this_hbox.pack_start(alignment, False, False, box_spacing)

        v_box = Gtk.VBox(False, box_spacing)
        v_box.pack_start(this_hbox, False, False, box_spacing)
        notebook_page_results.add(self.tree_view)

        v_box.add(notebook_page_results)
        return v_box

    def handle_tree_view_row_activated(self, tv_widget, path_tuple, view_column):
        # Get currently selected item        
        (model, item_path) = self.tree_selection.get_selected()
        # If we aren't at the filename level, exit out
        if len(path_tuple) < 3:
            print("Activated non-file entry")
            return
        # Get the filename entry
        tree_iter = model.get_iter(path_tuple)
        case_name = model.get_value(tree_iter, 0)
        # Clean the filename entry
        if ":" in case_name:
            colon_index = case_name.index(":")
            case_name = case_name[:colon_index]
        test_dir = "Tests"
        if self.suiteargs.force_run_type == ForceRunType.DD:
            test_dir = "Tests-DDOnly"
        elif self.suiteargs.force_run_type == ForceRunType.ANNUAL:
            test_dir = "Tests-Annual"
        dir_to_open = os.path.join(self.suiteargs.buildA.build_directory, test_dir, case_name)
        if platform == "linux":
            try:
                subprocess.Popen(['xdg-open', dir_to_open])
            except Exception as this_exception:
                print("Could not open file:")
                print(this_exception)
        elif platform == "windows":
            try:
                subprocess.Popen(['start', dir_to_open], shell=True)
            except Exception as this_exception:
                print("Could not open file:")
                print(this_exception)
        elif platform == "mac":
            try:
                subprocess.Popen(['open', dir_to_open])
            except Exception as this_exception:
                print("Could not open file:")
                print(this_exception)

    def gui_build_notebook_page_log(self):

        self.log_scroll_notebook_page = Gtk.ScrolledWindow()
        self.log_scroll_notebook_page.set_shadow_type(Gtk.ShadowType.ETCHED_IN)
        self.log_scroll_notebook_page.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)

        self.log_store = Gtk.ListStore(str, str)
        self.log_store.append(["%s" % str(datetime.now()), "%s" % "Program initialized"])

        tree_view = Gtk.TreeView(self.log_store)
        tree_view.set_rules_hint(True)
        tree_view.connect("size-allocate", self.tree_view_size_changed)

        column = Gtk.TreeViewColumn("TimeStamp", Gtk.CellRendererText(), text=0)
        column.set_sort_column_id(0)
        column.set_resizable(True)
        tree_view.append_column(column)

        column = Gtk.TreeViewColumn("Message", Gtk.CellRendererText(), text=1)
        column.set_sort_column_id(1)
        column.set_resizable(True)
        tree_view.append_column(column)
        self.log_scroll_notebook_page.add(tree_view)

        v_box = Gtk.VBox(False, box_spacing)
        v_box.pack_start(
            self.log_scroll_notebook_page, True, True, box_spacing
        )

        h_box_buttons = Gtk.HBox(True, box_spacing)
        save_button = Gtk.Button("Save Log Messages")
        save_button.connect("clicked", self.save_log)
        alignment = Gtk.Alignment(xalign=0.5, yalign=0.0, xscale=0.0, yscale=0.0)
        alignment.add(save_button)
        h_box_buttons.pack_start(alignment, False, False, box_spacing)
        clear_button = Gtk.Button("Clear Log Messages")
        clear_button.connect("clicked", self.clear_log)
        alignment = Gtk.Alignment(xalign=0.5, yalign=0.0, xscale=0.0, yscale=0.0)
        alignment.add(clear_button)
        h_box_buttons.pack_start(alignment, False, False, box_spacing)
        v_box.pack_start(h_box_buttons, False, False, box_spacing)

        return v_box

    def save_log(self, widget):
        output_string = '\n'.join(["%s: %s" % (x[0], x[1]) for x in self.log_store])
        save_file = os.path.join(os.path.expanduser("~"), "log_messages.log")
        dialog = Gtk.FileChooserDialog(
            title="Select log messages save file name", action=Gtk.FileChooserAction.SAVE,
            buttons=(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_OPEN, Gtk.ResponseType.OK)
        )
        dialog.set_select_multiple(False)
        if self.last_folder_path:
            dialog.set_current_folder(self.last_folder_path)
        a_filter = Gtk.FileFilter()
        a_filter.set_name("Log Files")
        a_filter.add_pattern("*.log")
        dialog.add_filter(a_filter)
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            self.last_folder_path = dialog.get_current_folder()
            save_file = dialog.get_filename()
            dialog.destroy()
        else:
            dialog.destroy()
            return
        try:
            with open(save_file, 'w') as f_save:
                f_save.write(output_string)
        except Exception as write_exception:
            self.warning_dialog('Problem writing save file, log not saved; error: %s' % str(write_exception))
            return

    def clear_log(self, widget):
        self.log_store.clear()

    def tree_view_size_changed(self, widget, event, data=None):

        # this routine should auto-scroll the v-adjustment if
        # the user is scrolled to within 0.2*page height of the widget

        # get things once
        adj = self.log_scroll_notebook_page.get_vadjustment()
        cur_val = adj.get_value()
        new_upper = adj.get_upper()
        page_size = adj.get_page_size()

        # only adjust it if the user is very close to the upper value
        cur_bottom = cur_val + page_size
        distance_from_bottom = new_upper - cur_bottom
        fraction_of_page_size = 0.2 * page_size
        if distance_from_bottom < fraction_of_page_size:
            adj.set_value(new_upper - page_size)
            return True
        else:
            return False

    def gui_build_notebook(self):
        self.notebook = Gtk.Notebook()
        self.notebook.append_page(self.gui_build_notebook_page_test_suite(), Gtk.Label("Test Suite"))
        self.notebook.append_page(self.gui_build_notebook_page_last_run(), Gtk.Label("Last Run Summary"))
        self.notebook.append_page(self.gui_build_notebook_page_log(), Gtk.Label("Log Messages"))
        return self.notebook

    def gui_build_messaging(self):
        self.progress = Gtk.ProgressBar()
        self.status_bar = Gtk.Statusbar()
        aligner = Gtk.Alignment(xalign=1.0, yalign=0.0, xscale=0.4, yscale=1.0)
        aligner.add(self.progress)
        self.status_bar.pack_start(aligner, False, False, box_spacing)
        self.status_bar_context_id = self.status_bar.get_context_id("Status")
        aligner = Gtk.Alignment(xalign=1.0, yalign=1.0, xscale=1.0, yscale=0.0)
        aligner.add(self.status_bar)
        return aligner

    @staticmethod
    def add_frame(widget, for_separator=False):
        frame = Gtk.Frame()
        if for_separator:
            color = Gdk.Color(76*256, 72*256, 69*256)
        else:
            color = Gdk.Color(56283, 22359, 0)
        frame.modify_bg(Gtk.StateType.NORMAL, color)
        frame.add(widget)
        return frame

    @staticmethod
    def add_shadow_frame(widget):
        frame = Gtk.Frame()
        frame.set_shadow_type(Gtk.ShadowType.IN)
        frame.add(widget)
        return frame

    def add_log_entry(self, message):
        if len(self.log_store) >= 5000:
            self.log_store.remove(self.log_store[0].iter)
        self.log_store.append(["%s" % str(datetime.now()), "%s" % message])

    def warning_dialog(self, message, do_log_entry=True):
        dialog = Gtk.MessageDialog(
            self, Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT,
            Gtk.MessageType.WARNING,
            Gtk.ButtonsType.OK,
            message
        )
        dialog.set_title("Warning message")
        dialog.run()
        if do_log_entry:
            self.add_log_entry("Warning: %s" % message)
        dialog.destroy()

    def warning_not_yet_built(self):
        self.warning_dialog("File selection and/or test suite operations can't be performed until master list is built")

    def open_documentation(self, widget):
        url = 'https://energyplusregressiontool.readthedocs.io/en/latest/'
        try:
            webbrowser.open_new_tab(url)
        except Exception as this_exception:
            # error message
            dialog = Gtk.MessageDialog(
                self, Gtk.DialogFlags.DESTROY_WITH_PARENT, Gtk.MessageType.ERROR, Gtk.ButtonsType.CLOSE,
                "Could not open browser file.  Try opening manually.  Documentation is at:\n %s" % url
            )
            dialog.run()
            dialog.destroy()
            print(this_exception)
            return

    # IDF selection worker and handlers for buttons and checkboxes, etc.

    def init_file_list_builder_args(self):

        # could read from temp file

        # build a default set of arguments
        self.file_list_builder_configuration = FileListArgsBuilderForGUI()

        # override with our defaults
        self.file_list_builder_configuration.check = False
        self.file_list_builder_configuration.master_data_file = os.path.join(script_dir, 'full_file_set_details.csv')

    def build_button(self, widget):

        self.status_bar.push(self.status_bar_context_id, "Building idf list")

        file_builder = FileListBuilder(self.file_list_builder_configuration)
        file_builder.set_callbacks(self.build_callback_print, self.build_callback_init, self.build_callback_increment)
        return_data = file_builder.build_verified_list(self.file_list_builder_configuration)
        status, verified_idf_files, idf_files_missing_in_folder, idf_files_missing_from_csv_file = return_data

        # reset the progress bar either way
        self.progress.set_fraction(self.current_progress_value / self.progress_maximum_value)

        # return if not successful
        if not status:
            return

        self.idf_list_store.clear()
        for file_a in verified_idf_files:
            if file_a.external_interface:
                this_file = [False, file_a.filename]
            else:
                this_file = [True, file_a.filename]
            if file_a.has_weather_file:
                this_file.append(file_a.weatherfilename)
            else:
                this_file.append(self.missing_weather_file_key)
            self.idf_list_store.append(this_file)

        self.add_log_entry("Completed building idf list")
        self.add_log_entry("Resulting file list has %s entries; During verification:" % len(verified_idf_files))
        self.add_log_entry(
            "\t there were %s files listed in the csv database that were missing in verification folder(s), and" % len(
                idf_files_missing_in_folder))
        self.add_log_entry(
            "\t there were %s files found in the verification folder(s) that were missing from csv datafile" % len(
                idf_files_missing_from_csv_file))
        self.idf_files_have_been_built = True

    def build_callback_print(self, msg):
        # no need to invoke g-object on this since the builder isn't on a separate thread
        self.status_bar.push(self.status_bar_context_id, msg)
        self.add_log_entry(msg)

    def build_callback_init(self, approx_num_progress_increments):
        self.current_progress_value = 0.0
        self.progress_maximum_value = float(approx_num_progress_increments)
        self.progress.set_fraction(0.0)

    def build_callback_increment(self):
        self.current_progress_value += 1.0
        self.progress.set_fraction(self.current_progress_value / self.progress_maximum_value)

    def idf_selection_all(self, widget, calltype):
        if not self.idf_files_have_been_built:
            self.warning_not_yet_built()
            return
        selection = False
        if calltype == "select":
            selection = True
        for this_file in self.idf_list_store:
            this_file[0] = selection
        self.update_status_with_num_selected()

    def idf_selection_random(self, widget, calltype):
        if not self.idf_files_have_been_built:
            self.warning_not_yet_built()
            return
        # clear them all first; eventually this could be changed to just randomly "down-select" already checked items
        for this_file in self.idf_list_store:
            this_file[0] = False
        number_to_select = int(self.file_list_num_files.get_value())
        number_of_idf_files = len(self.idf_list_store)
        if len(self.idf_list_store) <= number_to_select:  # just take all of them
            pass
        else:  # down select randomly
            indices_to_take = random.sample(range(number_of_idf_files), number_to_select)
            for i in indices_to_take:
                self.idf_list_store[i][0] = True
        self.update_status_with_num_selected()

    def idf_selection_dir(self, widget):
        if not self.idf_files_have_been_built:
            self.warning_not_yet_built()
            return
        self.add_log_entry("User is entering idfs for selection using a folder of idfs")
        dialog = Gtk.FileChooserDialog(
            title="Select folder",
            buttons=(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_OPEN, Gtk.ResponseType.OK)
        )
        dialog.set_action(Gtk.FileChooserAction.SELECT_FOLDER)
        dialog.set_select_multiple(False)
        if self.last_folder_path:
            dialog.set_current_folder(self.last_folder_path)
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            self.last_folder_path = dialog.get_filename()
        dialog.destroy()
        paths_in_dir = glob.glob(os.path.join(self.last_folder_path, "*.idf"))
        files_to_select = []
        for this_path in paths_in_dir:
            filename = os.path.basename(this_path)
            file_no_ext = os.path.splitext(filename)[0]
            files_to_select.append(file_no_ext)
        # do a diagnostic check
        files_entered_not_available = []
        file_names_in_list_store = [x[1] for x in self.idf_list_store]
        for this_file in files_to_select:
            if this_file not in file_names_in_list_store:
                files_entered_not_available.append(this_file)
        if len(files_entered_not_available) > 0:
            text = ""
            num = 0
            for this_file in files_entered_not_available:
                num += 1
                text += "\t%s\n" % this_file
                if num == 3:
                    break
            num_missing = len(files_entered_not_available)
            if num_missing == 1:
                word = "was"
            else:
                word = "were"
            if num_missing <= 3:
                self.warning_dialog(
                    "%s files typed in %s not available for selection, listed here:\n%s" % (num_missing, word, text),
                    False)
            else:
                self.warning_dialog("%s files typed in %s not available for selection, the first 3 listed here:\n%s" % (
                    num_missing, word, text), False)
            self.add_log_entry("Warning: %s files typed in %s not available for selection" % (num_missing, word))
        # deselect them all first
        for this_file in self.idf_list_store:
            if this_file[1] in files_to_select:
                this_file[0] = True
            else:
                this_file[0] = False
        self.update_status_with_num_selected()

    def idf_selection_list(self, widget):
        if not self.idf_files_have_been_built:
            self.warning_not_yet_built()
            return
        self.add_log_entry("User is entering idf files for selection using dialog")
        dialog = Gtk.MessageDialog(
            self, Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT, Gtk.MessageType.QUESTION,
            Gtk.ButtonsType.OK_CANCEL, None
        )
        dialog.set_title("Enter list of files to select")
        dialog.set_markup('Enter file names to select, one per line\nFile extensions are optional')
        scrolled_window = Gtk.ScrolledWindow()
        scrolled_window.set_size_request(400, 400)
        scrolled_window.set_shadow_type(Gtk.ShadowType.ETCHED_IN)
        scrolled_window.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        this_entry = Gtk.TextView()
        scrolled_window.add(this_entry)
        dialog.vbox.pack_end(scrolled_window, True, True, 0)
        dialog.show_all()
        result = dialog.run()
        my_buffer = this_entry.get_buffer()
        text = my_buffer.get_text(my_buffer.get_start_iter(), my_buffer.get_end_iter(), False)
        dialog.destroy()
        if result != Gtk.ResponseType.OK:
            return
        if text.strip() == "":
            self.warning_dialog("Appears a blank entry was entered, no action taken")
        files_to_select = []
        for line in text.split('\n'):
            this_line = line.strip()
            if this_line == "":
                continue
            if line[-4:] == ".imf" or line[-4:] == ".idf":
                this_line = this_line[:-4]
            files_to_select.append(this_line)
        # do a diagnostic check
        files_entered_not_available = []
        file_names_in_list_store = [x[1] for x in self.idf_list_store]
        for this_file in files_to_select:
            if this_file not in file_names_in_list_store:
                files_entered_not_available.append(this_file)
        if len(files_entered_not_available) > 0:
            text = ""
            num = 0
            for this_file in files_entered_not_available:
                num += 1
                text += "\t%s\n" % this_file
                if num == 3:
                    break
            num_missing = len(files_entered_not_available)
            if num_missing == 1:
                word = "was"
            else:
                word = "were"
            if num_missing <= 3:
                self.warning_dialog(
                    "%s files typed in %s not available for selection, listed here:\n%s" % (num_missing, word, text),
                    False)
            else:
                self.warning_dialog("%s files typed in %s not available for selection, the first 3 listed here:\n%s" % (
                    num_missing, word, text), False)
            self.add_log_entry("Warning: %s files typed in %s not available for selection" % (num_missing, word))
        # deselect them all first
        for this_file in self.idf_list_store:
            if this_file[1] in files_to_select:
                this_file[0] = True
            else:
                this_file[0] = False
        self.update_status_with_num_selected()

    def file_list_handler_toggle_listview(self, widget, this_path, list_store):
        list_store[this_path][0] = not list_store[this_path][0]
        self.update_status_with_num_selected()

    def update_status_with_num_selected(self):
        num_selected = 0
        for this_file in self.idf_list_store:
            if this_file[0]:
                num_selected += 1
        self.status_bar.push(self.status_bar_context_id, "%i IDFs selected now" % num_selected)

    # Test Suite workers and GUI handlers

    def init_suite_args(self):

        self.do_runtime_report = True
        if platform == "windows":
            self.runtime_report_file = "C:\\temp\\runtimes.csv"
        else:
            self.runtime_report_file = "/tmp/run_times.csv"

        if platform == "windows":
            suiteargs_base = SingleCaseInformation(source_directory="C:\\ResearchProjects\\EnergyPlus\\Repo1",
                                                   build_directory="C:\\ResearchProjects\\EnergyPlus\\Repo1\\Build",
                                                   run_this_directory=True)
        else:
            suiteargs_base = SingleCaseInformation(source_directory="/home/user/EnergyPlus/repo1/",
                                                   build_directory="/home/user/EnergyPlus/repo1/build/",
                                                   run_this_directory=True)

        if platform == "windows":
            suiteargs_mod = SingleCaseInformation(source_directory="C:\\ResearchProjects\\EnergyPlus\\Repo2",
                                                  build_directory="C:\\ResearchProjects\\EnergyPlus\\Repo2\\Build",
                                                  run_this_directory=True)
        else:
            suiteargs_mod = SingleCaseInformation(source_directory="/home/user/EnergyPlus/repo2/",
                                                  build_directory="/home/user/EnergyPlus/repo2/build/",
                                                  run_this_directory=True)

        # Build the run configuration and the number of threads; using 1 for
        #  windows causes the runtests script to not even use the multi-thread libraries
        num_threads_to_run = 1
        if platform == "windows":
            num_threads_to_run = 1
        else:
            num_threads_to_run = 4
        self.suiteargs = TestRunConfiguration(run_mathdiff=True,
                                              do_composite_err=True,
                                              force_run_type=ForceRunType.NONE,  # ANNUAL, DD, NONE
                                              single_test_run=False,
                                              num_threads=num_threads_to_run,
                                              report_freq=ReportingFreq.HOURLY,
                                              build_a=suiteargs_base,
                                              build_b=suiteargs_mod)

    def run_button(self, widget):

        if self.test_suite_is_running:
            self.runner.id_like_to_stop_now = True
            self.btn_run_suite.set_label("Cancelling...")
            self.add_log_entry("Attempting to cancel test suite...")
            return

        if not self.idf_files_have_been_built:
            self.warning_not_yet_built()
            return

        verified = self.suite_option_handler_suite_validate(None)
        if not verified:
            self.warning_dialog("Pre-run verification step failed, verify files exist and re-try")
            return

        # Now create a file list to pass in
        these_entries = []
        for this_file in self.idf_list_store:
            if this_file[IDFListViewColumnIndex.RUN]:  # if it is checked
                if self.missing_weather_file_key not in this_file[IDFListViewColumnIndex.EPW]:
                    these_entries.append(
                        TestEntry(this_file[IDFListViewColumnIndex.IDF], this_file[IDFListViewColumnIndex.EPW])
                    )
                else:
                    these_entries.append(
                        TestEntry(this_file[IDFListViewColumnIndex.IDF], None)
                    )

        if len(these_entries) == 0:
            self.warning_dialog("Attempted to run a test suite with no files selected")
            return

        # set up the test suite
        self.runner = TestSuiteRunner(self.suiteargs, these_entries)
        self.runner.add_callbacks(print_callback=self.print_callback,
                                  simstarting_callback=self.sim_starting_callback,
                                  casecompleted_callback=self.case_completed_callback,
                                  simulationscomplete_callback=self.simulations_complete_callback,
                                  enderrcompleted_callback=self.end_err_completed_callback,
                                  diffcompleted_callback=self.diff_completed_callback,
                                  alldone_callback=self.all_done_callback,
                                  cancel_callback=self.cancel_callback)

        # create a background thread to do it
        self.work_thread = threading.Thread(target=self.runner.run_test_suite)

        # make it a daemon so it dies with the main window
        self.work_thread.setDaemon(True)

        # Run it
        self.work_thread.start()

        # Update the button
        self.btn_run_suite.set_label("Cancel Suite")
        self.test_suite_is_running = True

    def suite_option_handler_base_build_dir(self, widget):
        dialog = Gtk.FileChooserDialog(
            title="Select build folder",
            buttons=(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_OPEN, Gtk.ResponseType.OK)
        )
        dialog.set_action(Gtk.FileChooserAction.SELECT_FOLDER)
        dialog.set_select_multiple(False)
        if self.last_folder_path:
            dialog.set_current_folder(self.last_folder_path)
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            self.last_folder_path = dialog.get_filename()
            self.suiteargs.buildA.build_directory = self.last_folder_path
            self.case_1_build_dir_label.set_text(self.last_folder_path)
        dialog.destroy()

    def suite_option_handler_mod_build_dir(self, widget):
        dialog = Gtk.FileChooserDialog(
            title="Select build folder",
            buttons=(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_OPEN, Gtk.ResponseType.OK)
        )
        dialog.set_action(Gtk.FileChooserAction.SELECT_FOLDER)
        dialog.set_select_multiple(False)
        if self.last_folder_path:
            dialog.set_current_folder(self.last_folder_path)
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            self.last_folder_path = dialog.get_filename()
            self.suiteargs.buildB.build_directory = self.last_folder_path
            self.case_2_build_dir_label.set_text(self.last_folder_path)
        dialog.destroy()

    def suite_option_handler_basedir_check(self, widget):
        self.suiteargs.buildA.run = widget.get_active()

    def suite_option_handler_mod_dir_check(self, widget):
        self.suiteargs.buildB.run = widget.get_active()

    def suite_option_handler_force_run_type(self, widget):
        text = widget.get_active_text()
        if text == force_none:
            self.suiteargs.force_run_type = ForceRunType.NONE
        elif text == force_dd:
            self.suiteargs.force_run_type = ForceRunType.DD
        elif text == force_annual:
            self.suiteargs.force_run_type = ForceRunType.ANNUAL
        else:
            # error
            widget.set_active(0)
        self.gui_update_label_for_run_config()

    def suite_option_handler_report_frequency(self, widget):
        self.suiteargs.report_freq = widget.get_active_text()
        self.gui_update_label_for_run_config()

    def suite_option_handler_num_threads(self, widget):
        self.suiteargs.num_threads = widget.get_value()

    @staticmethod
    def get_row_color(boolean):
        if boolean:
            return None  # Gtk.gdk.Color(127, 255, 0)
        else:
            return "red"  # Gtk.gdk.Color(220, 20, 60)

    def suite_option_handler_runtime_file(self, widget):
        dialog = Gtk.FileChooserDialog(
            title="Select runtime file save name",
            action=Gtk.FileChooserAction.SAVE,
            buttons=(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_OPEN, Gtk.ResponseType.OK)
        )
        dialog.set_select_multiple(False)
        if self.last_folder_path:
            dialog.set_current_folder(self.last_folder_path)
        afilter = Gtk.FileFilter()
        afilter.set_name("CSV Files")
        afilter.add_pattern("*.csv")
        dialog.add_filter(afilter)
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            self.last_folder_path = dialog.get_current_folder()
            self.runtime_report_file = dialog.get_filename()
            self.suite_option_runtime_file_label.set_label(self.runtime_report_file)
            dialog.destroy()
        else:
            dialog.destroy()
            # reset the flag
            return

    def suite_option_handler_runtime_check(self, widget):
        self.do_runtime_report = widget.get_active()

    def suite_option_handler_suite_validate(self, widget):

        self.add_log_entry("Verifying directory structure")

        # check for directory, then executable and IDD, then input files
        self.verify_list_store.clear()

        # Check case 1
        build_dir = self.suiteargs.buildA.build_directory
        exists = os.path.exists(build_dir)
        self.verify_list_store.append(
            ["Case 1 Build Directory Exists? ", build_dir, exists, self.get_row_color(exists)]
        )
        cmake_cache_file = os.path.join(build_dir, 'CMakeCache.txt')
        exists = os.path.exists(cmake_cache_file)
        self.verify_list_store.append(
            ["Case 1 Build CMake Cache? ", cmake_cache_file, exists, self.get_row_color(exists)]
        )
        source_dir = None
        exists = False
        with open(cmake_cache_file, 'r') as f_cache:
            for this_line in f_cache.readlines():
                if 'CMAKE_HOME_DIRECTORY:INTERNAL=' in this_line:
                    tokens = this_line.strip().split('=')
                    source_dir = tokens[1]
                    self.suiteargs.buildA.source_directory = source_dir
                    exists = True  # this is saying the CMakeCache signal line exists, not the source dir
                    break
        self.verify_list_store.append(
            ["Case 1 Cache Source Dir Line? ", 'CMAKE_HOME_DIRECTORY:INTERNAL', exists, self.get_row_color(exists)]
        )
        if not source_dir:
            source_dir = '<not_found_in_cmake_cache>'
        exists = os.path.exists(source_dir)
        self.verify_list_store.append(
            ["Case 1 Source Directory Exists? ", source_dir, exists, self.get_row_color(exists)]
        )
        test_files_dir = os.path.join(self.suiteargs.buildA.source_directory, 'testfiles')
        exists = os.path.exists(test_files_dir)
        self.verify_list_store.append(
            ["Case 1 Test Files Directory Exists? ", test_files_dir, exists, self.get_row_color(exists)]
        )
        data_sets_dir = os.path.join(self.suiteargs.buildA.source_directory, 'datasets')
        exists = os.path.exists(data_sets_dir)
        self.verify_list_store.append(
            ["Case 1 Data Sets Directory Exists? ", data_sets_dir, exists, self.get_row_color(exists)]
        )
        products_dir = os.path.join(self.suiteargs.buildA.build_directory, 'Products')
        exists = os.path.exists(products_dir)
        self.verify_list_store.append(
            ["Case 1 Products Directory Exists? ", products_dir, exists, self.get_row_color(exists)]
        )
        exe_extension = ''
        if platform == 'windows':
            exe_extension = '.exe'
        if platform == 'windows':  # TODO: Edwin Formalize this later
            energy_plus_exe = os.path.join(
                self.suiteargs.buildA.build_directory, 'Products', 'Debug', 'energyplus' + exe_extension
            )
        else:
            energy_plus_exe = os.path.join(
                self.suiteargs.buildA.build_directory, 'Products', 'energyplus' + exe_extension
            )
        exists = os.path.exists(energy_plus_exe)
        self.verify_list_store.append(
            ["Case 1 EnergyPlus Binary Exists? ", energy_plus_exe, exists, self.get_row_color(exists)]
        )
        basement_exe = os.path.join(self.suiteargs.buildA.build_directory, 'Products', 'Basement' + exe_extension)
        exists = os.path.exists(basement_exe)
        self.verify_list_store.append(
            ["Case 1 Basement (Fortran) Binary Exists? ", basement_exe, exists, self.get_row_color(exists)]
        )

        # Check case 2
        build_dir = self.suiteargs.buildB.build_directory
        exists = os.path.exists(build_dir)
        self.verify_list_store.append(
            ["Case 2 Build Directory Exists? ", build_dir, exists, self.get_row_color(exists)]
        )
        cmake_cache_file = os.path.join(build_dir, 'CMakeCache.txt')
        exists = os.path.exists(cmake_cache_file)
        self.verify_list_store.append(
            ["Case 1 Build CMake Cache? ", cmake_cache_file, exists, self.get_row_color(exists)]
        )
        source_dir = None
        exists = False
        with open(cmake_cache_file, 'r') as f_cache:
            for this_line in f_cache.readlines():
                if 'CMAKE_HOME_DIRECTORY:INTERNAL=' in this_line:
                    tokens = this_line.strip().split('=')
                    source_dir = tokens[1]
                    self.suiteargs.buildB.source_directory = source_dir
                    exists = True  # this is saying the CMakeCache signal line exists, not the source dir
                    break
        self.verify_list_store.append(
            ["Case 1 Cache Source Dir Line? ", 'CMAKE_HOME_DIRECTORY:INTERNAL', exists, self.get_row_color(exists)]
        )
        if not source_dir:
            source_dir = '<not_found_in_cmake_cache>'
        exists = os.path.exists(source_dir)
        self.verify_list_store.append(
            ["Case 2 Source Directory Exists? ", source_dir, exists, self.get_row_color(exists)]
        )
        test_files_dir = os.path.join(self.suiteargs.buildB.source_directory, 'testfiles')
        exists = os.path.exists(test_files_dir)
        self.verify_list_store.append(
            ["Case 2 Test Files Directory Exists? ", test_files_dir, exists, self.get_row_color(exists)]
        )
        data_sets_dir = os.path.join(self.suiteargs.buildB.source_directory, 'datasets')
        exists = os.path.exists(data_sets_dir)
        self.verify_list_store.append(
            ["Case 2 Data Sets Directory Exists? ", data_sets_dir, exists, self.get_row_color(exists)]
        )
        products_dir = os.path.join(self.suiteargs.buildB.build_directory, 'Products')
        exists = os.path.exists(products_dir)
        self.verify_list_store.append(
            ["Case 2 Products Directory Exists? ", products_dir, exists, self.get_row_color(exists)]
        )
        exe_extension = ''
        if platform == 'windows':
            exe_extension = '.exe'
        if platform == 'windows':  # TODO: Edwin Formalize this later
            energy_plus_exe = os.path.join(
                self.suiteargs.buildB.build_directory, 'Products', 'Debug', 'energyplus' + exe_extension
            )
        else:
            energy_plus_exe = os.path.join(
                self.suiteargs.buildB.build_directory, 'Products', 'energyplus' + exe_extension
            )
        exists = os.path.exists(energy_plus_exe)
        self.verify_list_store.append(
            ["Case 2 EnergyPlus Binary Exists? ", energy_plus_exe, exists, self.get_row_color(exists)]
        )
        basement_exe = os.path.join(self.suiteargs.buildB.build_directory, 'Products', 'Basement' + exe_extension)
        exists = os.path.exists(basement_exe)
        self.verify_list_store.append(
            ["Case 2 Basement (Fortran) Binary Exists? ", basement_exe, exists, self.get_row_color(exists)]
        )

        if all([item[2] for item in self.verify_list_store]):
            return True
        else:
            return False

    def handle_results_list_copy(self, widget):
        current_list = self.results_lists_to_copy[self.results_list_selected_entry_root_index]
        if current_list is not None:
            string = u""
            for item in current_list:
                string += "%s\n" % item
            clip = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
            clip.set_text(string, -1)
        else:
            pass

    def handle_tree_view_context_menu(self, widget, event):
        # EDWIN: I need to figure out what this was trying to do, we may not need it at all now
        if event.button == 3:
            x = int(event.x)
            y = int(event.y)
            time = event.time
            path_info = self.tree_view.get_path_at_pos(x, y)
            if path_info:
                this_path, col, cellx, celly = path_info
                self.tree_view.grab_focus()
                self.tree_view.set_cursor(this_path, col, 0)
                widget.popup(None, None, None, None, event.button, time)
                self.results_list_selected_entry_root_index = this_path[0]
                self.last_run_context_copy.show()
                self.last_run_context_nocopy.hide()
            else:
                self.last_run_context_copy.hide()
                self.last_run_context_nocopy.show()

    def gui_update_label_for_run_config(self):
        current_config = self.suiteargs.force_run_type
        if current_config == ForceRunType.NONE:
            self.suite_dir_struct_info.set_markup(
                "A 'Tests' directory will be created in each run directory.\n" +
                "  Comparison results will be in run directory 1."
            )
        elif current_config == ForceRunType.DD:
            self.suite_dir_struct_info.set_markup(
                "A 'Tests-DDOnly' directory will be created in each run directory.\n" +
                "  Comparison results will be in run directory 1."
            )
        elif current_config == ForceRunType.ANNUAL:
            self.suite_dir_struct_info.set_markup(
                "A 'Tests-Annual' directory will be created in each run directory.\n" +
                "  Comparison results will be in run directory 1."
            )
        else:
            pass  # gonna go ahead and say this won't happen

    # Callbacks and callback handlers for GUI to interact with background operations

    def print_callback(self, msg):
        result = GObject.idle_add(self.print_callback_handler, msg)  # EDWIN renamed to GObject, verify this

    def print_callback_handler(self, msg):
        self.status_bar.push(self.status_bar_context_id, msg)
        self.add_log_entry(msg)

    def sim_starting_callback(self, number_of_builds, number_of_cases_per_build):
        result = GObject.idle_add(self.sim_starting_callback_handler, number_of_builds, number_of_cases_per_build)

    def sim_starting_callback_handler(self, number_of_builds, number_of_cases_per_build):
        self.current_progress_value = 0.0
        multiplier = 0.0
        # total number of increments is:
        #   number_of_cases_per_build (buildA simulations)
        # + number_of_cases_per_build (buildB simulations)
        # + number_of_cases_per_build (buildA-buildB diffs)
        if self.suiteargs.buildA.run:
            multiplier += 1
        if self.suiteargs.buildB.run:
            multiplier += 1
        if True:  # there will always be a diff step
            multiplier += 1
        self.progress_maximum_value = float(number_of_cases_per_build * multiplier)
        self.progress.set_fraction(0.0)
        self.status_bar.push(self.status_bar_context_id, "Simulations running...")

    def case_completed_callback(self, test_case_completed_instance):
        result = GObject.idle_add(self.case_completed_callback_handler, test_case_completed_instance)

    def case_completed_callback_handler(self, test_case_completed_instance):
        self.current_progress_value += 1.0
        self.progress.set_fraction(self.current_progress_value / self.progress_maximum_value)
        if not test_case_completed_instance.muffle_err_msg:
            if test_case_completed_instance.run_success:
                self.print_callback_handler("Completed %s : %s, Success" % (
                    test_case_completed_instance.run_directory, test_case_completed_instance.case_name))
            else:
                self.print_callback_handler("Completed %s : %s, Failed" % (
                    test_case_completed_instance.run_directory, test_case_completed_instance.case_name))

    def simulations_complete_callback(self):
        result = GObject.idle_add(self.simulations_complete_callback_handler)

    def simulations_complete_callback_handler(self):
        self.status_bar.push(self.status_bar_context_id, "Simulations done; Post-processing...")

    def end_err_completed_callback(self, build_name, case_name):
        result = GObject.idle_add(self.end_err_completed_callback_handler, build_name, case_name)

    def end_err_completed_callback_handler(self, build_name, case_name):
        self.current_progress_value += 1.0
        self.progress.set_fraction(self.current_progress_value / self.progress_maximum_value)

    def diff_completed_callback(self, case_name):
        result = GObject.idle_add(self.diff_completed_callback_handler, case_name)

    def diff_completed_callback_handler(self, case_name):
        self.current_progress_value += 1.0
        self.progress.set_fraction(self.current_progress_value / self.progress_maximum_value)

    def all_done_callback(self, results):
        result = GObject.idle_add(self.all_done_callback_handler, results)

    def all_done_callback_handler(self, results):

        total_num = 0
        total_num_ = []
        total_num_files = []
        total_diff_files = 0
        total_diff_files_ = []
        total_diff_files_files = []
        num_big_diffs = 0
        num_big_diffs_ = []
        num_big_diffs_files = []
        num_small_diffs = 0
        num_small_diffs_ = []
        num_small_diffs_files = []
        num_success = 0
        num_success_ = []
        num_success_files = []
        num_not_success = 0
        num_not_success_ = []
        num_not_success_files = []
        num_success_2 = 0
        num_success_2_ = []
        num_success_2_files = []
        num_not_success_2 = 0
        num_not_success_2_ = []
        num_not_success_2_files = []
        num_table_big_diffs = 0
        num_table_big_diffs_ = []
        num_table_big_diffs_files = []
        num_table_small_diffs = 0
        num_table_small_diffs_ = []
        num_table_small_diffs_files = []
        num_text_diffs = 0
        num_text_diffs_ = []
        num_text_diffs_files = []

        for this_entry in results:
            total_num += 1
            total_num_.append(["%s" % this_entry.basename])
            total_num_files.append(this_entry.basename)
            if this_entry.summary_result.simulation_status_case1 == EndErrSummary.STATUS_SUCCESS:
                num_success += 1
                num_success_.append(["%s" % this_entry.basename])
                num_success_files.append(this_entry.basename)
            else:
                num_not_success += 1
                num_not_success_.append(["%s" % this_entry.basename])
                num_not_success_files.append(this_entry.basename)
            if this_entry.summary_result.simulation_status_case2 == EndErrSummary.STATUS_SUCCESS:
                num_success_2 += 1
                num_success_2_.append(["%s" % this_entry.basename])
                num_success_2_files.append(this_entry.basename)
            else:
                num_not_success_2 += 1
                num_not_success_2_.append(["%s" % this_entry.basename])
                num_not_success_2_files.append(this_entry.basename)
            if this_entry.eso_diffs:
                total_diff_files += 1
                total_diff_files_.append(["%s: eso" % this_entry.basename])
                if this_entry.basename not in total_diff_files_files:
                    total_diff_files_files.append(this_entry.basename)
                if this_entry.eso_diffs.count_of_big_diff > 0:
                    num_big_diffs += 1
                    num_big_diffs_.append(["%s: %s" % (this_entry.basename, "eso")])
                    if this_entry.basename not in num_big_diffs_files:
                        num_big_diffs_files.append(this_entry.basename)
                elif this_entry.eso_diffs.count_of_small_diff > 0:
                    num_small_diffs += 1
                    num_small_diffs_.append(["%s: %s" % (this_entry.basename, "eso")])
                    if this_entry.basename not in num_small_diffs_files:
                        num_small_diffs_files.append(this_entry.basename)
            if this_entry.mtr_diffs:
                total_diff_files += 1
                total_diff_files_.append(["%s: mtr" % this_entry.basename])
                if this_entry.basename not in total_diff_files_files:
                    total_diff_files_files.append(this_entry.basename)
                if this_entry.mtr_diffs.count_of_big_diff > 0:
                    num_big_diffs += 1
                    num_big_diffs_.append(["%s: %s" % (this_entry.basename, "mtr")])
                    if this_entry.basename not in num_big_diffs_files:
                        num_big_diffs_files.append(this_entry.basename)
                elif this_entry.mtr_diffs.count_of_small_diff > 0:
                    num_small_diffs += 1
                    num_small_diffs_.append(["%s: %s" % (this_entry.basename, "mtr")])
                    if this_entry.basename not in num_small_diffs_files:
                        num_small_diffs_files.append(this_entry.basename)
            if this_entry.zsz_diffs:
                total_diff_files += 1
                total_diff_files_.append(["%s: zsz" % this_entry.basename])
                if this_entry.basename not in total_diff_files_files:
                    total_diff_files_files.append(this_entry.basename)
                if this_entry.zsz_diffs.count_of_big_diff > 0:
                    num_big_diffs += 1
                    num_big_diffs_.append(["%s: %s" % (this_entry.basename, "zsz")])
                    if this_entry.basename not in num_big_diffs_files:
                        num_big_diffs_files.append(this_entry.basename)
                elif this_entry.zsz_diffs.count_of_small_diff > 0:
                    num_small_diffs += 1
                    num_small_diffs_.append(["%s: %s" % (this_entry.basename, "zsz")])
                    if this_entry.basename not in num_small_diffs_files:
                        num_small_diffs_files.append(this_entry.basename)
            if this_entry.ssz_diffs:
                total_diff_files += 1
                total_diff_files_.append(["%s: ssz" % this_entry.basename])
                if this_entry.basename not in total_diff_files_files:
                    total_diff_files_files.append(this_entry.basename)
                if this_entry.ssz_diffs.count_of_big_diff > 0:
                    num_big_diffs += 1
                    num_big_diffs_.append(["%s: %s" % (this_entry.basename, "ssz")])
                    if this_entry.basename not in num_big_diffs_files:
                        num_big_diffs_files.append(this_entry.basename)
                elif this_entry.ssz_diffs.count_of_small_diff > 0:
                    num_small_diffs += 1
                    num_small_diffs_.append(["%s: %s" % (this_entry.basename, "ssz")])
                    if this_entry.basename not in num_small_diffs_files:
                        num_small_diffs_files.append(this_entry.basename)
            if this_entry.table_diffs:
                total_diff_files += 1
                total_diff_files_.append(["%s: table" % this_entry.basename])
                if this_entry.basename not in total_diff_files_files:
                    total_diff_files_files.append(this_entry.basename)
                if this_entry.table_diffs.bigdiff_count > 0:
                    num_table_big_diffs += 1
                    num_table_big_diffs_.append(["%s: %s" % (this_entry.basename, "table")])
                    if this_entry.basename not in num_big_diffs_files:
                        num_table_big_diffs_files.append(this_entry.basename)
                elif this_entry.table_diffs.smalldiff_count > 0:
                    num_table_small_diffs += 1
                    num_table_small_diffs_.append(["%s: %s" % (this_entry.basename, "table")])
                    if this_entry.basename not in num_small_diffs_files:
                        num_table_small_diffs_files.append(this_entry.basename)
            if this_entry.aud_diffs:
                total_diff_files += 1
                total_diff_files_.append(["%s: audit" % this_entry.basename])
                if this_entry.aud_diffs.diff_type != TextDifferences.EQUAL:
                    if this_entry.basename not in total_diff_files_files:
                        total_diff_files_files.append(this_entry.basename)
                    num_text_diffs += 1
                    num_text_diffs_.append(["%s: %s" % (this_entry.basename, "audit")])
                    if this_entry.basename not in num_text_diffs_files:
                        num_text_diffs_files.append(this_entry.basename)
            if this_entry.bnd_diffs:
                total_diff_files += 1
                total_diff_files_.append(["%s: bnd" % this_entry.basename])
                if this_entry.bnd_diffs.diff_type != TextDifferences.EQUAL:
                    if this_entry.basename not in total_diff_files_files:
                        total_diff_files_files.append(this_entry.basename)
                    num_text_diffs += 1
                    num_text_diffs_.append(["%s: %s" % (this_entry.basename, "bnd")])
                    if this_entry.basename not in num_text_diffs_files:
                        num_text_diffs_files.append(this_entry.basename)
            if this_entry.dxf_diffs:
                total_diff_files += 1
                total_diff_files_.append(["%s: dxf" % this_entry.basename])
                if this_entry.dxf_diffs.diff_type != TextDifferences.EQUAL:
                    if this_entry.basename not in total_diff_files_files:
                        total_diff_files_files.append(this_entry.basename)
                    num_text_diffs += 1
                    num_text_diffs_.append(["%s: %s" % (this_entry.basename, "dxf")])
                    if this_entry.basename not in num_text_diffs_files:
                        num_text_diffs_files.append(this_entry.basename)
            if this_entry.eio_diffs:
                total_diff_files += 1
                total_diff_files_.append(["%s: eio" % this_entry.basename])
                if this_entry.eio_diffs.diff_type != TextDifferences.EQUAL:
                    if this_entry.basename not in total_diff_files_files:
                        total_diff_files_files.append(this_entry.basename)
                    num_text_diffs += 1
                    num_text_diffs_.append(["%s: %s" % (this_entry.basename, "eio")])
                    if this_entry.basename not in num_text_diffs_files:
                        num_text_diffs_files.append(this_entry.basename)
            if this_entry.mdd_diffs:
                total_diff_files += 1
                total_diff_files_.append(["%s: mdd" % this_entry.basename])
                if this_entry.mdd_diffs.diff_type != TextDifferences.EQUAL:
                    if this_entry.basename not in total_diff_files_files:
                        total_diff_files_files.append(this_entry.basename)
                    num_text_diffs += 1
                    num_text_diffs_.append(["%s: %s" % (this_entry.basename, "mdd")])
                    if this_entry.basename not in num_text_diffs_files:
                        num_text_diffs_files.append(this_entry.basename)
            if this_entry.mtd_diffs:
                total_diff_files += 1
                total_diff_files_.append(["%s: mtd" % this_entry.basename])
                if this_entry.mtd_diffs.diff_type != TextDifferences.EQUAL:
                    if this_entry.basename not in total_diff_files_files:
                        total_diff_files_files.append(this_entry.basename)
                    num_text_diffs += 1
                    num_text_diffs_.append(["%s: %s" % (this_entry.basename, "mtd")])
                    if this_entry.basename not in num_text_diffs_files:
                        num_text_diffs_files.append(this_entry.basename)
            if this_entry.rdd_diffs:
                total_diff_files += 1
                total_diff_files_.append(["%s: rdd" % this_entry.basename])
                if this_entry.rdd_diffs.diff_type != TextDifferences.EQUAL:
                    if this_entry.basename not in total_diff_files_files:
                        total_diff_files_files.append(this_entry.basename)
                    num_text_diffs += 1
                    num_text_diffs_.append(["%s: %s" % (this_entry.basename, "rdd")])
                    if this_entry.basename not in num_text_diffs_files:
                        num_text_diffs_files.append(this_entry.basename)
            if this_entry.shd_diffs:
                total_diff_files += 1
                total_diff_files_.append(["%s: shd" % this_entry.basename])
                if this_entry.shd_diffs.diff_type != TextDifferences.EQUAL:
                    if this_entry.basename not in total_diff_files_files:
                        total_diff_files_files.append(this_entry.basename)
                    num_text_diffs += 1
                    num_text_diffs_.append(["%s: %s" % (this_entry.basename, "shd")])
                    if this_entry.basename not in num_text_diffs_files:
                        num_text_diffs_files.append(this_entry.basename)
            if this_entry.err_diffs:
                total_diff_files += 1
                total_diff_files_.append(["%s: err" % this_entry.basename])
                if this_entry.err_diffs.diff_type != TextDifferences.EQUAL:
                    if this_entry.basename not in total_diff_files_files:
                        total_diff_files_files.append(this_entry.basename)
                    num_text_diffs += 1
                    num_text_diffs_.append(["%s: %s" % (this_entry.basename, "err")])
                    if this_entry.basename not in num_text_diffs_files:
                        num_text_diffs_files.append(this_entry.basename)
            if this_entry.dlin_diffs:
                total_diff_files += 1
                total_diff_files_.append(["%s: delightin" % this_entry.basename])
                if this_entry.dlin_diffs.diff_type != TextDifferences.EQUAL:
                    if this_entry.basename not in total_diff_files_files:
                        total_diff_files_files.append(this_entry.basename)
                    num_text_diffs += 1
                    num_text_diffs_.append(["%s: %s" % (this_entry.basename, "delightin")])
                    if this_entry.basename not in num_text_diffs_files:
                        num_text_diffs_files.append(this_entry.basename)
            if this_entry.dlout_diffs:
                total_diff_files += 1
                total_diff_files_.append(["%s: delightout" % this_entry.basename])
                if this_entry.dlout_diffs.diff_type != TextDifferences.EQUAL:
                    if this_entry.basename not in total_diff_files_files:
                        total_diff_files_files.append(this_entry.basename)
                    num_text_diffs += 1
                    num_text_diffs_.append(["%s: %s" % (this_entry.basename, "delightout")])
                    if this_entry.basename not in num_text_diffs_files:
                        num_text_diffs_files.append(this_entry.basename)

        self.results_lists_to_copy = []

        if self.results_child_num_run:
            self.results_list_store.remove(self.results_child_num_run)
        self.results_child_num_run = self.results_list_store.append(self.results_parent_num_run, [str(total_num)])
        this_path = self.results_list_store.get_path(self.results_parent_num_run)
        self.tree_view.expand_row(this_path, False)
        for result in total_num_:
            self.results_list_store.append(self.results_child_num_run, result)
        self.results_lists_to_copy.append(total_num_files)

        if self.results_child_success:
            self.results_list_store.remove(self.results_child_success)
        self.results_child_success = self.results_list_store.append(self.results_parent_success, [str(num_success)])
        this_path = self.results_list_store.get_path(self.results_parent_success)
        self.tree_view.expand_row(this_path, False)
        for result in num_success_:
            self.results_list_store.append(self.results_child_success, result)
        self.results_lists_to_copy.append(num_success_files)

        if self.results_child_not_success:
            self.results_list_store.remove(self.results_child_not_success)
        self.results_child_not_success = self.results_list_store.append(
            self.results_parent_not_success, [str(num_not_success)]
        )
        this_path = self.results_list_store.get_path(self.results_parent_not_success)
        self.tree_view.expand_row(this_path, False)
        for result in num_not_success_:
            self.results_list_store.append(self.results_child_not_success, result)
        self.results_lists_to_copy.append(num_not_success_files)

        if self.results_child_success_2:
            self.results_list_store.remove(self.results_child_success_2)
        self.results_child_success_2 = self.results_list_store.append(
            self.results_parent_success_2, [str(num_success_2)]
        )
        this_path = self.results_list_store.get_path(self.results_parent_success_2)
        self.tree_view.expand_row(this_path, False)
        for result in num_success_2_:
            self.results_list_store.append(self.results_child_success_2, result)
        self.results_lists_to_copy.append(num_success_2_files)

        if self.results_child_not_success_2:
            self.results_list_store.remove(self.results_child_not_success_2)
        self.results_child_not_success_2 = self.results_list_store.append(self.results_parent_not_success_2,
                                                                          [str(num_not_success_2)])
        this_path = self.results_list_store.get_path(self.results_parent_not_success_2)
        self.tree_view.expand_row(this_path, False)
        for result in num_not_success_2_:
            self.results_list_store.append(self.results_child_not_success_2, result)
        self.results_lists_to_copy.append(num_not_success_2_files)

        if self.results_child_files_compared:
            self.results_list_store.remove(self.results_child_files_compared)
        self.results_child_files_compared = self.results_list_store.append(self.results_parent_files_compared,
                                                                           [str(total_diff_files)])
        this_path = self.results_list_store.get_path(self.results_parent_files_compared)
        self.tree_view.expand_row(this_path, False)
        for result in total_diff_files_:
            self.results_list_store.append(self.results_child_files_compared, result)
        self.results_lists_to_copy.append(total_diff_files_files)

        if self.results_child_big_math:
            self.results_list_store.remove(self.results_child_big_math)
        self.results_child_big_math = self.results_list_store.append(self.results_parent_big_math, [str(num_big_diffs)])
        this_path = self.results_list_store.get_path(self.results_parent_big_math)
        self.tree_view.expand_row(this_path, False)
        for result in num_big_diffs_:
            self.results_list_store.append(self.results_child_big_math, result)
        self.results_lists_to_copy.append(num_big_diffs_files)

        if self.results_child_small_math:
            self.results_list_store.remove(self.results_child_small_math)
        self.results_child_small_math = self.results_list_store.append(
            self.results_parent_small_math, [str(num_small_diffs)]
        )
        this_path = self.results_list_store.get_path(self.results_parent_small_math)
        self.tree_view.expand_row(this_path, False)
        for result in num_small_diffs_:
            self.results_list_store.append(self.results_child_small_math, result)
        self.results_lists_to_copy.append(num_small_diffs_files)

        if self.results_child_big_table:
            self.results_list_store.remove(self.results_child_big_table)
        self.results_child_big_table = self.results_list_store.append(
            self.results_parent_big_table, [str(num_table_big_diffs)]
        )
        this_path = self.results_list_store.get_path(self.results_parent_big_table)
        self.tree_view.expand_row(this_path, False)
        for result in num_table_big_diffs_:
            self.results_list_store.append(self.results_child_big_table, result)
        self.results_lists_to_copy.append(num_table_big_diffs_files)

        if self.results_child_small_table:
            self.results_list_store.remove(self.results_child_small_table)
        self.results_child_small_table = self.results_list_store.append(self.results_parent_small_table,
                                                                        [str(num_table_small_diffs)])
        this_path = self.results_list_store.get_path(self.results_parent_small_table)
        self.tree_view.expand_row(this_path, False)
        for result in num_table_small_diffs_:
            self.results_list_store.append(self.results_child_small_table, result)
        self.results_lists_to_copy.append(num_table_small_diffs_files)

        if self.results_child_textual:
            self.results_list_store.remove(self.results_child_textual)
        self.results_child_textual = self.results_list_store.append(self.results_parent_textual, [str(num_text_diffs)])
        this_path = self.results_list_store.get_path(self.results_parent_textual)
        self.tree_view.expand_row(this_path, False)
        for result in num_text_diffs_:
            self.results_list_store.append(self.results_child_textual, result)
        self.results_lists_to_copy.append(num_text_diffs_files)

        if self.do_runtime_report:
            try:
                import csv
                with open(self.runtime_report_file, "w") as csvfile:
                    writer = csv.writer(csvfile)
                    writer.writerow(["Case", "Runtime [s]", "Runtime [s]"])
                    for this_entry in results:
                        runtime1 = -1
                        runtime2 = -1
                        if this_entry.summary_result:
                            this_summary = this_entry.summary_result
                            if this_summary.simulation_status_case1 == EndErrSummary.STATUS_SUCCESS:
                                runtime1 = this_summary.run_time_seconds_case1
                            if this_summary.simulation_status_case2 == EndErrSummary.STATUS_SUCCESS:
                                runtime2 = this_summary.run_time_seconds_case2
                        writer.writerow([this_entry.basename, runtime1, runtime2])
            except Exception as this_exception:
                self.add_log_entry("Couldn't write runtime report file")
                print(this_exception)

        # update the GUI
        self.btn_run_suite.set_label("Run Suite")
        self.test_suite_is_running = False
        self.status_bar.push(self.status_bar_context_id, "ALL DONE")
        self.progress.set_fraction(1.0)

    def cancel_callback(self):
        GObject.idle_add(self.cancel_callback_handler)

    def cancel_callback_handler(self):
        self.btn_run_suite.set_label("Run Suite")
        self.test_suite_is_running = False
        self.status_bar.push(self.status_bar_context_id, "Cancelled")
        self.progress.set_fraction(1.0)
        self.add_log_entry("Test suite cancel complete")
