class ForceRunType:
    DD = "A"
    ANNUAL = "B"
    NONE = "C"


class ReportingFreq:
    DETAILED = "Detailed"
    TIME_STEP = "Timestep"
    HOURLY = "Hourly"
    DAILY = "Daily"
    MONTHLY = "Monthly"
    RUN_PERIOD = "RunPeriod"
    ENVIRONMENT = "Environment"
    ANNUAL = "Annual"


class SingleCaseInformation:
    def __init__(self, source_directory, build_directory, run_this_directory):
        self.source_directory = source_directory
        self.build_directory = build_directory
        self.run = run_this_directory

    def establish_dir_struc(self, somethings):  # TODO: Make this usable!
        pass


class TestRunConfiguration:
    def __init__(self, run_math_diff, do_composite_err, force_run_type, single_test_run, num_threads,
                 report_freq, build_a, build_b=None):
        self.MathDiff = run_math_diff
        self.CompositeErr = do_composite_err
        self.force_run_type = force_run_type
        self.TestOneFile = single_test_run
        self.num_threads = num_threads
        self.buildA = build_a
        self.buildB = build_b
        self.report_freq = report_freq


class ResultsLists:
    def __init__(self):
        self.descriptions = []
        self.base_names = set()


class CompletedStructure:
    def __init__(self):
        # results by file
        self.entries_by_file = []
        # results by type
        self.all_files = ResultsLists()
        self.success_case_a = ResultsLists()
        self.failure_case_a = ResultsLists()
        self.success_case_b = ResultsLists()
        self.failure_case_b = ResultsLists()
        self.total_files_compared = ResultsLists()
        self.big_math_diffs = ResultsLists()
        self.small_math_diffs = ResultsLists()
        self.big_table_diffs = ResultsLists()
        self.small_table_diffs = ResultsLists()
        self.text_diffs = ResultsLists()

    def add_test_entry(self, this_entry):
        self.entries_by_file.append(this_entry)
        # always add the current entry because it was tested
        self.all_files.descriptions.append("%s" % this_entry.basename)
        self.all_files.base_names.add(this_entry.basename)

        # add the entry to the appropriate success/failure bins
        if this_entry.summary_result.simulation_status_case1 == EndErrSummary.STATUS_SUCCESS:
            self.success_case_a.descriptions.append("%s" % this_entry.basename)
            self.success_case_a.base_names.add(this_entry.basename)
        else:
            self.failure_case_a.descriptions.append("%s" % this_entry.basename)
            self.failure_case_a.base_names.add(this_entry.basename)
        if this_entry.summary_result.simulation_status_case2 == EndErrSummary.STATUS_SUCCESS:
            self.success_case_b.descriptions.append("%s" % this_entry.basename)
            self.success_case_b.base_names.add(this_entry.basename)
        else:
            self.failure_case_b.descriptions.append("%s" % this_entry.basename)
            self.failure_case_b.base_names.add(this_entry.basename)

        # check the math diffs for this entry
        math_diff_hash = {
            this_entry.eso_diffs: "eso",
            this_entry.mtr_diffs: "mtr",
            this_entry.zsz_diffs: "zsz",
            this_entry.ssz_diffs: "ssz"
        }
        for diff in math_diff_hash:
            file_type = math_diff_hash[diff]
            if diff:
                self.total_files_compared.descriptions.append("%s: %s" % (this_entry.basename, file_type))
                self.total_files_compared.base_names.add(this_entry.basename)
                if diff.count_of_big_diff > 0:
                    self.big_math_diffs.descriptions.append("%s: %s" % (this_entry.basename, file_type))
                    self.big_math_diffs.base_names.add(this_entry.basename)
                elif diff.count_of_small_diff > 0:
                    self.small_math_diffs.descriptions.append("%s: %s" % (this_entry.basename, file_type))
                    self.small_math_diffs.base_names.add(this_entry.basename)

        # get tabular diffs
        if this_entry.table_diffs:
            self.total_files_compared.descriptions.append("%s: table" % this_entry.basename)
            self.total_files_compared.base_names.add(this_entry.basename)
            if this_entry.table_diffs.big_diff_count > 0:
                self.big_table_diffs.descriptions.append("%s: %s" % (this_entry.basename, "table"))
                self.big_table_diffs.base_names.add(this_entry.basename)
            elif this_entry.table_diffs.small_diff_count > 0:
                self.small_table_diffs.descriptions.append("%s: %s" % (this_entry.basename, "table"))
                self.small_table_diffs.base_names.add(this_entry.basename)

        # check the textual diffs
        text_diff_hash = {
            this_entry.aud_diffs: "audit",
            this_entry.bnd_diffs: "bnd",
            this_entry.dxf_diffs: "dxf",
            this_entry.eio_diffs: "eio",
            this_entry.mdd_diffs: "mdd",
            this_entry.mtd_diffs: "mtd",
            this_entry.rdd_diffs: "rdd",
            this_entry.shd_diffs: "shd",
            this_entry.err_diffs: "err",
            this_entry.dl_in_diffs: "delightin",
            this_entry.dl_out_diffs: "delightout",
        }
        for diff in text_diff_hash:
            file_type = text_diff_hash[diff]
            if diff:
                self.total_files_compared.descriptions.append("%s: %s" % (this_entry.basename, file_type))
                if diff.diff_type != TextDifferences.EQUAL:
                    self.total_files_compared.base_names.add(this_entry.basename)  # should just use a set()
                    self.text_diffs.descriptions.append("%s: %s" % (this_entry.basename, file_type))
                    self.text_diffs.base_names.add(this_entry.basename)


