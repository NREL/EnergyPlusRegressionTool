#!/usr/bin/env python

class ForceRunType():
    DD        = "A"
    ANNUAL    = "B"
    NONE      = "C"
    REVERSEDD = "D"

class ReportingFreq():
    DETAILED    = "Detailed"
    TIMESTEP    = "Timestep"
    HOURLY      = "Hourly"
    DAILY       = "Daily"
    MONTHLY     = "Monthly"
    RUNPERIOD   = "RunPeriod"
    ENVIRONMENT = "Environment"
    ANNUAL      = "Annual"
    
class SingleBuildDirectory():    
    def __init__(self, directory_path, executable_name, run_this_directory):
        self.build      = directory_path
        self.executable = executable_name
        self.run        = run_this_directory
    def establish_dir_struc(self, somethings):
        pass

class TestRunConfiguration():    
    def __init__(self, run_mathdiff, do_composite_err, force_run_type, single_test_run, eplus_install_path, num_threads, report_freq, buildA, buildB = None):
        self.MathDiff = run_mathdiff
        self.CompositeErr = do_composite_err
        self.force_run_type = force_run_type
        self.TestOneFile = single_test_run
        self.eplus_install = eplus_install_path
        self.num_threads = num_threads
        self.buildA = buildA
        self.buildB = buildB
        self.report_freq = report_freq

class TextDifferences():
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
        
class MathDifferences():
    ESO = 1
    MTR = 2
    ZSZ = 3
    SSZ = 4    
    def __init__(self, args_from_mathdiff):
        self.diff_type = args_from_mathdiff[0]
        self.num_records = args_from_mathdiff[1]
        self.count_of_big_diff = args_from_mathdiff[2]
        self.count_of_small_diff = args_from_mathdiff[3]
        
class TableDifferences():
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

class EndErrSummary():
    STATUS_UNKNOWN = 1
    STATUS_SUCCESS = 2
    STATUS_FATAL = 3
    STATUS_MISSING = 4
    def __init__(self, status_case1, runtime_seconds_case1, status_case2, runtime_seconds_case2):
        self.simulation_status_case1 = status_case1
        self.run_time_seconds_case1 = runtime_seconds_case1
        self.simulation_status_case2 = status_case2
        self.run_time_seconds_case2 = runtime_seconds_case2
    
class TestEntry():
    
    def __init__(self, name, epw):
        self.basename = name
        self.epw = epw
        self.has_summary_result = False
        self.has_eso_diffs = False
        self.has_mtr_diffs = False
        self.has_zsz_diffs = False
        self.has_ssz_diffs = False
        self.has_table_diffs = False
        self.has_aud_diffs = False
        self.has_bnd_diffs = False
        self.has_dxf_diffs = False
        self.has_eio_diffs = False
        self.has_err_diffs = False
        self.has_mdd_diffs = False
        self.has_mtd_diffs = False
        self.has_rdd_diffs = False
        self.has_shd_diffs = False
        self.has_dlin_diffs = False
        self.has_dlout_diffs = False
        self.has_runtime_result = False
        
    def add_summary_result(self, end_err_summary):
        self.has_summary_result = True
        self.summary_result = end_err_summary
        
    def add_runtime_result(self, runtime_in_seconds_case1, runtime_in_seconds_case2):
        self.has_runtime_result = True
        self.runtime_case1 = runtime_in_seconds_case1
        self.runtime_case2 = runtime_in_seconds_case2
        
    def add_math_differences(self, diffs, diff_type):
        if diff_type == MathDifferences.ESO:
            self.has_eso_diffs = True
            self.eso_diffs = diffs
        elif diff_type == MathDifferences.MTR:
            self.has_mtr_diffs = True
            self.mtr_diffs = diffs
        elif diff_type == MathDifferences.ZSZ:
            self.has_zsz_diffs = True
            self.zsz_diffs = diffs
        elif diff_type == MathDifferences.SSZ:
            self.has_ssz_diffs = True
            self.ssz_diffs = diffs
    
    def add_text_differences(self, diffs, diff_type):
        if diff_type == TextDifferences.AUD:
            self.has_aud_diffs = True
            self.aud_diffs = diffs
        elif diff_type == TextDifferences.BND:
            self.has_bnd_diffs = True
            self.bnd_diffs = diffs
        elif diff_type == TextDifferences.DXF:
            self.has_dxf_diffs = True
            self.dxf_diffs = diffs
        elif diff_type == TextDifferences.EIO:
            self.has_eio_diffs = True
            self.eio_diffs = diffs
        elif diff_type == TextDifferences.ERR:
            self.has_err_diffs = True
            self.err_diffs = diffs
        elif diff_type == TextDifferences.MDD:
            self.has_mdd_diffs = True
            self.mdd_diffs = diffs
        elif diff_type == TextDifferences.MTD:
            self.has_mtd_diffs = True
            self.mtd_diffs = diffs
        elif diff_type == TextDifferences.RDD:
            self.has_rdd_diffs = True
            self.rdd_diffs = diffs
        elif diff_type == TextDifferences.SHD:
            self.has_shd_diffs = True
            self.shd_diffs = diffs
        elif diff_type == TextDifferences.DLIN:
            self.has_dlin_diffs = True
            self.dlin_diffs = diffs
        elif diff_type == TextDifferences.DLOUT:
            self.has_dlout_diffs = True
            self.dlout_diffs = diffs
            
    def add_table_differences(self, diffs):
        self.has_table_diffs = True
        self.table_diffs = diffs

class TestCaseCompleted():
    def __init__(self, run_directory, case_name, run_status, error_msg_reported_already, name_of_thread):
        self.run_directory = run_directory
        self.case_name = case_name
        self.run_success = run_status
        self.name_of_thread = name_of_thread     
        self.muffle_err_msg = error_msg_reported_already
