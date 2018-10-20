class ForceRunType:
    DD = "A"
    ANNUAL = "B"
    NONE = "C"


class ReportingFreq:
    DETAILED = "Detailed"
    TIMESTEP = "Timestep"
    HOURLY = "Hourly"
    DAILY = "Daily"
    MONTHLY = "Monthly"
    RUNPERIOD = "RunPeriod"
    ENVIRONMENT = "Environment"
    ANNUAL = "Annual"


class SingleCaseInformation:
    def __init__(self, source_directory, build_directory, run_this_directory):
        self.source_directory = source_directory
        self.build_directory = build_directory
        self.run = run_this_directory

    def establish_dir_struc(self, somethings):  # TODO: Is this used?
        pass


class TestRunConfiguration:
    def __init__(self, run_mathdiff, do_composite_err, force_run_type, single_test_run, num_threads,
                 report_freq, build_a, build_b=None):
        self.MathDiff = run_mathdiff
        self.CompositeErr = do_composite_err
        self.force_run_type = force_run_type
        self.TestOneFile = single_test_run
        self.num_threads = num_threads
        self.buildA = build_a
        self.buildB = build_b
        self.report_freq = report_freq


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
    DLIN = 10
    DLOUT = 11
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

    def __init__(self, args_from_mathdiff):
        self.diff_type = args_from_mathdiff[0]
        self.num_records = args_from_mathdiff[1]
        self.count_of_big_diff = args_from_mathdiff[2]
        self.count_of_small_diff = args_from_mathdiff[3]


class TableDifferences:
    def __init__(self, args_from_tablediff):
        self.msg = args_from_tablediff[0]
        self.table_count = args_from_tablediff[1]
        self.bigdiff_count = args_from_tablediff[2]
        self.smalldiff_count = args_from_tablediff[3]
        self.equal_count = args_from_tablediff[4]
        self.stringdiff_count = args_from_tablediff[5]
        self.sizeerr_count = args_from_tablediff[6]
        self.notin1_count = args_from_tablediff[7]
        self.notin2_count = args_from_tablediff[8]


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
        self.dlin_diffs = None
        self.dlout_diffs = None
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
        elif diff_type == TextDifferences.DLIN:
            self.dlin_diffs = diffs
        elif diff_type == TextDifferences.DLOUT:
            self.dlout_diffs = diffs

    def add_table_differences(self, diffs):
        self.table_diffs = diffs


class TestCaseCompleted:
    def __init__(self, run_directory, case_name, run_status, error_msg_reported_already, name_of_thread):
        self.run_directory = run_directory
        self.case_name = case_name
        self.run_success = run_status
        self.name_of_thread = name_of_thread
        self.muffle_err_msg = error_msg_reported_already
