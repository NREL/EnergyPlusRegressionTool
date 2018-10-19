#!/usr/bin/env python

# this GUI uses PyGtk
# this is available in Python 3 as PyGObject, or gi
# the steps for getting it installed on your system are available here:
#  https://pygobject.readthedocs.io/en/latest/getting_started.html
# I use virtual environments, so I needed a little extra help
# those instructions are *also* provided by them and worked flawlessly
#  https://pygobject.readthedocs.io/en/latest/devguide/dev_environ.html#devenv

import datetime  # datetime allows us to generate timestamps for the log
import subprocess  # subprocess allows us to spawn the help pdf separately
import threading  # threading allows for the test suite to run multiple E+ runs concurrently
from datetime import datetime  # get datetime to do date/time calculations for timestamps, etc.
# TODO: Remove XML - use JSON
from xml.dom import minidom
# we use xml for the save file
from xml.etree import ElementTree
from xml.etree.ElementTree import Element, parse

# graphics stuff
import gi
from gi.repository import Gtk, GObject

# import the supporting python modules for this script
from epregressions.build_files_to_run import *
from epregressions.runtests import *

python_version = float("%s.%s" % (sys.version_info.major, sys.version_info.minor))
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
force_annual = "Force annual runperiod simulations"
gi.require_version("Gtk", "3.0")


