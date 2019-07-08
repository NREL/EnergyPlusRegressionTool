import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk

from epregressions.structures import CompletedStructure, TestEntry, EndErrSummary


class ResultsTreeRoots:
    # probably refactor this elsewhere but it's a start
    NumRun = "Cases run:"
    Success1 = "Case 1 Successful runs:"
    NotSuccess1 = "Case 1 Unsuccessful run:"
    Success2 = "Case 2 Successful runs:"
    NotSuccess2 = "Case 2 Unsuccessful run:"
    FilesCompared = "Files compared:"
    BigMath = "Files with BIG mathdiffs:"
    SmallMath = "Files with small mathdiffs:"
    BigTable = "Files with BIG tablediffs:"
    SmallTable = "Files with small tablediffs:"
    Textual = "Files with textual diffs:"

    @staticmethod
    def list_all():
        return [
            ResultsTreeRoots.NumRun,
            ResultsTreeRoots.Success1,
            ResultsTreeRoots.NotSuccess1,
            ResultsTreeRoots.Success2,
            ResultsTreeRoots.NotSuccess2,
            ResultsTreeRoots.FilesCompared,
            ResultsTreeRoots.BigMath,
            ResultsTreeRoots.SmallMath,
            ResultsTreeRoots.BigTable,
            ResultsTreeRoots.SmallTable,
            ResultsTreeRoots.Textual
        ]


class MyWindow(Gtk.Window):

    def __init__(self):
        Gtk.Window.__init__(self, title="Hello World")

        self.box = Gtk.Box(spacing=6)
        self.add(self.box)

        self.button1 = Gtk.Button(label="Add Contents to Tree")
        self.button1.connect("clicked", self.on_button1_clicked)
        self.box.pack_start(self.button1, True, True, 0)

        self.results_list_store = Gtk.TreeStore(str)
        self.results_parent = {}
        self.results_child = {}
        for parent_root in ResultsTreeRoots.list_all():
            self.results_parent[parent_root] = self.results_list_store.append(None, [parent_root])
            self.results_child[parent_root] = None

        self.tree_view = Gtk.TreeView(model=self.results_list_store)
        tree_view_column = Gtk.TreeViewColumn('Results Summary')

        cell = Gtk.CellRendererText()
        tree_view_column.pack_start(cell, True)
        tree_view_column.add_attribute(cell, 'text', 0)
        self.tree_view.append_column(tree_view_column)

        self.box.pack_start(self.tree_view, True, True, 0)

    def on_button1_clicked(self, widget):
        results = CompletedStructure('/a/', '/b/', '/c/', '/d/', '/e/')
        this_entry = TestEntry('file.idf', 'file.epw')
        this_entry.add_summary_result(
            EndErrSummary(
                EndErrSummary.STATUS_SUCCESS,
                1,
                EndErrSummary.STATUS_SUCCESS,
                2
            ))
        results.add_test_entry(this_entry)
        root_and_files = {
            ResultsTreeRoots.NumRun: results.all_files,
            ResultsTreeRoots.Success1: results.success_case_a,
            ResultsTreeRoots.NotSuccess1: results.failure_case_a,
            ResultsTreeRoots.Success2: results.success_case_b,
            ResultsTreeRoots.NotSuccess2: results.failure_case_b,
            ResultsTreeRoots.FilesCompared: results.total_files_compared,
            ResultsTreeRoots.BigMath: results.big_math_diffs,
            ResultsTreeRoots.SmallMath: results.small_math_diffs,
            ResultsTreeRoots.BigTable: results.big_table_diffs,
            ResultsTreeRoots.SmallTable: results.small_table_diffs,
            ResultsTreeRoots.Textual: results.text_diffs
        }
        for tree_root in root_and_files:
            file_lists = root_and_files[tree_root]
            this_file_list_count = len(file_lists.descriptions)
            if self.results_child[tree_root]:  # pragma: no cover - I'd try to test this if the tree was its own class
                self.results_list_store.remove(self.results_child[tree_root])
            self.results_child[tree_root] = self.results_list_store.append(
                self.results_parent[tree_root],
                [str(this_file_list_count)]
            )
            this_path = self.results_list_store.get_path(self.results_parent[tree_root])
            self.tree_view.expand_row(this_path, False)
            for result in file_lists.descriptions:  # pragma: no cover
                self.results_list_store.append(self.results_child[tree_root], [result])


win = MyWindow()
win.connect("destroy", Gtk.main_quit)
win.show_all()
Gtk.main()