class TextDifferences:
    # file types
    AUD = 1
    BND = 2
    DXF = 3
    EIO = 4
    ERR = 5
    MDD = 6
    MTD = 7
    RDD = 8
    SHD = 9
    DL_IN = 10
    DL_OUT = 11
    # diff types
    EQUAL = 1
    DIFFS = 2

    def __init__(self, diff_type):
        self.diff_type = diff_type


class MathDifferences:
    ESO = 1
    MTR = 2
    ZSZ = 3
    SSZ = 4

    def __init__(self, args_from_math_diff):
        self.diff_type = args_from_math_diff[0]
        self.num_records = args_from_math_diff[1]
        self.count_of_big_diff = args_from_math_diff[2]
        self.count_of_small_diff = args_from_math_diff[3]


class TableDifferences:
    def __init__(self, args_from_table_diff):
        self.msg = args_from_table_diff[0]
        self.table_count = args_from_table_diff[1]
        self.big_diff_count = args_from_table_diff[2]
        self.small_diff_count = args_from_table_diff[3]
        self.equal_count = args_from_table_diff[4]
        self.string_diff_count = args_from_table_diff[5]
        self.size_err_count = args_from_table_diff[6]
        self.not_in_1_count = args_from_table_diff[7]
        self.not_in_2_count = args_from_table_diff[8]


class EndErrSummary:
    STATUS_UNKNOWN = 1
    STATUS_SUCCESS = 2
    STATUS_FATAL = 3
    STATUS_MISSING = 4

    def __init__(self, status_case1, runtime_seconds_case1, status_case2, runtime_seconds_case2):
        self.simulation_status_case1 = status_case1
        self.run_time_seconds_case1 = runtime_seconds_case1
        self.simulation_status_case2 = status_case2
        self.run_time_seconds_case2 = runtime_seconds_case2


class TestEntry:

    def __init__(self, name, epw):
        self.basename = name
        self.epw = epw
        self.summary_result = None
        self.eso_diffs = None
        self.mtr_diffs = None
        self.zsz_diffs = None
        self.ssz_diffs = None
        self.table_diffs = None
        self.aud_diffs = None
        self.bnd_diffs = None
        self.dxf_diffs = None
        self.eio_diffs = None
        self.err_diffs = None
        self.mdd_diffs = None
        self.mtd_diffs = None
        self.rdd_diffs = None
        self.shd_diffs = None
        self.dl_in_diffs = None
        self.dl_out_diffs = None
        self.runtime_case1 = None
        self.runtime_case2 = None

    def add_summary_result(self, end_err_summary):
        self.summary_result = end_err_summary

    def add_runtime_result(self, runtime_in_seconds_case1, runtime_in_seconds_case2):
        self.runtime_case1 = runtime_in_seconds_case1
        self.runtime_case2 = runtime_in_seconds_case2

    def add_math_differences(self, diffs, diff_type):
        if diff_type == MathDifferences.ESO:
            self.eso_diffs = diffs
        elif diff_type == MathDifferences.MTR:
            self.mtr_diffs = diffs
        elif diff_type == MathDifferences.ZSZ:
            self.zsz_diffs = diffs
        elif diff_type == MathDifferences.SSZ:
            self.ssz_diffs = diffs

    def add_text_differences(self, diffs, diff_type):
        if diff_type == TextDifferences.AUD:
            self.aud_diffs = diffs
        elif diff_type == TextDifferences.BND:
            self.bnd_diffs = diffs
        elif diff_type == TextDifferences.DXF:
            self.dxf_diffs = diffs
        elif diff_type == TextDifferences.EIO:
            self.eio_diffs = diffs
        elif diff_type == TextDifferences.ERR:
            self.err_diffs = diffs
        elif diff_type == TextDifferences.MDD:
            self.mdd_diffs = diffs
        elif diff_type == TextDifferences.MTD:
            self.mtd_diffs = diffs
        elif diff_type == TextDifferences.RDD:
            self.rdd_diffs = diffs
        elif diff_type == TextDifferences.SHD:
            self.shd_diffs = diffs
        elif diff_type == TextDifferences.DL_IN:
            self.dl_in_diffs = diffs
        elif diff_type == TextDifferences.DL_OUT:
            self.dl_out_diffs = diffs

    def add_table_differences(self, diffs):
        self.table_diffs = diffs


class TestCaseCompleted:
    def __init__(self, run_directory, case_name, run_status, error_msg_reported_already, name_of_thread):
        self.run_directory = run_directory
        self.case_name = case_name
        self.run_success = run_status
        self.name_of_thread = name_of_thread
        self.muffle_err_msg = error_msg_reported_already