class IDFListViewColumnIndex:
    RUN = 0
    IDF = 1
    EPW = 2
    EXTERNAL_INTERFACE = 3
    GROUND_HT = 4
    DATA_SET = 5
    PARAMETRIC = 6
    MACRO = 7
    DELIGHT = 8


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
        self.suite_option_handler_basecheckbutton = None
        self.suite_option_baseexe = None
        self.suite_option_handler_modcheckbutton = None
        self.suite_option_modexe = None
        self.suite_option_numthreads = None
        self.runtypecombobox = None
        self.reportfreqcombobox = None
        self.suite_dir_struc_info = None
        self.suite_option_eplusinstall_label = None
        self.suite_option_handler_runtimereportcheck = None
        self.suite_option_runtime_file_label = None
        self.btn_run_suite = None
        self.verifyliststore = None
        self.verifytreeView = None
        self.resultsliststore = None
        self.resultsparent_numrun = None
        self.resultsparent_success = None
        self.resultsparent_unsuccess = None
        self.resultsparent_success2 = None
        self.resultsparent_unsuccess2 = None
        self.resultsparent_filescompared = None
        self.resultsparent_bigmath = None
        self.resultsparent_smallmath = None
        self.resultsparent_bigtable = None
        self.resultsparent_smalltable = None
        self.resultsparent_textual = None
        self.resultschild_numrun = None
        self.resultschild_success = None
        self.resultschild_unsuccess = None
        self.resultschild_success2 = None
        self.resultschild_unsuccess2 = None
        self.resultschild_filescompared = None
        self.resultschild_bigmath = None
        self.resultschild_smallmath = None
        self.resultschild_bigtable = None
        self.resultschild_smalltable = None
        self.resultschild_textual = None
        self.tree_view = None
        self.tree_selection = None
        self.last_run_heading = None
        self.log_scroller_notebook_page = None
        self.logstore = None
        self.notebook = None
        self.progress = None
        self.status_bar = None
        self.status_bar_context_id = None
        self.lastrun_context = None
        self.lastrun_context_copy = None
        self.lastrun_context_nocopy = None
        self.file_list_builder_configuration = None
        self.current_progress_value = None
        self.progress_maximum_value = None
        self.do_runtime_report = None  # EDWIN: Always do runtime report and formalize this
        self.runtime_report_file = None
        self.suiteargs = None
        self.runner = None
        self.work_thread = None
        self.resultslist_selected_entry_root_index = None
        self.results_lists_to_copy = None

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

    def go_away(self, what_else_goes_in_gtk_main_quit):
        try:
            self.save_settings(None)
        except Exception as exc:
            print(exc)
        Gtk.main_quit()

    def gui_build(self):
        # put the window in the center of the (primary? current?) screen
        self.set_position(Gtk.WindowPosition.CENTER)

        # make a nice border around the outside of the window
        self.set_border_width(10)

        # set the window title
        self.set_title("EnergyPlus Test Suite")

        # set the window icon
        self.set_icon_from_file(os.path.join(script_dir, 'ep_icon.png'))

        # build pre-GUI stuff here (context menus that will be referenced by GUI objects, for example)
        self.build_pre_gui_stuff()

        # create a v-box to start laying out the geometry of the form
        vbox = Gtk.VBox(False, box_spacing)

        # add the menu to the v-box
        vbox.pack_start(self.gui_build_menu_bar(), False, False, padding=0)

        # add the notebook to the v-box
        vbox.pack_start(self.gui_build_notebook(), True, True, padding=0)

        # and finally add the status section at the bottom
        vbox.pack_end(self.gui_build_messaging(), False, False, padding=0)

        # now add the entire v-box to the main form
        self.add(vbox)

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
        filemenu = Gtk.Menu()
        filemenu.append(menu_item_file_load)
        filemenu.append(menu_item_file_save)
        filemenu.append(Gtk.SeparatorMenuItem())
        filemenu.append(menu_item_file_exit)
        menu_item_file.set_submenu(filemenu)

        # attach the FILE menu to the main menu bar
        mb.append(menu_item_file)

        menu_item_help_pdf = Gtk.MenuItem("Show PDF Help File")
        menu_item_help_pdf.connect("activate", self.show_help_pdf)
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
            sure_dialog = Gtk.MessageDialog(self, flags=0, type=Gtk.MESSAGE_QUESTION, buttons=Gtk.BUTTONS_YES_NO,
                                            message_format="Are you sure you want to load a new configuration?")
            response = sure_dialog.run()
            sure_dialog.destroy()
            if response == Gtk.RESPONSE_NO:
                return
            dialog = Gtk.FileChooserDialog(title="Select settings file", buttons=(
                Gtk.STOCK_CANCEL, Gtk.RESPONSE_CANCEL, Gtk.STOCK_OPEN, Gtk.RESPONSE_OK))
            dialog.set_select_multiple(False)
            if self.last_folder_path:
                dialog.set_current_folder(self.last_folder_path)
            a_filter = Gtk.FileFilter()
            a_filter.set_name("EPT Files")
            a_filter.add_pattern("*.ept")
            dialog.add_filter(a_filter)
            response = dialog.run()
            if response == Gtk.RESPONSE_OK:
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

        project_tree = parse(settings_file)
        project_root = project_tree.getroot()

        # set up some nice shorthands
        get = project_root.find
        gets = project_root.findall

        masterfile = get("idfselection/masterfile")
        if masterfile is not None:
            if os.path.exists(str(masterfile)):
                self.file_list_builder_configuration.master_data_file = masterfile.attrib["filepath"]
        for idf_entry in self.idf_list_store:
            idf_entry[IDFListViewColumnIndex.RUN] = False
        idfs_selected = gets("idfselection/selectedfiles/selectedfile")
        if idfs_selected is not None:
            for idfelement in idfs_selected:
                filename = idfelement.attrib["filename"]
                for idf_entry in self.idf_list_store:
                    if idf_entry[IDFListViewColumnIndex.IDF] == filename:  # if it matches
                        idf_entry[IDFListViewColumnIndex.RUN] = True
        random_int = get("idfselection/randomnumber")
        if random_int is not None:
            self.file_list_num_files.set_value(int(random_int.attrib["value"]))
        case_a_stuff = get("suiteoptions/casea")
        if case_a_stuff is not None:
            self.suiteargs.buildA.build = case_a_stuff.attrib["dirpath"]
            test = case_a_stuff.attrib["selected"]
            if test == "True":
                self.suiteargs.buildA.run = True
            else:
                self.suiteargs.buildA.run = False
            self.suiteargs.buildA.executable = case_a_stuff.attrib["executable"]
        case_b_stuff = get("suiteoptions/caseb")
        if case_b_stuff is not None:
            self.suiteargs.buildB.build = case_b_stuff.attrib["dirpath"]
            test = case_b_stuff.attrib["selected"]
            if test == "True":
                self.suiteargs.buildB.run = True
            else:
                self.suiteargs.buildB.run = False
            self.suiteargs.buildB.executable = case_b_stuff.attrib["executable"]
        installdir = get("suiteoptions/epinstalldir")
        if installdir is not None:
            self.suiteargs.eplus_install = installdir.attrib["dirpath"]
        runconfig_elem = get("suiteoptions/runconfig")
        if runconfig_elem is not None:
            runconfig_option = runconfig_elem.attrib["value"]
            if runconfig_option == "NONE":
                self.suiteargs.force_run_type = ForceRunType.NONE
            elif runconfig_option == "DDONLY":
                self.suiteargs.force_run_type = ForceRunType.DD
            elif runconfig_option == "ANNUAL":
                self.suiteargs.force_run_type = ForceRunType.ANNUAL
        report_freq_elem = get("suiteoptions/reportfreq")
        if report_freq_elem is not None:
            report_freq_option = report_freq_elem.attrib["value"]
            self.suiteargs.report_freq = report_freq_option
        numthreads_elem = get("suiteoptions/otheroptions/numthreads")
        if numthreads_elem is not None:
            self.suiteargs.num_threads = numthreads_elem.attrib["value"]
        if from_menu:
            self.gui_fill_with_data()

    def gui_fill_with_data(self):
        self.suite_option_handler_basecheckbutton.set_active(self.suiteargs.buildA.run)
        if self.suiteargs.buildA.build:
            self.suite_option_handler_basecheckbutton.set_label(self.suiteargs.buildA.build)
        if self.suiteargs.buildA.executable:
            self.suite_option_baseexe.set_text(self.suiteargs.buildA.executable)
        self.suite_option_handler_modcheckbutton.set_active(self.suiteargs.buildB.run)
        if self.suiteargs.buildB.build:
            self.suite_option_handler_modcheckbutton.set_label(self.suiteargs.buildB.build)
        if self.suiteargs.buildB.executable:
            self.suite_option_modexe.set_text(self.suiteargs.buildB.executable)
        # num threads here
        if self.suiteargs.force_run_type:
            if self.suiteargs.force_run_type == ForceRunType.NONE:
                self.runtypecombobox.set_active(0)
            elif self.suiteargs.force_run_type == ForceRunType.DD:
                self.runtypecombobox.set_active(1)
            elif self.suiteargs.force_run_type == ForceRunType.ANNUAL:
                self.runtypecombobox.set_active(2)
            elif self.suiteargs.force_run_type == ForceRunType.REVERSEDD:
                self.runtypecombobox.set_active(3)
        if self.suiteargs.report_freq:
            if self.suiteargs.report_freq == ReportingFreq.DETAILED:
                self.reportfreqcombobox.set_active(0)
            elif self.suiteargs.report_freq == ReportingFreq.TIMESTEP:
                self.reportfreqcombobox.set_active(1)
            elif self.suiteargs.report_freq == ReportingFreq.HOURLY:
                self.reportfreqcombobox.set_active(2)
            elif self.suiteargs.report_freq == ReportingFreq.DAILY:
                self.reportfreqcombobox.set_active(3)
            elif self.suiteargs.report_freq == ReportingFreq.MONTHLY:
                self.reportfreqcombobox.set_active(4)
            elif self.suiteargs.report_freq == ReportingFreq.RUNPERIOD:
                self.reportfreqcombobox.set_active(5)
            elif self.suiteargs.report_freq == ReportingFreq.ENVIRONMENT:
                self.reportfreqcombobox.set_active(6)
            elif self.suiteargs.report_freq == ReportingFreq.ANNUAL:
                self.reportfreqcombobox.set_active(7)
        if self.suiteargs.eplus_install:
            self.suite_option_eplusinstall_label.set_label(self.suiteargs.eplus_install)

    def prettify(self, elem):
        """Return a pretty-printed XML string for the Element."""
        rough_string = ElementTree.tostring(elem, 'utf-8')
        re_parsed = minidom.parseString(rough_string)
        return re_parsed.toprettyxml(indent="  ")

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
                title="Select settings file save name", action=Gtk.FILE_CHOOSER_ACTION_SAVE,
                buttons=(Gtk.STOCK_CANCEL, Gtk.RESPONSE_CANCEL, Gtk.STOCK_OPEN, Gtk.RESPONSE_OK)
            )
            dialog.set_select_multiple(False)
            if self.last_folder_path:
                dialog.set_current_folder(self.last_folder_path)
            a_filter = Gtk.FileFilter()
            a_filter.set_name("EPT Files")
            a_filter.add_pattern("*.ept")
            dialog.add_filter(a_filter)
            response = dialog.run()
            if response == Gtk.RESPONSE_OK:
                self.last_folder_path = dialog.get_current_folder()
                save_file = dialog.get_filename()
                dialog.destroy()
            else:
                dialog.destroy()
                # reset the flag
                self.currently_saving = False
                return

        project = Element("project")
        # idf_selection = SubElement(project, "idfselection")
        # idf_selection_db = SubElement(idf_selection, "masterfile",
        #                               filepath=self.file_list_builder_configuration.master_data_file)
        # idf_selected_list = SubElement(idf_selection, "selectedfiles")
        # if self.idf_files_have_been_built:
        #     for idf_entry in self.idfliststore:
        #         if idf_entry[IDFListViewColumnIndex.RUN]:  # if it is checked
        #             this_entry = SubElement(idf_selected_list, "selectedfile",
        #                                     filename=idf_entry[IDFListViewColumnIndex.IDF])
        # random_integer = SubElement(idf_selection, "random number",
        # value=str(int(self.file_list_num_files.get_value())))

        # suite_options = SubElement(project, "suite_options")
        # case_a = SubElement(suite_options, "case_a", dirpath=self.suiteargs.buildA.build,
        #                    selected=str(self.suiteargs.buildA.run), executable=self.suiteargs.buildA.executable)
        # case_b = SubElement(suite_options, "case_b", dirpath=self.suiteargs.buildB.build,
        #                    selected=str(self.suiteargs.buildB.run), executable=self.suiteargs.buildB.executable)
        # install_dir = SubElement(suite_options, "ep_install_dir", dirpath=self.suiteargs.eplus_install)
        # s_value = ""
        # if self.suiteargs.force_run_type == ForceRunType.NONE:
        #     s_value = "NONE"
        # elif self.suiteargs.force_run_type == ForceRunType.DD:
        #     s_value = "DD_ONLY"
        # elif self.suiteargs.force_run_type == ForceRunType.ANNUAL:
        #     s_value = "ANNUAL"
        # run_config = SubElement(suite_options, "run_config", value=s_value)
        # report_freq = SubElement(suite_options, "report_freq", value=self.suiteargs.report_freq)
        # other_options = SubElement(suite_options, "other_options")
        # num_threads = SubElement(other_options, "num_threads", value=str(int(self.suiteargs.num_threads)))

        save_text = self.prettify(project)
        with open(save_file, 'w') as f:
            f.write(save_text)

        # reset the flag
        self.currently_saving = False

        # since this is included in auto-save, return True to the timeout_add function
        # for normal (manual) saving, this will return to nothingness most likely
        return True

    def add_idf_selection_row(self, button_text, callback, rownum):
        label = Gtk.Label(button_text)
        label.set_justify(Gtk.Justification.RIGHT)
        alignment = Gtk.Alignment(xalign=1.0)
        alignment.add(label)
        self.idf_selection_table.attach(
            alignment, 0, 1, rownum - 1, rownum, Gtk.AttachOptions.FILL, Gtk.AttachOptions.EXPAND, 4, 4
        )
        button = Gtk.Button("Select")
        button.connect("clicked", callback, "select")
        self.idf_selection_table.attach(
            button, 1, 2, rownum - 1, rownum, Gtk.AttachOptions.FILL, Gtk.AttachOptions.EXPAND, 4, 4
        )
        button = Gtk.Button("Deselect")
        button.connect("clicked", callback, "deselect")
        self.idf_selection_table.attach(
            button, 2, 3, rownum - 1, rownum, Gtk.AttachOptions.FILL, Gtk.AttachOptions.EXPAND, 4, 4
        )

    def gui_build_notebook_page_idf_selection(self):

        # PAGE 1: FILE LIST OPTIONS, base layout is the idf_selection HPanel
        notebook_page_idf_selection = Gtk.HPaned()

        # idf_list is a v-box holding the verification, master file path, build command button, and idf list
        notebook_page_idf_list = Gtk.VBox(False, box_spacing)

        button1 = Gtk.Button("Rebuild Master File List")
        button1.connect("clicked", self.build_button)
        alignment = Gtk.Alignment(xalign=0.5, yalign=0.0, xscale=0.0, yscale=0.0)
        alignment.add(button1)
        notebook_page_idf_list.pack_start(alignment, False, False, box_spacing)

        # add a separator for nicety
        notebook_page_idf_list.pack_start(Gtk.HSeparator(), False, True, 0)

        # PAGE: IDF LIST RESULTS
        listview_window = Gtk.ScrolledWindow()
        listview_window.set_size_request(550, -1)
        listview_window.set_shadow_type(Gtk.ShadowType.ETCHED_IN)
        listview_window.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        # make the list store and the tree view

        self.idf_list_store = Gtk.ListStore(bool, str, str, str, str, str, str, str, str)
        self.idf_list_store.append([False, "-- Re-build idf list --", "-- to see results --", "", "", "", "", "", ""])
        tree_view = Gtk.TreeView(self.idf_list_store)
        tree_view.set_rules_hint(True)
        # make the columns for the treeview; could add more columns including a checkbox
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
        # column: External Interface name
        renderer_text = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn("ExtInterface?", renderer_text, text=IDFListViewColumnIndex.EXTERNAL_INTERFACE)
        column.set_sort_column_id(3)
        column.set_resizable(True)
        tree_view.append_column(column)
        # column: GroundHT name
        renderer_text = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn("GroundHT?", renderer_text, text=IDFListViewColumnIndex.GROUND_HT)
        column.set_sort_column_id(4)
        column.set_resizable(True)
        tree_view.append_column(column)
        # column: Data set name name
        renderer_text = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn("ExtDataset?", renderer_text, text=IDFListViewColumnIndex.DATA_SET)
        column.set_sort_column_id(5)
        column.set_resizable(True)
        tree_view.append_column(column)
        # column: Parametric name
        renderer_text = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn("Parametrics", renderer_text, text=IDFListViewColumnIndex.PARAMETRIC)
        column.set_sort_column_id(6)
        column.set_resizable(True)
        tree_view.append_column(column)
        # column: Macro name
        renderer_text = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn("MacroDefns", renderer_text, text=IDFListViewColumnIndex.MACRO)
        column.set_sort_column_id(7)
        column.set_resizable(True)
        tree_view.append_column(column)
        # column: Delight name
        renderer_text = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn("DeLight", renderer_text, text=IDFListViewColumnIndex.DELIGHT)
        column.set_sort_column_id(8)
        column.set_resizable(True)
        tree_view.append_column(column)

        listview_window.add(tree_view)
        aligner = Gtk.Alignment(xalign=0, yalign=0, xscale=1, yscale=1)
        aligner.add(listview_window)
        notebook_page_idf_list.pack_start(aligner, True, True, padding=0)

        # the second side of the page is the table of buttons for selection options
        self.idf_selection_table = Gtk.Table(9, 3, True)
        self.idf_selection_table.set_row_spacings(box_spacing)
        self.idf_selection_table.set_col_spacings(box_spacing)

        label = Gtk.Label("")
        label.set_markup("<b>These options will only switch the matching entries</b>")
        label.set_justify(Gtk.Justification.CENTER)
        alignment = Gtk.Alignment(xalign=0.5, yalign=1.0)
        alignment.add(label)
        self.idf_selection_table.attach(alignment, 0, 3, 0, 1)

        this_row_num = 2
        self.add_idf_selection_row("ALL:", self.idf_selection_all, rownum=this_row_num)
        this_row_num += 1
        self.add_idf_selection_row("ExternalInterface:", self.idf_selection_extint, rownum=this_row_num)
        this_row_num += 1
        self.add_idf_selection_row("GroundHT:", self.idf_selection_groundht, rownum=this_row_num)
        this_row_num += 1
        self.add_idf_selection_row("ExtDataSet:", self.idf_selection_dataset, rownum=this_row_num)
        this_row_num += 1
        self.add_idf_selection_row("DeLight:", self.idf_selection_delight, rownum=this_row_num)
        this_row_num += 1
        self.add_idf_selection_row("Macro:", self.idf_selection_macro, rownum=this_row_num)
        this_row_num += 1
        self.add_idf_selection_row("Parametric:", self.idf_selection_parametric, rownum=this_row_num)
        this_row_num += 1
        self.add_idf_selection_row("NoWeather:", self.idf_selection_noweather, rownum=this_row_num)
        this_row_num += 1
        self.add_idf_selection_row("Underscore:", self.idf_selection_underscore, rownum=this_row_num)
        this_row_num += 1

        label = Gtk.Label("")
        label.set_markup("<b>These options will clear all selections first</b>")
        label.set_justify(Gtk.Justification.CENTER)
        alignment = Gtk.Alignment(xalign=0.5, yalign=1.0)
        alignment.add(label)
        self.idf_selection_table.attach(alignment, 0, 3, this_row_num - 1, this_row_num)

        this_row_num += 1
        label = Gtk.Label("Random:")
        label.set_justify(Gtk.Justification.RIGHT)
        alignment = Gtk.Alignment(xalign=1.0)
        alignment.add(label)
        self.idf_selection_table.attach(alignment, 0, 1, this_row_num - 1, this_row_num, Gtk.AttachOptions.FILL,
                                        Gtk.AttachOptions.FILL, 4, 4)
        self.file_list_num_files = Gtk.SpinButton()
        self.file_list_num_files.set_range(0, 1000)
        self.file_list_num_files.set_increments(1, 10)
        self.file_list_num_files.spin(Gtk.SpinType.PAGE_FORWARD,
                                      1)  # EDWIN: Had to add a 1 here for the number of pages I guess?
        self.idf_selection_table.attach(self.file_list_num_files, 1, 2, this_row_num - 1, this_row_num,
                                        Gtk.AttachOptions.FILL,
                                        Gtk.AttachOptions.FILL, 4, 4)
        button = Gtk.Button("Select")
        button.connect("clicked", self.idf_selection_random, "select")
        self.idf_selection_table.attach(button, 2, 3, this_row_num - 1, this_row_num, Gtk.AttachOptions.FILL,
                                        Gtk.AttachOptions.FILL, 4, 4)

        this_row_num += 1
        label = Gtk.Label("Enter a list:")
        label.set_justify(Gtk.Justification.RIGHT)
        alignment = Gtk.Alignment(xalign=1.0)
        alignment.add(label)
        self.idf_selection_table.attach(alignment, 0, 1, this_row_num - 1, this_row_num, Gtk.AttachOptions.FILL,
                                        Gtk.AttachOptions.FILL, 4, 4)
        button = Gtk.Button("Click to enter list")
        button.connect("clicked", self.idf_selection_list)
        self.idf_selection_table.attach(button, 1, 3, this_row_num - 1, this_row_num, Gtk.AttachOptions.FILL,
                                        Gtk.AttachOptions.FILL, 4, 4)

        this_row_num += 1
        label = Gtk.Label("Verify from Folder:")
        label.set_justify(Gtk.Justification.RIGHT)
        alignment = Gtk.Alignment(xalign=1.0)
        alignment.add(label)
        self.idf_selection_table.attach(alignment, 0, 1, this_row_num - 1, this_row_num, Gtk.AttachOptions.FILL,
                                        Gtk.AttachOptions.FILL, 4, 4)
        button = Gtk.Button("Click to select folder")
        button.connect("clicked", self.idf_selection_dir)
        self.idf_selection_table.attach(button, 1, 3, this_row_num - 1, this_row_num, Gtk.AttachOptions.FILL,
                                        Gtk.AttachOptions.FILL, 4, 4)

        # now pack both sides
        notebook_page_idf_selection.pack1(self.add_shadow_frame(notebook_page_idf_list))
        aligner = Gtk.Alignment(xalign=0.25, yalign=0.25, xscale=0.5, yscale=0.5)
        aligner.add(self.idf_selection_table)
        notebook_page_idf_selection.pack2(self.add_shadow_frame(aligner))
        return notebook_page_idf_selection

    def gui_build_notebook_page_test_suite(self):

        # PAGE: TEST SUITE OPTIONS
        notebook_page_suite = Gtk.HPaned()

        notebook_page_suite_options = Gtk.VBox(False, box_spacing)

        heading = Gtk.Label(None)
        heading.set_markup(
            "<b>Test Suite Directories:</b>\n  Mark checkbox to select a directory for running.\n" +
            "  If the runs in the directory are already completed, uncheck it."
        )
        alignment = Gtk.Alignment(xalign=0.0, xscale=0.0)
        alignment.add(heading)
        this_h_box = Gtk.HBox(False, box_spacing)
        this_h_box.pack_start(alignment, False, False, box_spacing)
        notebook_page_suite_options.pack_start(this_h_box, False, False, box_spacing)

        notebook_page_suite_options.pack_start(Gtk.HSeparator(), False, True, box_spacing)

        h_box_1 = Gtk.HBox(False, box_spacing)
        button1 = Gtk.Button("Choose Dir 1...")
        button1.connect("clicked", self.suite_option_handler_basedir)
        alignment = Gtk.Alignment(xalign=0.0, yalign=0.0, xscale=0.0, yscale=0.0)
        alignment.add(button1)
        h_box_1.pack_start(alignment, False, False, box_spacing)
        self.suite_option_handler_basecheckbutton = Gtk.CheckButton("< select a dir >", use_underline=False)
        self.suite_option_handler_basecheckbutton.set_active(self.suiteargs.buildA.run)
        self.suite_option_handler_basecheckbutton.connect("toggled", self.suite_option_handler_basedir_check)
        if self.suiteargs.buildA.build:
            self.suite_option_handler_basecheckbutton.set_label(self.suiteargs.buildA.build)
        alignment = Gtk.Alignment(xalign=0.0, yalign=0.5, xscale=0.0, yscale=0.0)
        alignment.add(self.suite_option_handler_basecheckbutton)
        h_box_1.pack_start(alignment, False, False, box_spacing)
        notebook_page_suite_options.pack_start(h_box_1, False, False, box_spacing)

        this_label = Gtk.Label("Executable name for dir 1 (relative to directory):")
        self.suite_option_baseexe = Gtk.Entry()
        self.suite_option_baseexe.set_size_request(200, -1)
        if self.suiteargs.buildA.executable:
            self.suite_option_baseexe.set_text(self.suiteargs.buildA.executable)
        self.suite_option_baseexe.connect("changed", self.suite_option_handler_baseexe)
        this_h_box = Gtk.HBox(False, box_spacing)
        this_h_box.pack_start(this_label, False, False, box_spacing)
        this_h_box.pack_start(self.suite_option_baseexe, False, False, box_spacing)
        notebook_page_suite_options.pack_start(this_h_box, False, False, box_spacing)

        notebook_page_suite_options.pack_start(Gtk.HSeparator(), False, True, box_spacing)

        h_box_1 = Gtk.HBox(False, box_spacing)
        button2 = Gtk.Button("Choose Dir 2...")
        button2.connect("clicked", self.suite_option_handler_moddir)
        alignment = Gtk.Alignment(xalign=0.0, yalign=0.0, xscale=0.0, yscale=0.0)
        alignment.add(button2)
        h_box_1.pack_start(alignment, False, False, box_spacing)
        self.suite_option_handler_modcheckbutton = Gtk.CheckButton("< select a dir >", use_underline=False)
        self.suite_option_handler_modcheckbutton.set_active(self.suiteargs.buildB.run)
        self.suite_option_handler_modcheckbutton.connect("toggled", self.suite_option_handler_moddir_check)
        if self.suiteargs.buildB.build:
            self.suite_option_handler_modcheckbutton.set_label(self.suiteargs.buildB.build)
        alignment = Gtk.Alignment(xalign=0.0, yalign=0.5, xscale=0.0, yscale=0.0)
        alignment.add(self.suite_option_handler_modcheckbutton)
        h_box_1.pack_start(alignment, False, False, box_spacing)
        notebook_page_suite_options.pack_start(h_box_1, False, False, box_spacing)

        this_label = Gtk.Label("Executable name for dir 2 (relative to directory):")
        self.suite_option_modexe = Gtk.Entry()
        self.suite_option_modexe.set_size_request(200, -1)
        if self.suiteargs.buildB.executable:
            self.suite_option_modexe.set_text(self.suiteargs.buildB.executable)
        self.suite_option_modexe.connect("changed", self.suite_option_handler_modexe)
        alignment = Gtk.Alignment(xalign=0.1, yalign=0.0, xscale=0.6, yscale=0.0)
        this_h_box = Gtk.HBox(False, box_spacing)
        alignment.add(self.suite_option_modexe)
        this_h_box.pack_start(this_label, False, False, box_spacing)
        this_h_box.pack_start(alignment, False, False, box_spacing)
        notebook_page_suite_options.pack_start(this_h_box, False, False, box_spacing)

        notebook_page_suite_options.pack_start(Gtk.HSeparator(), False, True, box_spacing)

        # multirheading in the GUI doesn't works in windows, so don't add the spinbutton if we are on windows
        if platform != "windows":
            numthreadsbox = Gtk.HBox(False, box_spacing)
            self.suite_option_numthreads = Gtk.SpinButton()
            self.suite_option_numthreads.set_range(1, 8)
            self.suite_option_numthreads.set_increments(1, 4)
            self.suite_option_numthreads.spin(Gtk.SpinType.PAGE_FORWARD, 1)  # EDWIN: Had to add a 1 here
            self.suite_option_numthreads.connect("value-changed", self.suite_option_handler_numthreads)
            num_threads_label = Gtk.Label("Number of threads to use for suite")
            num_threads_label_aligner = Gtk.Alignment(xalign=0.0, yalign=0.5, xscale=0.0, yscale=0.0)
            num_threads_label_aligner.add(num_threads_label)
            numthreadsbox.pack_start(num_threads_label_aligner, False, False, box_spacing)
            numthreadsbox.pack_start(self.suite_option_numthreads, False, False, box_spacing)
            notebook_page_suite_options.pack_start(numthreadsbox, False, False, box_spacing)

        h_box_1 = Gtk.HBox(False, box_spacing)
        label1 = Gtk.Label("Select a test suite run configuration: ")
        alignment = Gtk.Alignment(xalign=0.0, yalign=0.5, xscale=0.0, yscale=0.0)
        alignment.add(label1)
        h_box_1.pack_start(alignment, False, False, box_spacing)
        self.runtypecombobox = Gtk.ComboBoxText()
        self.runtypecombobox.append_text(force_none)
        self.runtypecombobox.append_text(force_dd)
        self.runtypecombobox.append_text(force_annual)
        self.runtypecombobox.connect("changed", self.suite_option_handler_forceruntype)
        alignment = Gtk.Alignment(xalign=0.0, yalign=0.0, xscale=0.0, yscale=0.0)
        alignment.add(self.runtypecombobox)
        h_box_1.pack_start(alignment, False, False, box_spacing)
        notebook_page_suite_options.pack_start(h_box_1, False, False, box_spacing)

        h_box_1 = Gtk.HBox(False, box_spacing)
        label1 = Gtk.Label("Select a minimum reporting frequency: ")
        alignment = Gtk.Alignment(xalign=0.0, yalign=0.5, xscale=0.0, yscale=0.0)
        alignment.add(label1)
        h_box_1.pack_start(alignment, False, False, box_spacing)
        self.reportfreqcombobox = Gtk.ComboBoxText()
        self.reportfreqcombobox.append_text(ReportingFreq.DETAILED)
        self.reportfreqcombobox.append_text(ReportingFreq.TIMESTEP)
        self.reportfreqcombobox.append_text(ReportingFreq.HOURLY)
        self.reportfreqcombobox.append_text(ReportingFreq.DAILY)
        self.reportfreqcombobox.append_text(ReportingFreq.MONTHLY)
        self.reportfreqcombobox.append_text(ReportingFreq.RUNPERIOD)
        self.reportfreqcombobox.append_text(ReportingFreq.ENVIRONMENT)
        self.reportfreqcombobox.append_text(ReportingFreq.ANNUAL)
        self.reportfreqcombobox.connect("changed", self.suite_option_handler_reportfreq)
        alignment = Gtk.Alignment(xalign=0.0, yalign=0.0, xscale=0.0, yscale=0.0)
        alignment.add(self.reportfreqcombobox)
        h_box_1.pack_start(alignment, False, False, box_spacing)
        notebook_page_suite_options.pack_start(h_box_1, False, False, box_spacing)

        self.suite_dir_struc_info = Gtk.Label("<Test suite run directory structure information>")
        self.gui_update_label_for_run_config()
        aligner = Gtk.Alignment(xalign=0.0, yalign=0.0, xscale=0.0, yscale=0.0)
        aligner.add(self.suite_dir_struc_info)
        this_h_box = Gtk.HBox(False, box_spacing)
        this_h_box.pack_start(aligner, False, False, box_spacing)
        notebook_page_suite_options.pack_start(this_h_box, False, False, box_spacing)

        notebook_page_suite_options.pack_start(Gtk.HSeparator(), False, True, box_spacing)

        heading = Gtk.Label(None)
        heading.set_markup(
            "<b>E+ Install Dir:</b>\n  External utilities will be accessed from this directory.\n" +
            "  This includes pre- and post-processors."
        )
        alignment = Gtk.Alignment(xalign=0.0, xscale=0.0)
        alignment.add(heading)
        this_h_box = Gtk.HBox(False, box_spacing)
        this_h_box.pack_start(alignment, False, False, box_spacing)
        notebook_page_suite_options.pack_start(this_h_box, False, False, box_spacing)

        h_box_1 = Gtk.HBox(False, box_spacing)
        button1 = Gtk.Button("Choose Dir...")
        button1.connect("clicked", self.suite_option_handler_eplusinstall)
        alignment = Gtk.Alignment(xalign=0.0, yalign=0.0, xscale=0.0, yscale=0.0)
        alignment.add(button1)
        h_box_1.pack_start(alignment, False, False, box_spacing)
        self.suite_option_eplusinstall_label = Gtk.Label("< select a dir >")
        alignment = Gtk.Alignment(xalign=0.0, yalign=0.5, xscale=0.0, yscale=0.0)
        alignment.add(self.suite_option_eplusinstall_label)
        h_box_1.pack_start(alignment, False, False, box_spacing)
        notebook_page_suite_options.pack_start(h_box_1, False, False, box_spacing)

        notebook_page_suite_options.pack_start(Gtk.HSeparator(), False, True, box_spacing)

        heading = Gtk.Label(None)
        heading.set_markup("<b>Runtime Report:</b>")
        alignment = Gtk.Alignment(xalign=0.0, xscale=0.0)
        alignment.add(heading)
        this_h_box = Gtk.HBox(False, box_spacing)
        this_h_box.pack_start(alignment, False, False, box_spacing)
        notebook_page_suite_options.pack_start(this_h_box, False, False, box_spacing)

        self.suite_option_handler_runtimereportcheck = Gtk.CheckButton("Generate a runtime summary for this run?",
                                                                       use_underline=False)
        self.suite_option_handler_runtimereportcheck.set_active(True)
        self.suite_option_handler_runtimereportcheck.connect("toggled", self.suite_option_handler_runtime_check)
        alignment = Gtk.Alignment(xalign=0.0, xscale=0.0)
        alignment.add(self.suite_option_handler_runtimereportcheck)
        this_h_box = Gtk.HBox(False, box_spacing)
        this_h_box.pack_start(alignment, False, False, box_spacing)
        notebook_page_suite_options.pack_start(this_h_box, False, False, box_spacing)

        h_box_1 = Gtk.HBox(False, box_spacing)
        button1 = Gtk.Button("Choose Runtime File...")
        button1.connect("clicked", self.suite_option_handler_runtime_file)
        alignment = Gtk.Alignment(xalign=0.0, yalign=0.0, xscale=0.0, yscale=0.0)
        alignment.add(button1)
        h_box_1.pack_start(alignment, False, False, box_spacing)
        self.suite_option_runtime_file_label = Gtk.Label(self.runtime_report_file)
        alignment = Gtk.Alignment(xalign=0.0, yalign=0.5, xscale=0.0, yscale=0.0)
        alignment.add(self.suite_option_runtime_file_label)
        h_box_1.pack_start(alignment, False, False, box_spacing)
        notebook_page_suite_options.pack_start(h_box_1, False, False, box_spacing)

        notebook_page_suite_options.pack_start(Gtk.HSeparator(), False, True, box_spacing)

        h_box_1 = Gtk.HBox(False, box_spacing)
        button1 = Gtk.Button("Validate Test Suite Directory Structure")
        button1.connect("clicked", self.suite_option_handler_suite_validate)
        alignment = Gtk.Alignment(xalign=0.0, yalign=0.0, xscale=0.0, yscale=0.0)
        alignment.add(button1)
        h_box_1.pack_start(alignment, False, False, box_spacing)

        self.btn_run_suite = Gtk.Button("Run Suite")
        self.btn_run_suite.connect("clicked", self.run_button)
        self.btn_run_suite.set_size_request(120, -1)
        # green = self.btn_run_suite.get_colormap().alloc_color("green")  # EDWIN: Commented this out because no
        # style = self.btn_run_suite.get_style().copy()
        # style.bg[Gtk.STATE_NORMAL] = green
        # self.btn_run_suite.set_style(style)
        alignment = Gtk.Alignment(xalign=0.0, yalign=0.0, xscale=0.0, yscale=0.0)
        alignment.add(self.btn_run_suite)
        h_box_1.pack_start(alignment, False, False, box_spacing)

        notebook_page_suite_options.pack_start(h_box_1, False, False, box_spacing)

        listview_window = Gtk.ScrolledWindow()
        listview_window.set_size_request(-1, 475)
        listview_window.set_shadow_type(Gtk.ShadowType.ETCHED_IN)
        listview_window.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        # make the list store and the treeview
        self.verifyliststore = Gtk.ListStore(str, str, bool, str)
        self.verifyliststore.append(["Press verify to see results", "", True, None])
        self.verifytreeView = Gtk.TreeView(self.verifyliststore)
        self.verifytreeView.set_rules_hint(True)
        # make the columns for the treeview; could add more columns including a checkbox
        # column: idf name
        renderer_text = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn("Verified Parameter", renderer_text, text=0)
        column.set_sort_column_id(0)
        column.set_resizable(True)
        self.verifytreeView.append_column(column)
        # column: selected for run
        renderer_text = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn("Verified?", renderer_text, text=2, foreground=3)
        column.set_sort_column_id(1)
        self.verifytreeView.append_column(column)
        # column: epw name
        renderer_text = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn("Parameter Value", renderer_text, text=1)
        column.set_sort_column_id(2)
        column.set_resizable(True)
        self.verifytreeView.append_column(column)
        listview_window.add(self.verifytreeView)

        notebook_page_suite.pack1(self.add_shadow_frame(notebook_page_suite_options))
        notebook_page_suite.pack2(self.add_shadow_frame(listview_window))
        return notebook_page_suite

    def gui_build_notebook_page_last_run(self):

        # PAGE 4: LAST RUN SUMMARY
        notebook_page_results = Gtk.ScrolledWindow()
        notebook_page_results.set_size_request(-1, 475)
        notebook_page_results.set_shadow_type(Gtk.ShadowType.ETCHED_IN)
        notebook_page_results.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)

        self.resultsliststore = Gtk.TreeStore(str)
        self.resultsparent_numrun = self.resultsliststore.append(None, ["Cases run:"])
        self.resultsparent_success = self.resultsliststore.append(None, ["Case 1 Successful runs:"])
        self.resultsparent_unsuccess = self.resultsliststore.append(None, ["Case 1 Unsuccessful run:"])
        self.resultsparent_success2 = self.resultsliststore.append(None, ["Case 2 Successful runs:"])
        self.resultsparent_unsuccess2 = self.resultsliststore.append(None, ["Case 2 Unsuccessful run:"])
        self.resultsparent_filescompared = self.resultsliststore.append(None, ["Files compared:"])
        self.resultsparent_bigmath = self.resultsliststore.append(None, ["Files with BIG mathdiffs:"])
        self.resultsparent_smallmath = self.resultsliststore.append(None, ["Files with small mathdiffs:"])
        self.resultsparent_bigtable = self.resultsliststore.append(None, ["Files with BIG tablediffs:"])
        self.resultsparent_smalltable = self.resultsliststore.append(None, ["Files with small tablediffs:"])
        self.resultsparent_textual = self.resultsliststore.append(None, ["Files with textual diffs:"])

        self.resultschild_numrun = None
        self.resultschild_success = None
        self.resultschild_unsuccess = None
        self.resultschild_success2 = None
        self.resultschild_unsuccess2 = None
        self.resultschild_filescompared = None
        self.resultschild_bigmath = None
        self.resultschild_smallmath = None
        self.resultschild_bigtable = None
        self.resultschild_smalltable = None
        self.resultschild_textual = None

        self.tree_view = Gtk.TreeView(self.resultsliststore)
        self.tree_view.set_rules_hint(True)
        tvcolumn = Gtk.TreeViewColumn('Results Summary')
        cell = Gtk.CellRendererText()
        tvcolumn.pack_start(cell, True)
        tvcolumn.add_attribute(cell, 'text', 0)
        self.tree_view.append_column(tvcolumn)

        self.tree_view.connect_object("event", self.handle_treeview_context_menu, self.lastrun_context)
        self.tree_view.connect("row-activated", self.handle_treeview_row_activated)
        self.tree_selection = self.tree_view.get_selection()

        self.last_run_heading = Gtk.Label(None)
        self.last_run_heading.set_markup(
            "<b>Hint:</b> Try double-clicking on a filename to launch a file browser to that folder.")
        alignment = Gtk.Alignment(xalign=0.0, xscale=0.0)
        alignment.add(self.last_run_heading)
        this_hbox = Gtk.HBox(False, box_spacing)
        this_hbox.pack_start(alignment, False, False, box_spacing)

        vbox = Gtk.VBox(False, box_spacing)
        vbox.pack_start(this_hbox, False, False, box_spacing)
        notebook_page_results.add(self.tree_view)

        vbox.add(notebook_page_results)
        return vbox

    def handle_treeview_row_activated(self, tv_widget, path_tuple, view_column):
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
        dir_to_open = os.path.join(self.suiteargs.buildA.build, test_dir, case_name)
        if platform == "linux":
            try:
                subprocess.Popen(['xdg-open', dir_to_open])
            except Exception as exc:
                print("Could not open file:")
                print(exc)
        elif platform == "windows":
            try:
                subprocess.Popen(['start', dir_to_open], shell=True)
            except Exception as exc:
                print("Could not open file:")
                print(exc)
        elif platform == "mac":
            try:
                subprocess.Popen(['open', dir_to_open])
            except Exception as exc:
                print("Could not open file:")
                print(exc)

    def gui_build_notebookpage_log(self):

        self.log_scroller_notebook_page = Gtk.ScrolledWindow()
        self.log_scroller_notebook_page.set_shadow_type(Gtk.ShadowType.ETCHED_IN)
        self.log_scroller_notebook_page.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)

        self.logstore = Gtk.ListStore(str, str)
        self.logstore.append(["%s" % str(datetime.now()), "%s" % "Program initialized"])

        tree_view = Gtk.TreeView(self.logstore)
        tree_view.set_rules_hint(True)
        tree_view.connect("size-allocate", self.treeview_size_changed)

        column = Gtk.TreeViewColumn("TimeStamp", Gtk.CellRendererText(), text=0)
        column.set_sort_column_id(0)
        column.set_resizable(True)
        tree_view.append_column(column)

        column = Gtk.TreeViewColumn("Message", Gtk.CellRendererText(), text=1)
        column.set_sort_column_id(1)
        column.set_resizable(True)
        tree_view.append_column(column)
        self.log_scroller_notebook_page.add(tree_view)

        v_box = Gtk.VBox(False, box_spacing)
        v_box.pack_start(
            self.log_scroller_notebook_page, False, False, box_spacing
        )  # EDWIN: Added False False here, verify this

        clear_button = Gtk.Button("Clear Log Messages")
        clear_button.connect("clicked", self.clear_log)
        alignment = Gtk.Alignment(xalign=0.5, yalign=0.0, xscale=0.0, yscale=0.0)
        alignment.add(clear_button)

        v_box.pack_start(alignment, False, False, box_spacing)

        return v_box

    def clear_log(self, widget):
        self.logstore.clear()

    def treeview_size_changed(self, widget, event, data=None):

        # this routine should autoscroll the vadjustment if the user is scrolled to within 0.2*page height of the widget
        # get things once
        adj = self.log_scroller_notebook_page.get_vadjustment()
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
        # self.notebook.set_tab_pos(Gtk.POS_TOP)
        self.notebook.append_page(self.gui_build_notebook_page_idf_selection(), Gtk.Label("IDF Selection"))
        self.notebook.append_page(self.gui_build_notebook_page_test_suite(), Gtk.Label("Test Suite"))
        self.notebook.append_page(self.gui_build_notebook_page_last_run(), Gtk.Label("Last Run Summary"))
        self.notebook.append_page(self.gui_build_notebookpage_log(), Gtk.Label("Log Messages"))
        return self.notebook

    def gui_build_messaging(self):

        self.progress = Gtk.ProgressBar()
        self.status_bar = Gtk.Statusbar()
        aligner = Gtk.Alignment(xalign=1.0, yalign=0.0, xscale=0.4, yscale=1.0)
        aligner.add(self.progress)
        self.status_bar.pack_start(aligner, False, False, box_spacing)  # EDWIN: Added args here
        self.status_bar_context_id = self.status_bar.get_context_id("Status")
        aligner = Gtk.Alignment(xalign=1.0, yalign=1.0, xscale=1.0, yscale=0.0)
        aligner.add(self.status_bar)
        return aligner

    def build_pre_gui_stuff(self):

        # build the last run context menu
        self.lastrun_context = Gtk.Menu()
        self.lastrun_context_copy = Gtk.MenuItem("Copy files from this node to the clipboard")
        self.lastrun_context.append(self.lastrun_context_copy)
        self.lastrun_context_copy.connect("activate", self.handle_resultslistcopy)
        self.lastrun_context_copy.hide()
        self.lastrun_context_nocopy = Gtk.MenuItem("No files on this node to copy to the clipboard")
        self.lastrun_context.append(self.lastrun_context_nocopy)
        self.lastrun_context_nocopy.show()

    def add_frame(self, widget):
        frame = Gtk.Frame()
        frame.modify_bg(Gtk.STATE_NORMAL, Gtk.gdk.Color(56283, 22359, 0))
        frame.add(widget)
        return frame

    def add_shadow_frame(self, widget):
        frame = Gtk.Frame()
        frame.set_shadow_type(Gtk.ShadowType.IN)
        frame.add(widget)
        return frame

    def add_log_entry(self, message):
        if len(self.logstore) >= 5000:
            self.logstore.remove(self.logstore[0].iter)
        self.logstore.append(["%s" % str(datetime.now()), "%s" % message])

    def warning_dialog(self, message, do_log_entry=True):
        dialog = Gtk.MessageDialog(self, Gtk.DIALOG_MODAL | Gtk.DIALOG_DESTROY_WITH_PARENT, Gtk.MESSAGE_WARNING,
                                   Gtk.BUTTONS_OK, message)
        dialog.set_title("Warning message")
        dialog.run()
        if do_log_entry:
            self.add_log_entry("Warning: %s" % message)
        dialog.destroy()

    def warning_not_yet_built(self):
        self.warning_dialog("File selection and/or test suite operations can't be performed until master list is built")

    def show_help_pdf(self, widget):
        path_to_pdf = os.path.join(script_dir, "..", "Documentation", "ep-testsuite.pdf")
        if not os.path.exists(path_to_pdf):
            dialog = Gtk.MessageDialog(self, Gtk.DIALOG_DESTROY_WITH_PARENT, Gtk.MESSAGE_ERROR, Gtk.BUTTONS_CLOSE,
                                       "Could not find help file; expected at:\n %s" % path_to_pdf)
            dialog.run()
            dialog.destroy()
            return

        try:
            if platform == "mac":
                subprocess.call(['open', path_to_pdf])
            elif platform == "windows":
                subprocess.call(['start', path_to_pdf])  # EDWIN: Verify this works
            elif platform == "linux":
                subprocess.call(['xdg-open', path_to_pdf])
        except Exception as exc:
            # error message
            dialog = Gtk.MessageDialog(
                self, Gtk.DIALOG_DESTROY_WITH_PARENT, Gtk.MESSAGE_ERROR, Gtk.BUTTONS_CLOSE,
                "Could not open help file.  Try opening manually.  File is at:\n %s" % path_to_pdf
            )
            dialog.run()
            dialog.destroy()
            print(exc)
            return

    # IDF selection worker and handlers for buttons and checkboxes, etc.

    def init_file_list_builder_args(self):

        # could read from temp file

        # build a default set of arguments
        self.file_list_builder_configuration = filelist_argsbuilder_forgui()

        # override with our defaults
        self.file_list_builder_configuration.check = False
        self.file_list_builder_configuration.master_data_file = os.path.join(script_dir, 'FullFileSetDetails.csv')

    def build_button(self, widget):

        self.status_bar.push(self.status_bar_context_id, "Building idf list")

        this_builder = file_list_builder(self.file_list_builder_configuration)
        this_builder.set_callbacks(self.build_callback_print, self.build_callback_init, self.build_callback_increment)
        status, verified_idfs, idfs_missing_in_folder, idfs_missing_from_csvfile = this_builder.build_verified_list(
            self.file_list_builder_configuration)

        # reset the progress bar either way
        self.progress.set_fraction(self.current_progress_value / self.progress_maximum_value)

        # return if not successful
        if not status:
            return

        self.idf_list_store.clear()
        for filea in verified_idfs:
            this_file = [True, filea.filename]
            if filea.has_weather_file:
                this_file.append(filea.weatherfilename)
            else:
                this_file.append(self.missing_weather_file_key)
            for attr in [filea.external_interface, filea.ground_ht, filea.external_dataset, filea.parametric,
                         filea.macro, filea.delight]:
                if attr:
                    this_file.append("Y")
                else:
                    this_file.append("")
            self.idf_list_store.append(this_file)

        self.add_log_entry("Completed building idf list")
        self.add_log_entry("Resulting file list has %s entries; During verification:" % len(verified_idfs))
        self.add_log_entry(
            "\t there were %s files listed in the csv database that were missing in verification folder(s), and" % len(
                idfs_missing_in_folder))
        self.add_log_entry(
            "\t there were %s files found in the verification folder(s) that were missing from csv datafile" % len(
                idfs_missing_from_csvfile))
        self.idf_files_have_been_built = True

    def build_callback_print(self, msg):
        # no need to invoke gobject on this since the builder isn't on a separate thread
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
        for filea in self.idf_list_store:
            filea[0] = selection
        self.update_status_with_num_selected()

    def idf_selection_extint(self, widget, calltype):
        if not self.idf_files_have_been_built:
            self.warning_not_yet_built()
            return
        column = IDFListViewColumnIndex.EXTERNAL_INTERFACE
        selection = False
        if calltype == "select":
            selection = True
        for filea in self.idf_list_store:
            if filea[column] == "Y":
                filea[0] = selection
        self.update_status_with_num_selected()

    def idf_selection_groundht(self, widget, calltype):
        if not self.idf_files_have_been_built:
            self.warning_not_yet_built()
            return
        column = IDFListViewColumnIndex.GROUND_HT
        selection = False
        if calltype == "select":
            selection = True
        for filea in self.idf_list_store:
            if filea[column] == "Y":
                filea[0] = selection
        self.update_status_with_num_selected()

    def idf_selection_dataset(self, widget, calltype):
        if not self.idf_files_have_been_built:
            self.warning_not_yet_built()
            return
        column = IDFListViewColumnIndex.DATA_SET
        selection = False
        if calltype == "select":
            selection = True
        for filea in self.idf_list_store:
            if filea[column] == "Y":
                filea[0] = selection
        self.update_status_with_num_selected()

    def idf_selection_delight(self, widget, calltype):
        if not self.idf_files_have_been_built:
            self.warning_not_yet_built()
            return
        column = IDFListViewColumnIndex.DELIGHT
        selection = False
        if calltype == "select":
            selection = True
        for filea in self.idf_list_store:
            if filea[column] == "Y":
                filea[0] = selection
        self.update_status_with_num_selected()

    def idf_selection_macro(self, widget, calltype):
        if not self.idf_files_have_been_built:
            self.warning_not_yet_built()
            return
        column = IDFListViewColumnIndex.MACRO
        selection = False
        if calltype == "select":
            selection = True
        for filea in self.idf_list_store:
            if filea[column] == "Y":
                filea[0] = selection
        self.update_status_with_num_selected()

    def idf_selection_parametric(self, widget, calltype):
        if not self.idf_files_have_been_built:
            self.warning_not_yet_built()
            return
        column = IDFListViewColumnIndex.PARAMETRIC
        selection = False
        if calltype == "select":
            selection = True
        for filea in self.idf_list_store:
            if filea[column] == "Y":
                filea[0] = selection
        self.update_status_with_num_selected()

    def idf_selection_noweather(self, widget, calltype):
        if not self.idf_files_have_been_built:
            self.warning_not_yet_built()
            return
        column = IDFListViewColumnIndex.EPW
        selection = False
        if calltype == "select":
            selection = True
        for filea in self.idf_list_store:
            if filea[column] == self.missing_weather_file_key:
                filea[0] = selection
        self.update_status_with_num_selected()

    def idf_selection_underscore(self, widget, calltype):
        if not self.idf_files_have_been_built:
            self.warning_not_yet_built()
            return
        column = IDFListViewColumnIndex.IDF
        selection = False
        if calltype == "select":
            selection = True
        for filea in self.idf_list_store:
            if filea[column][0] == "_":
                filea[0] = selection
        self.update_status_with_num_selected()

    def idf_selection_random(self, widget, calltype):
        if not self.idf_files_have_been_built:
            self.warning_not_yet_built()
            return
        # clear them all first; eventually this could be changed to just randomly "down-select" already checked items
        for filea in self.idf_list_store:
            filea[0] = False
        number_to_select = int(self.file_list_num_files.get_value())
        number_of_idfs = len(self.idf_list_store)
        if len(self.idf_list_store) <= number_to_select:  # just take all of them
            pass
        else:  # down select randomly
            indeces_to_take = random.sample(range(number_of_idfs), number_to_select)
            for i in indeces_to_take:
                self.idf_list_store[i][0] = True
        self.update_status_with_num_selected()

    def idf_selection_dir(self, widget):
        if not self.idf_files_have_been_built:
            self.warning_not_yet_built()
            return
        self.add_log_entry("User is entering idfs for selection using a folder of idfs")
        dialog = Gtk.FileChooserDialog(title="Select folder",
                                       buttons=(Gtk.STOCK_CANCEL, Gtk.RESPONSE_CANCEL, Gtk.STOCK_OPEN, Gtk.RESPONSE_OK))
        dialog.set_action(Gtk.FILE_CHOOSER_ACTION_SELECT_FOLDER)
        dialog.set_select_multiple(False)
        if self.last_folder_path:
            dialog.set_current_folder(self.last_folder_path)
        response = dialog.run()
        if response == Gtk.RESPONSE_OK:
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
        filenames_in_liststore = [x[1] for x in self.idf_list_store]
        for filea in files_to_select:
            if filea not in filenames_in_liststore:
                files_entered_not_available.append(filea)
        if len(files_entered_not_available) > 0:
            text = ""
            num = 0
            for filea in files_entered_not_available:
                num += 1
                text += "\t%s\n" % filea
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
        for filea in self.idf_list_store:
            if filea[1] in files_to_select:
                filea[0] = True
            else:
                filea[0] = False
        self.update_status_with_num_selected()

    def idf_selection_list(self, widget):
        if not self.idf_files_have_been_built:
            self.warning_not_yet_built()
            return
        self.add_log_entry("User is entering idfs for selection using dialog")
        dialog = Gtk.MessageDialog(self, Gtk.DIALOG_MODAL | Gtk.DIALOG_DESTROY_WITH_PARENT, Gtk.MESSAGE_QUESTION,
                                   Gtk.BUTTONS_OK_CANCEL, None)
        dialog.set_title("Enter list of files to select")
        dialog.set_markup('Enter filenames to select, one per line\nFile extensions are optional')
        scroller = Gtk.ScrolledWindow()
        scroller.set_size_request(400, 400)
        scroller.set_shadow_type(Gtk.ShadowType.ETCHED_IN)
        scroller.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        entry = Gtk.TextView()
        scroller.add(entry)
        dialog.vbox.pack_end(scroller, True, True, 0)
        dialog.show_all()
        result = dialog.run()
        mybuffer = entry.get_buffer()
        text = mybuffer.get_text(mybuffer.get_start_iter(), mybuffer.get_end_iter())
        dialog.destroy()
        if result != Gtk.RESPONSE_OK:
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
        filenames_in_liststore = [x[1] for x in self.idf_list_store]
        for filea in files_to_select:
            if filea not in filenames_in_liststore:
                files_entered_not_available.append(filea)
        if len(files_entered_not_available) > 0:
            text = ""
            num = 0
            for filea in files_entered_not_available:
                num += 1
                text += "\t%s\n" % filea
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
        for filea in self.idf_list_store:
            if filea[1] in files_to_select:
                filea[0] = True
            else:
                filea[0] = False
        self.update_status_with_num_selected()

    def file_list_handler_toggle_listview(self, widget, this_path, list_store):
        list_store[this_path][0] = not list_store[this_path][0]
        self.update_status_with_num_selected()

    def update_status_with_num_selected(self):
        num_selected = 0
        for filea in self.idf_list_store:
            if filea[0]:
                num_selected += 1
        self.status_bar.push(self.status_bar_context_id, "%i IDFs selected now" % num_selected)

    # Test Suite workers and GUI handlers

    def init_suite_args(self):

        self.do_runtime_report = True
        if platform == "windows":
            self.runtime_report_file = "C:\temp\runtimes.csv"
        else:
            self.runtime_report_file = "/tmp/runtimes.csv"

        # For ALL runs use BuildA
        if platform == "windows":
            suiteargs_base = SingleBuildDirectory(directory_path="C:\ResearchProjects\EnergyPlus\Versions\V8.1Release",
                                                  executable_name="build\Debug\EnergyPlus.exe",
                                                  run_this_directory=True)
        else:
            suiteargs_base = SingleBuildDirectory(directory_path="/home/elee/EnergyPlus/Builds/Releases/8.1.0.009",
                                                  executable_name="8.1.0.009_ifort_release",
                                                  run_this_directory=True)

            # If using ReverseDD, builB can just be None
        if platform == "windows":
            suiteargs_mod = SingleBuildDirectory(directory_path="C:\ResearchProjects\EnergyPlus\Versions\V8.1ReRelease",
                                                 executable_name="build\Debug\EnergyPlus.exe",
                                                 run_this_directory=True)
        else:
            suiteargs_mod = SingleBuildDirectory(directory_path="/home/elee/EnergyPlus/Builds/Releases/8.2.0.001",
                                                 executable_name="8.2.0.001_ifort_release",
                                                 run_this_directory=True)

        # Build the run configuration and the number of threads; using 1 for
        #  windows causes the runtests script to not even use the multithread libraries
        installpath = ""
        num_threads_to_run = 1
        if platform == "windows":
            installpath = 'C:\EnergyPlusV8-1-0'
            num_threads_to_run = 1
        else:
            installpath = '/home/elee/EnergyPlus/EnergyPlus-8-1-0'
            num_threads_to_run = 4
        self.suiteargs = TestRunConfiguration(run_mathdiff=True,
                                              do_composite_err=True,
                                              force_run_type=ForceRunType.NONE,  # ANNUAL, DD, NONE, REVERSEDD
                                              single_test_run=False,
                                              eplus_install_path=installpath,
                                              num_threads=num_threads_to_run,
                                              report_freq=ReportingFreq.HOURLY,
                                              buildA=suiteargs_base,
                                              buildB=suiteargs_mod)

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
        entries = []
        for filea in self.idf_list_store:
            if filea[IDFListViewColumnIndex.RUN]:  # if it is checked
                if self.missing_weather_file_key not in filea[IDFListViewColumnIndex.EPW]:
                    entries.append(TestEntry(filea[IDFListViewColumnIndex.IDF], filea[IDFListViewColumnIndex.EPW]))
                else:
                    entries.append(TestEntry(filea[IDFListViewColumnIndex.IDF], None))

        if len(entries) == 0:
            self.warning_dialog("Attempted to run a test suite with no files selected")
            return

        # set up the test suite
        self.runner = TestSuiteRunner(self.suiteargs, entries)
        self.runner.add_callbacks(print_callback=self.print_callback,
                                  simstarting_callback=self.simstarting_callback,
                                  casecompleted_callback=self.casecompleted_callback,
                                  simulationscomplete_callback=self.simulationscomplete_callback,
                                  enderrcompleted_callback=self.enderrcompleted_callback,
                                  diffcompleted_callback=self.diffcompleted_callback,
                                  alldone_callback=self.alldone_callback,
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

    def suite_option_handler_basedir(self, widget):
        dialog = Gtk.FileChooserDialog(title="Select folder",
                                       buttons=(Gtk.STOCK_CANCEL, Gtk.RESPONSE_CANCEL, Gtk.STOCK_OPEN, Gtk.RESPONSE_OK))
        dialog.set_action(Gtk.FILE_CHOOSER_ACTION_SELECT_FOLDER)
        dialog.set_select_multiple(False)
        if self.last_folder_path:
            dialog.set_current_folder(self.last_folder_path)
        response = dialog.run()
        if response == Gtk.RESPONSE_OK:
            self.last_folder_path = dialog.get_filename()
            self.suiteargs.buildA.build = self.last_folder_path
            self.suite_option_handler_basecheckbutton.set_label(self.last_folder_path)
        dialog.destroy()

    def suite_option_handler_basedir_check(self, widget):
        self.suiteargs.buildA.run = widget.get_active()

    def suite_option_handler_moddir(self, widget):
        dialog = Gtk.FileChooserDialog(title="Select folder",
                                       buttons=(Gtk.STOCK_CANCEL, Gtk.RESPONSE_CANCEL, Gtk.STOCK_OPEN, Gtk.RESPONSE_OK))
        dialog.set_action(Gtk.FILE_CHOOSER_ACTION_SELECT_FOLDER)
        dialog.set_select_multiple(False)
        if self.last_folder_path:
            dialog.set_current_folder(self.last_folder_path)
        response = dialog.run()
        if response == Gtk.RESPONSE_OK:
            self.last_folder_path = dialog.get_filename()
            self.suiteargs.buildB.build = self.last_folder_path
            self.suite_option_handler_modcheckbutton.set_label(self.last_folder_path)
        dialog.destroy()

    def suite_option_handler_moddir_check(self, widget):
        self.suiteargs.buildB.run = widget.get_active()

    def suite_option_handler_baseexe(self, widget):
        if widget.get_text():
            self.suiteargs.buildA.executable = widget.get_text()
        else:
            self.suiteargs.buildA.executable = ''

    def suite_option_handler_modexe(self, widget):
        if widget.get_text():
            self.suiteargs.buildB.executable = widget.get_text()
        else:
            self.suiteargs.buildB.executable = ''

    def suite_option_handler_forceruntype(self, widget):
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

    def suite_option_handler_reportfreq(self, widget):
        self.suiteargs.report_freq = widget.get_active_text()
        self.gui_update_label_for_run_config()

    def suite_option_handler_eplusinstall(self, widget):
        dialog = Gtk.FileChooserDialog(title="Select folder",
                                       buttons=(Gtk.STOCK_CANCEL, Gtk.RESPONSE_CANCEL, Gtk.STOCK_OPEN, Gtk.RESPONSE_OK))
        dialog.set_action(Gtk.FILE_CHOOSER_ACTION_SELECT_FOLDER)
        dialog.set_select_multiple(False)
        if self.last_folder_path:
            dialog.set_current_folder(self.last_folder_path)
        response = dialog.run()
        if response == Gtk.RESPONSE_OK:
            self.last_folder_path = dialog.get_filename()
            self.suiteargs.eplus_install = self.last_folder_path
            self.suite_option_eplusinstall_label.set_label(self.last_folder_path)
        dialog.destroy()

    def suite_option_handler_numthreads(self, widget):
        self.suiteargs.num_threads = widget.get_value()

    def get_row_color(self, boolean):
        if boolean:
            return None  # Gtk.gdk.Color(127, 255, 0)
        else:
            return "red"  # Gtk.gdk.Color(220, 20, 60)

    def suite_option_handler_runtime_file(self, widget):
        dialog = Gtk.FileChooserDialog(title="Select runtime file save name", action=Gtk.FILE_CHOOSER_ACTION_SAVE,
                                       buttons=(Gtk.STOCK_CANCEL, Gtk.RESPONSE_CANCEL, Gtk.STOCK_OPEN, Gtk.RESPONSE_OK))
        dialog.set_select_multiple(False)
        if self.last_folder_path:
            dialog.set_current_folder(self.last_folder_path)
        afilter = Gtk.FileFilter()
        afilter.set_name("CSV Files")
        afilter.add_pattern("*.csv")
        dialog.add_filter(afilter)
        response = dialog.run()
        if response == Gtk.RESPONSE_OK:
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
        run_type = self.suiteargs.force_run_type

        self.add_log_entry("Verifying directory structure")

        # check for directory, then executable and IDD, then input files
        self.verifyliststore.clear()
        if run_type == ForceRunType.REVERSEDD:
            basedir = self.suiteargs.buildA.build
            exec_path = os.path.join(basedir, self.suiteargs.buildA.executable)
            idd_path = os.path.join(basedir, "Energy+.idd")
            idf_folder = os.path.join(basedir, "InputFiles")
            basedir_exists = os.path.exists(basedir)
            self.verifyliststore.append(
                ["Suite Directory Exists:", basedir, basedir_exists, self.get_row_color(basedir_exists)])
            checked = self.suiteargs.buildA.run
            self.verifyliststore.append(
                ["Suite Directory Selected:", "Checkbox checked?", checked, self.get_row_color(checked)])
            exec_exists = os.path.exists(exec_path)
            self.verifyliststore.append(
                ["Suite Executable Exists:", exec_path, exec_exists, self.get_row_color(exec_exists)])
            idd_exists = os.path.exists(idd_path)
            self.verifyliststore.append(
                ["Suite Energy+.idd Exists:", idd_path, idd_exists, self.get_row_color(idd_exists)])
            idfdir_exists = os.path.exists(idf_folder)
            self.verifyliststore.append(
                ["Suite Input File Folder Exists:", idf_folder, idfdir_exists, self.get_row_color(idfdir_exists)])
            if basedir_exists and checked and exec_exists and idd_exists and idfdir_exists:
                self.add_log_entry("Reverse Design Day directory verification passed")
            else:
                self.add_log_entry("Reverse Design Day directory verification FAILED")
        else:
            basedir = self.suiteargs.buildA.build
            exec_path = os.path.join(basedir, self.suiteargs.buildA.executable)
            idd_path = os.path.join(basedir, "Energy+.idd")
            idf_folder = os.path.join(basedir, "InputFiles")
            basedir_exists = os.path.exists(basedir)
            self.verifyliststore.append(
                ["Base Directory Exists:", basedir, basedir_exists, self.get_row_color(basedir_exists)])
            checked = self.suiteargs.buildA.run
            if checked:
                self.verifyliststore.append(
                    ["Base Directory Selected:", "Checkbox checked?", checked, self.get_row_color(checked)])
                exec_exists = os.path.exists(exec_path)
                self.verifyliststore.append(
                    ["Base Executable Exists:", exec_path, exec_exists, self.get_row_color(exec_exists)])
                idd_exists = os.path.exists(idd_path)
                self.verifyliststore.append(
                    ["Base Energy+.idd Exists:", idd_path, idd_exists, self.get_row_color(idd_exists)])
                idfdir_exists = os.path.exists(idf_folder)
                self.verifyliststore.append(
                    ["Base Input File Folder Exists:", idf_folder, idfdir_exists, self.get_row_color(idfdir_exists)])

            basedir = self.suiteargs.buildB.build
            exec_path = os.path.join(basedir, self.suiteargs.buildB.executable)
            idd_path = os.path.join(basedir, "Energy+.idd")
            idf_folder = os.path.join(basedir, "InputFiles")
            basedir_exists = os.path.exists(basedir)
            self.verifyliststore.append(
                ["Mod Directory Exists:", basedir, basedir_exists, self.get_row_color(basedir_exists)])
            checked = self.suiteargs.buildB.run
            if checked:
                self.verifyliststore.append(
                    ["Mod Directory Selected:", "Checkbox checked?", checked, self.get_row_color(checked)])
                exec_exists = os.path.exists(exec_path)
                self.verifyliststore.append(
                    ["Mod Executable Exists:", exec_path, exec_exists, self.get_row_color(exec_exists)])
                idd_exists = os.path.exists(idd_path)
                self.verifyliststore.append(
                    ["Mod Energy+.idd Exists:", idd_path, idd_exists, self.get_row_color(idd_exists)])
                idfdir_exists = os.path.exists(idf_folder)
                self.verifyliststore.append(
                    ["Mod Input File Folder Exists:", idf_folder, idfdir_exists, self.get_row_color(idfdir_exists)])

        # set up paths
        eplus_install = self.suiteargs.eplus_install
        basement = os.path.join(eplus_install, 'PreProcess', 'GrndTempCalc', 'Basement')
        slab = os.path.join(eplus_install, 'PreProcess', 'GrndTempCalc', 'Slab')
        basementidd = os.path.join(eplus_install, 'PreProcess', 'GrndTempCalc', 'BasementGHT.idd')
        slabidd = os.path.join(eplus_install, 'PreProcess', 'GrndTempCalc', 'SlabGHT.idd')
        expandobjects = os.path.join(eplus_install, 'ExpandObjects')
        epmacro = os.path.join(eplus_install, 'EPMacro')
        readvars = os.path.join(eplus_install, 'PostProcess', 'ReadVarsESO')
        parametric = os.path.join(eplus_install, 'PreProcess', 'ParametricPreProcessor', 'parametricpreprocessor')

        # if we're on windows, append the executable extension
        if platform == "windows":
            basement += ".exe"
            slab += ".exe"
            expandobjects += ".exe"
            epmacro += ".exe"
            readvars += ".exe"
            parametric += ".exe"

        # check if they exist
        eplus_install_exists = os.path.exists(eplus_install)
        basement_exists = os.path.exists(basement)
        slab_exists = os.path.exists(slab)
        basementidd_exists = os.path.exists(basementidd)
        slabidd_exists = os.path.exists(slabidd)
        expandobjects_exists = os.path.exists(expandobjects)
        epmacro_exists = os.path.exists(epmacro)
        readvars_exists = os.path.exists(readvars)
        parametric_exists = os.path.exists(parametric)

        # add to liststore
        self.verifyliststore.append(
            ["E+ Install Dir Exists:", eplus_install, eplus_install_exists, self.get_row_color(eplus_install_exists)])
        self.verifyliststore.append(
            ["Basement Executable Exists:", basement, basement_exists, self.get_row_color(basement_exists)])
        self.verifyliststore.append(["Slab Executable Exists:", slab, slab_exists, self.get_row_color(slab_exists)])
        self.verifyliststore.append(
            ["Basement IDD Exists:", basementidd, basementidd_exists, self.get_row_color(basementidd_exists)])
        self.verifyliststore.append(["Slab IDD Exists:", slabidd, slabidd_exists, self.get_row_color(slabidd_exists)])
        self.verifyliststore.append(["ExpandObjects Executable Exists:", expandobjects, expandobjects_exists,
                                     self.get_row_color(expandobjects_exists)])
        self.verifyliststore.append(
            ["EPMacro Executable Exists:", epmacro, epmacro_exists, self.get_row_color(epmacro_exists)])
        self.verifyliststore.append(
            ["ReadVars Executable Exists:", readvars, readvars_exists, self.get_row_color(readvars_exists)])
        self.verifyliststore.append(
            ["Parametric PreProcessor Exists:", parametric, parametric_exists, self.get_row_color(parametric_exists)])

        if all([item[2] for item in self.verifyliststore]):
            return True
        else:
            return False

    def handle_resultslistcopy(self, widget):
        current_list = self.results_lists_to_copy[self.resultslist_selected_entry_root_index]
        if current_list is not None:
            string = ""
            for item in current_list:
                string += "%s\n" % item
            clip = Gtk.Clipboard()
            clip.set_text(string)
        else:
            pass

    def handle_treeview_context_menu(self, widget, event):
        if event.type == Gtk.gdk.BUTTON_PRESS and event.button == 3:
            x = int(event.x)
            y = int(event.y)
            time = event.time
            pthinfo = self.tree_view.get_path_at_pos(x, y)
            if pthinfo is not None:
                this_path, col, cellx, celly = pthinfo
                self.tree_view.grab_focus()
                self.tree_view.set_cursor(this_path, col, 0)
                widget.popup(None, None, None, event.button, time)
                self.resultslist_selected_entry_root_index = this_path[0]
                self.lastrun_context_copy.show()
                self.lastrun_context_nocopy.hide()
            else:
                self.lastrun_context_copy.hide()
                self.lastrun_context_nocopy.show()

    def gui_update_label_for_run_config(self):
        current_config = self.suiteargs.force_run_type
        if current_config == ForceRunType.NONE:
            self.suite_dir_struc_info.set_markup(
                "<b>Results:</b>\n  A 'Tests' directory will be created in each run directory.\n" +
                "  Comparison results will be in run directory 1."
            )
        elif current_config == ForceRunType.DD:
            self.suite_dir_struc_info.set_markup(
                "<b>Results:</b>\n  A 'Tests-DDOnly' directory will be created in each run directory.\n" +
                "  Comparison results will be in run directory 1."
            )
        elif current_config == ForceRunType.ANNUAL:
            self.suite_dir_struc_info.set_markup(
                "<b>Results:</b>\n  A 'Tests-Annual' directory will be created in each run directory.\n" +
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

    def simstarting_callback(self, number_of_builds, number_of_cases_per_build):
        result = GObject.idle_add(self.simstarting_callback_handler, number_of_builds, number_of_cases_per_build)

    def simstarting_callback_handler(self, number_of_builds, number_of_cases_per_build):
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

    def casecompleted_callback(self, test_case_completed_instance):
        result = GObject.idle_add(self.casecompleted_callback_handler, test_case_completed_instance)

    def casecompleted_callback_handler(self, test_case_completed_instance):
        self.current_progress_value += 1.0
        self.progress.set_fraction(self.current_progress_value / self.progress_maximum_value)
        if not test_case_completed_instance.muffle_err_msg:
            if test_case_completed_instance.run_success:
                self.print_callback_handler("Completed %s : %s, Success" % (
                    test_case_completed_instance.run_directory, test_case_completed_instance.case_name))
            else:
                self.print_callback_handler("Completed %s : %s, Failed" % (
                    test_case_completed_instance.run_directory, test_case_completed_instance.case_name))

    def simulationscomplete_callback(self):
        result = GObject.idle_add(self.simulationscomplete_callback_handler)

    def simulationscomplete_callback_handler(self):
        self.status_bar.push(self.status_bar_context_id, "Simulations done; Post-processing...")

    def enderrcompleted_callback(self, build_name, case_name):
        result = GObject.idle_add(self.enderrcompleted_callback_handler, build_name, case_name)

    def enderrcompleted_callback_handler(self, build_name, case_name):
        self.current_progress_value += 1.0
        self.progress.set_fraction(self.current_progress_value / self.progress_maximum_value)

    def diffcompleted_callback(self, case_name):
        result = GObject.idle_add(self.diffcompleted_callback_handler, case_name)

    def diffcompleted_callback_handler(self, case_name):
        self.current_progress_value += 1.0
        self.progress.set_fraction(self.current_progress_value / self.progress_maximum_value)

    def alldone_callback(self, results):
        result = GObject.idle_add(self.alldone_callback_handler, results)

    def alldone_callback_handler(self, results):

        totalnum = 0
        totalnum_ = []
        totalnum_files = []
        totaldifffiles = 0
        totaldifffiles_ = []
        totaldifffiles_files = []
        numbigdiffs = 0
        numbigdiffs_ = []
        numbigdiffs_files = []
        numsmalldiffs = 0
        numsmalldiffs_ = []
        numsmalldiffs_files = []
        numsuccess = 0
        numsuccess_ = []
        numsuccess_files = []
        numnotsuccess = 0
        numnotsuccess_ = []
        numnotsuccess_files = []
        numsuccess2 = 0
        numsuccess2_ = []
        numsuccess2_files = []
        numnotsuccess2 = 0
        numnotsuccess2_ = []
        numnotsuccess2_files = []
        numtablebigdiffs = 0
        numtablebigdiffs_ = []
        numtablebigdiffs_files = []
        numtablesmalldiffs = 0
        numtablesmalldiffs_ = []
        numtablesmalldiffs_files = []
        numtextdiffs = 0
        numtextdiffs_ = []
        numtextdiffs_files = []

        for entry in results:
            totalnum += 1
            totalnum_.append(["%s" % entry.basename])
            totalnum_files.append(entry.basename)
            if entry.summary_result.simulation_status_case1 == EndErrSummary.STATUS_SUCCESS:
                numsuccess += 1
                numsuccess_.append(["%s" % entry.basename])
                numsuccess_files.append(entry.basename)
            else:
                numnotsuccess += 1
                numnotsuccess_.append(["%s" % entry.basename])
                numnotsuccess_files.append(entry.basename)
            if entry.summary_result.simulation_status_case2 == EndErrSummary.STATUS_SUCCESS:
                numsuccess2 += 1
                numsuccess2_.append(["%s" % entry.basename])
                numsuccess2_files.append(entry.basename)
            else:
                numnotsuccess2 += 1
                numnotsuccess2_.append(["%s" % entry.basename])
                numnotsuccess2_files.append(entry.basename)
            if entry.has_eso_diffs:
                totaldifffiles += 1
                totaldifffiles_.append(["%s: eso" % entry.basename])
                if entry.basename not in totaldifffiles_files:
                    totaldifffiles_files.append(entry.basename)
                if entry.eso_diffs.count_of_big_diff > 0:
                    numbigdiffs += 1
                    numbigdiffs_.append(["%s: %s" % (entry.basename, "eso")])
                    if entry.basename not in numbigdiffs_files:
                        numbigdiffs_files.append(entry.basename)
                elif entry.eso_diffs.count_of_small_diff > 0:
                    numsmalldiffs += 1
                    numsmalldiffs_.append(["%s: %s" % (entry.basename, "eso")])
                    if entry.basename not in numsmalldiffs_files:
                        numsmalldiffs_files.append(entry.basename)
            if entry.has_mtr_diffs:
                totaldifffiles += 1
                totaldifffiles_.append(["%s: mtr" % entry.basename])
                if entry.basename not in totaldifffiles_files:
                    totaldifffiles_files.append(entry.basename)
                if entry.mtr_diffs.count_of_big_diff > 0:
                    numbigdiffs += 1
                    numbigdiffs_.append(["%s: %s" % (entry.basename, "mtr")])
                    if entry.basename not in numbigdiffs_files:
                        numbigdiffs_files.append(entry.basename)
                elif entry.mtr_diffs.count_of_small_diff > 0:
                    numsmalldiffs += 1
                    numsmalldiffs_.append(["%s: %s" % (entry.basename, "mtr")])
                    if entry.basename not in numsmalldiffs_files:
                        numsmalldiffs_files.append(entry.basename)
            if entry.has_zsz_diffs:
                totaldifffiles += 1
                totaldifffiles_.append(["%s: zsz" % entry.basename])
                if entry.basename not in totaldifffiles_files:
                    totaldifffiles_files.append(entry.basename)
                if entry.zsz_diffs.count_of_big_diff > 0:
                    numbigdiffs += 1
                    numbigdiffs_.append(["%s: %s" % (entry.basename, "zsz")])
                    if entry.basename not in numbigdiffs_files:
                        numbigdiffs_files.append(entry.basename)
                elif entry.zsz_diffs.count_of_small_diff > 0:
                    numsmalldiffs += 1
                    numsmalldiffs_.append(["%s: %s" % (entry.basename, "zsz")])
                    if entry.basename not in numsmalldiffs_files:
                        numsmalldiffs_files.append(entry.basename)
            if entry.has_ssz_diffs:
                totaldifffiles += 1
                totaldifffiles_.append(["%s: ssz" % entry.basename])
                if entry.basename not in totaldifffiles_files:
                    totaldifffiles_files.append(entry.basename)
                if entry.ssz_diffs.count_of_big_diff > 0:
                    numbigdiffs += 1
                    numbigdiffs_.append(["%s: %s" % (entry.basename, "ssz")])
                    if entry.basename not in numbigdiffs_files:
                        numbigdiffs_files.append(entry.basename)
                elif entry.ssz_diffs.count_of_small_diff > 0:
                    numsmalldiffs += 1
                    numsmalldiffs_.append(["%s: %s" % (entry.basename, "ssz")])
                    if entry.basename not in numsmalldiffs_files:
                        numsmalldiffs_files.append(entry.basename)
            if entry.has_table_diffs:
                totaldifffiles += 1
                totaldifffiles_.append(["%s: table" % entry.basename])
                if entry.basename not in totaldifffiles_files:
                    totaldifffiles_files.append(entry.basename)
                if entry.table_diffs.bigdiff_count > 0:
                    numtablebigdiffs += 1
                    numtablebigdiffs_.append(["%s: %s" % (entry.basename, "table")])
                    if entry.basename not in numbigdiffs_files:
                        numtablebigdiffs_files.append(entry.basename)
                elif entry.table_diffs.smalldiff_count > 0:
                    numtablesmalldiffs += 1
                    numtablesmalldiffs_.append(["%s: %s" % (entry.basename, "table")])
                    if entry.basename not in numsmalldiffs_files:
                        numtablesmalldiffs_files.append(entry.basename)
            if entry.has_aud_diffs:
                totaldifffiles += 1
                totaldifffiles_.append(["%s: audit" % entry.basename])
                if entry.aud_diffs.diff_type != TextDifferences.EQUAL:
                    if entry.basename not in totaldifffiles_files:
                        totaldifffiles_files.append(entry.basename)
                    numtextdiffs += 1
                    numtextdiffs_.append(["%s: %s" % (entry.basename, "audit")])
                    if entry.basename not in numtextdiffs_files:
                        numtextdiffs_files.append(entry.basename)
            if entry.has_bnd_diffs:
                totaldifffiles += 1
                totaldifffiles_.append(["%s: bnd" % entry.basename])
                if entry.bnd_diffs.diff_type != TextDifferences.EQUAL:
                    if entry.basename not in totaldifffiles_files:
                        totaldifffiles_files.append(entry.basename)
                    numtextdiffs += 1
                    numtextdiffs_.append(["%s: %s" % (entry.basename, "bnd")])
                    if entry.basename not in numtextdiffs_files:
                        numtextdiffs_files.append(entry.basename)
            if entry.has_dxf_diffs:
                totaldifffiles += 1
                totaldifffiles_.append(["%s: dxf" % entry.basename])
                if entry.dxf_diffs.diff_type != TextDifferences.EQUAL:
                    if entry.basename not in totaldifffiles_files:
                        totaldifffiles_files.append(entry.basename)
                    numtextdiffs += 1
                    numtextdiffs_.append(["%s: %s" % (entry.basename, "dxf")])
                    if entry.basename not in numtextdiffs_files:
                        numtextdiffs_files.append(entry.basename)
            if entry.has_eio_diffs:
                totaldifffiles += 1
                totaldifffiles_.append(["%s: eio" % entry.basename])
                if entry.eio_diffs.diff_type != TextDifferences.EQUAL:
                    if entry.basename not in totaldifffiles_files:
                        totaldifffiles_files.append(entry.basename)
                    numtextdiffs += 1
                    numtextdiffs_.append(["%s: %s" % (entry.basename, "eio")])
                    if entry.basename not in numtextdiffs_files:
                        numtextdiffs_files.append(entry.basename)
            if entry.has_mdd_diffs:
                totaldifffiles += 1
                totaldifffiles_.append(["%s: mdd" % entry.basename])
                if entry.mdd_diffs.diff_type != TextDifferences.EQUAL:
                    if entry.basename not in totaldifffiles_files:
                        totaldifffiles_files.append(entry.basename)
                    numtextdiffs += 1
                    numtextdiffs_.append(["%s: %s" % (entry.basename, "mdd")])
                    if entry.basename not in numtextdiffs_files:
                        numtextdiffs_files.append(entry.basename)
            if entry.has_mtd_diffs:
                totaldifffiles += 1
                totaldifffiles_.append(["%s: mtd" % entry.basename])
                if entry.mtd_diffs.diff_type != TextDifferences.EQUAL:
                    if entry.basename not in totaldifffiles_files:
                        totaldifffiles_files.append(entry.basename)
                    numtextdiffs += 1
                    numtextdiffs_.append(["%s: %s" % (entry.basename, "mtd")])
                    if entry.basename not in numtextdiffs_files:
                        numtextdiffs_files.append(entry.basename)
            if entry.has_rdd_diffs:
                totaldifffiles += 1
                totaldifffiles_.append(["%s: rdd" % entry.basename])
                if entry.rdd_diffs.diff_type != TextDifferences.EQUAL:
                    if entry.basename not in totaldifffiles_files:
                        totaldifffiles_files.append(entry.basename)
                    numtextdiffs += 1
                    numtextdiffs_.append(["%s: %s" % (entry.basename, "rdd")])
                    if entry.basename not in numtextdiffs_files:
                        numtextdiffs_files.append(entry.basename)
            if entry.has_shd_diffs:
                totaldifffiles += 1
                totaldifffiles_.append(["%s: shd" % entry.basename])
                if entry.shd_diffs.diff_type != TextDifferences.EQUAL:
                    if entry.basename not in totaldifffiles_files:
                        totaldifffiles_files.append(entry.basename)
                    numtextdiffs += 1
                    numtextdiffs_.append(["%s: %s" % (entry.basename, "shd")])
                    if entry.basename not in numtextdiffs_files:
                        numtextdiffs_files.append(entry.basename)
            if entry.has_err_diffs:
                totaldifffiles += 1
                totaldifffiles_.append(["%s: err" % entry.basename])
                if entry.err_diffs.diff_type != TextDifferences.EQUAL:
                    if entry.basename not in totaldifffiles_files:
                        totaldifffiles_files.append(entry.basename)
                    numtextdiffs += 1
                    numtextdiffs_.append(["%s: %s" % (entry.basename, "err")])
                    if entry.basename not in numtextdiffs_files:
                        numtextdiffs_files.append(entry.basename)
            if entry.has_dlin_diffs:
                totaldifffiles += 1
                totaldifffiles_.append(["%s: delightin" % entry.basename])
                if entry.dlin_diffs.diff_type != TextDifferences.EQUAL:
                    if entry.basename not in totaldifffiles_files:
                        totaldifffiles_files.append(entry.basename)
                    numtextdiffs += 1
                    numtextdiffs_.append(["%s: %s" % (entry.basename, "delightin")])
                    if entry.basename not in numtextdiffs_files:
                        numtextdiffs_files.append(entry.basename)
            if entry.has_dlout_diffs:
                totaldifffiles += 1
                totaldifffiles_.append(["%s: delightout" % entry.basename])
                if entry.dlout_diffs.diff_type != TextDifferences.EQUAL:
                    if entry.basename not in totaldifffiles_files:
                        totaldifffiles_files.append(entry.basename)
                    numtextdiffs += 1
                    numtextdiffs_.append(["%s: %s" % (entry.basename, "delightout")])
                    if entry.basename not in numtextdiffs_files:
                        numtextdiffs_files.append(entry.basename)

        self.results_lists_to_copy = []

        if self.resultschild_numrun:
            self.resultsliststore.remove(self.resultschild_numrun)
        self.resultschild_numrun = self.resultsliststore.append(self.resultsparent_numrun, [str(totalnum)])
        this_path = self.resultsliststore.get_path(self.resultsparent_numrun)
        self.tree_view.expand_row(this_path, False)
        for result in totalnum_:
            self.resultsliststore.append(self.resultschild_numrun, result)
        self.results_lists_to_copy.append(totalnum_files)

        if self.resultschild_success:
            self.resultsliststore.remove(self.resultschild_success)
        self.resultschild_success = self.resultsliststore.append(self.resultsparent_success, [str(numsuccess)])
        this_path = self.resultsliststore.get_path(self.resultsparent_success)
        self.tree_view.expand_row(this_path, False)
        for result in numsuccess_:
            self.resultsliststore.append(self.resultschild_success, result)
        self.results_lists_to_copy.append(numsuccess_files)

        if self.resultschild_unsuccess:
            self.resultsliststore.remove(self.resultschild_unsuccess)
        self.resultschild_unsuccess = self.resultsliststore.append(self.resultsparent_unsuccess, [str(numnotsuccess)])
        this_path = self.resultsliststore.get_path(self.resultsparent_unsuccess)
        self.tree_view.expand_row(this_path, False)
        for result in numnotsuccess_:
            self.resultsliststore.append(self.resultschild_unsuccess, result)
        self.results_lists_to_copy.append(numnotsuccess_files)

        if self.resultschild_success2:
            self.resultsliststore.remove(self.resultschild_success2)
        self.resultschild_success2 = self.resultsliststore.append(self.resultsparent_success2, [str(numsuccess2)])
        this_path = self.resultsliststore.get_path(self.resultsparent_success2)
        self.tree_view.expand_row(this_path, False)
        for result in numsuccess2_:
            self.resultsliststore.append(self.resultschild_success2, result)
        self.results_lists_to_copy.append(numsuccess2_files)

        if self.resultschild_unsuccess2:
            self.resultsliststore.remove(self.resultschild_unsuccess2)
        self.resultschild_unsuccess2 = self.resultsliststore.append(self.resultsparent_unsuccess2,
                                                                    [str(numnotsuccess2)])
        this_path = self.resultsliststore.get_path(self.resultsparent_unsuccess2)
        self.tree_view.expand_row(this_path, False)
        for result in numnotsuccess2_:
            self.resultsliststore.append(self.resultschild_unsuccess2, result)
        self.results_lists_to_copy.append(numnotsuccess2_files)

        if self.resultschild_filescompared:
            self.resultsliststore.remove(self.resultschild_filescompared)
        self.resultschild_filescompared = self.resultsliststore.append(self.resultsparent_filescompared,
                                                                       [str(totaldifffiles)])
        this_path = self.resultsliststore.get_path(self.resultsparent_filescompared)
        self.tree_view.expand_row(this_path, False)
        for result in totaldifffiles_:
            self.resultsliststore.append(self.resultschild_filescompared, result)
        self.results_lists_to_copy.append(totaldifffiles_files)

        if self.resultschild_bigmath:
            self.resultsliststore.remove(self.resultschild_bigmath)
        self.resultschild_bigmath = self.resultsliststore.append(self.resultsparent_bigmath, [str(numbigdiffs)])
        this_path = self.resultsliststore.get_path(self.resultsparent_bigmath)
        self.tree_view.expand_row(this_path, False)
        for result in numbigdiffs_:
            self.resultsliststore.append(self.resultschild_bigmath, result)
        self.results_lists_to_copy.append(numbigdiffs_files)

        if self.resultschild_smallmath:
            self.resultsliststore.remove(self.resultschild_smallmath)
        self.resultschild_smallmath = self.resultsliststore.append(self.resultsparent_smallmath, [str(numsmalldiffs)])
        this_path = self.resultsliststore.get_path(self.resultsparent_smallmath)
        self.tree_view.expand_row(this_path, False)
        for result in numsmalldiffs_:
            self.resultsliststore.append(self.resultschild_smallmath, result)
        self.results_lists_to_copy.append(numsmalldiffs_files)

        if self.resultschild_bigtable:
            self.resultsliststore.remove(self.resultschild_bigtable)
        self.resultschild_bigtable = self.resultsliststore.append(self.resultsparent_bigtable, [str(numtablebigdiffs)])
        this_path = self.resultsliststore.get_path(self.resultsparent_bigtable)
        self.tree_view.expand_row(this_path, False)
        for result in numtablebigdiffs_:
            self.resultsliststore.append(self.resultschild_bigtable, result)
        self.results_lists_to_copy.append(numtablebigdiffs_files)

        if self.resultschild_smalltable:
            self.resultsliststore.remove(self.resultschild_smalltable)
        self.resultschild_smalltable = self.resultsliststore.append(self.resultsparent_smalltable,
                                                                    [str(numtablesmalldiffs)])
        this_path = self.resultsliststore.get_path(self.resultsparent_smalltable)
        self.tree_view.expand_row(this_path, False)
        for result in numtablesmalldiffs_:
            self.resultsliststore.append(self.resultschild_smalltable, result)
        self.results_lists_to_copy.append(numtablesmalldiffs_files)

        if self.resultschild_textual:
            self.resultsliststore.remove(self.resultschild_textual)
        self.resultschild_textual = self.resultsliststore.append(self.resultsparent_textual, [str(numtextdiffs)])
        this_path = self.resultsliststore.get_path(self.resultsparent_textual)
        self.tree_view.expand_row(this_path, False)
        for result in numtextdiffs_:
            self.resultsliststore.append(self.resultschild_textual, result)
        self.results_lists_to_copy.append(numtextdiffs_files)

        if self.do_runtime_report:
            try:
                import csv
                with open(self.runtime_report_file, "w") as csvfile:
                    writer = csv.writer(csvfile)
                    writer.writerow(["Case", "Runtime [s]", "Runtime [s]"])
                    for entry in results:
                        runtime1 = -1
                        runtime2 = -1
                        if entry.has_summary_result:
                            this_summary = entry.summary_result
                            if this_summary.simulation_status_case1 == EndErrSummary.STATUS_SUCCESS:
                                runtime1 = this_summary.run_time_seconds_case1
                            if this_summary.simulation_status_case2 == EndErrSummary.STATUS_SUCCESS:
                                runtime2 = this_summary.run_time_seconds_case2
                        writer.writerow([entry.basename, runtime1, runtime2])
            except Exception as exc:
                self.add_log_entry("Couldn't write runtime report file")
                print(exc)

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


# once done doing any preliminary processing, actually run the application
main_window = PyApp()
Gtk.main()
