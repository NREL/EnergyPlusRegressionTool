#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import glob
import json
import os
import sys
from datetime import datetime

# add the root of the repo to the python path so it can find things relative to it
# like the energyplus_regressions package
from os.path import dirname, realpath

sys.path.append(os.path.join(dirname(realpath(__file__)), '..', '..'))

from energyplus_regressions.builds.install import EPlusInstallDirectory
from energyplus_regressions.runtests import SuiteRunner, TestRunConfiguration
from energyplus_regressions.structures import ForceRunType, ReportingFreq, TextDifferences, TestEntry


def get_diff_files(out_dir):
    files = glob.glob(os.path.join(out_dir, "*.*.*"))
    return files


def cleanup(out_dir):
    for this_file in get_diff_files(out_dir):
        os.remove(this_file)


def print_message(msg):
    print("[decent_ci:test_result:message] " + msg)


def process_diffs(diff_name, diffs, this_has_diffs, this_has_small_diffs):
    if not diffs:
        return this_has_diffs, this_has_small_diffs
    if diffs.diff_type == 'Big Diffs':
        this_has_diffs = True
        print_message(diff_name + " big diffs.")
    elif diffs.diff_type == 'Small Diffs':
        this_has_small_diffs = True
        print_message(diff_name + " small diffs.")
    return this_has_diffs, this_has_small_diffs


def main_function(file_name, base_dir, mod_dir, base_sha, mod_sha, make_public, device_id, test_mode):
    print("Device id: %s" % device_id)

    # build type really doesn't matter, so use the simplest one, the E+ install
    base = EPlusInstallDirectory()
    base.set_build_directory(base_dir)
    base.run = False
    mod = EPlusInstallDirectory()
    mod.set_build_directory(mod_dir)
    mod.run = False

    run_config = TestRunConfiguration(
        force_run_type=ForceRunType.NONE,
        single_test_run=True,
        num_threads=1,
        report_freq=ReportingFreq.HOURLY,
        build_a=base,
        build_b=mod
    )

    print("Comparing `{0}` with `{1}`".format(base_dir, mod_dir))

    initial_entry = TestEntry(file_name, "")
    runner = SuiteRunner(run_config, [])

    cleanup(mod_dir)
    entry, message = runner.process_diffs_for_one_case(
        initial_entry,
        runner.build_tree_a,
        runner.build_tree_b,
        runner.test_output_dir,
        runner.thresh_dict_file,
        ci_mode=True
    )  # returns an updated entry

    with open('results.json', 'w') as f:
        f.write(json.dumps(entry.to_dict(), indent=4))

    success = True
    has_diffs = False
    has_small_diffs = False

    # Note, comment out any of the "has_diffs" below if you don't want
    # it to generate an error condition

    if entry.aud_diffs and (entry.aud_diffs.diff_type != TextDifferences.EQUAL):
        has_small_diffs = True
        print_message("AUD diffs.")

    if entry.bnd_diffs and (entry.bnd_diffs.diff_type != TextDifferences.EQUAL):
        has_small_diffs = True
        print_message("BND diffs.")

    if entry.dl_in_diffs and (entry.dl_in_diffs.diff_type != TextDifferences.EQUAL):
        has_small_diffs = True
        print_message("delightin diffs.")

    if entry.dl_out_diffs and (entry.dl_out_diffs.diff_type != TextDifferences.EQUAL):
        has_small_diffs = True
        print_message("delightout diffs.")

    if entry.dxf_diffs and (entry.dxf_diffs.diff_type != TextDifferences.EQUAL):
        has_small_diffs = True
        print_message("DXF diffs.")

    if entry.eio_diffs and (entry.eio_diffs.diff_type != TextDifferences.EQUAL):
        has_small_diffs = True
        print_message("EIO diffs.")

    if entry.err_diffs and (entry.err_diffs.diff_type != TextDifferences.EQUAL):
        has_small_diffs = True
        print_message("ERR diffs.")

    if entry.readvars_audit_diffs and (entry.readvars_audit_diffs.diff_type != TextDifferences.EQUAL):
        has_small_diffs = True
        print_message("ReadvarsAudit diffs.")

    if entry.edd_diffs and (entry.edd_diffs.diff_type != TextDifferences.EQUAL):
        has_small_diffs = True
        print_message("EDD diffs.")

    if entry.wrl_diffs and (entry.wrl_diffs.diff_type != TextDifferences.EQUAL):
        has_small_diffs = True
        print_message("WRL diffs.")

    if entry.sln_diffs and (entry.sln_diffs.diff_type != TextDifferences.EQUAL):
        has_small_diffs = True
        print_message("SLN diffs.")

    if entry.sci_diffs and (entry.sci_diffs.diff_type != TextDifferences.EQUAL):
        has_small_diffs = True
        print_message("SCI diffs.")

    if entry.map_diffs and (entry.map_diffs.diff_type != TextDifferences.EQUAL):
        has_small_diffs = True
        print_message("MAP diffs.")

    if entry.dfs_diffs and (entry.dfs_diffs.diff_type != TextDifferences.EQUAL):
        has_small_diffs = True
        print_message("DFS diffs.")

    if entry.screen_diffs and (entry.screen_diffs.diff_type != TextDifferences.EQUAL):
        has_small_diffs = True
        print_message("SCREEN diffs.")

    if entry.glhe_diffs and (entry.glhe_diffs.diff_type != TextDifferences.EQUAL):
        has_small_diffs = True
        print_message("GLHE diffs")

    # numeric diff
    if entry.eso_diffs:
        has_diffs, has_small_diffs = process_diffs("ESO", entry.eso_diffs, has_diffs, has_small_diffs)

    if entry.mdd_diffs and (entry.mdd_diffs.diff_type != TextDifferences.EQUAL):
        has_small_diffs = True
        print_message("MDD diffs.")

    if entry.mtd_diffs and (entry.mtd_diffs.diff_type != TextDifferences.EQUAL):
        has_small_diffs = True
        print_message("MTD diffs.")

    # numeric diff
    if entry.mtr_diffs:
        has_diffs, has_small_diffs = process_diffs("MTR", entry.mtr_diffs, has_diffs, has_small_diffs)

    if entry.rdd_diffs and (entry.rdd_diffs.diff_type != TextDifferences.EQUAL):
        has_small_diffs = True
        print_message("RDD diffs.")

    if entry.shd_diffs and (entry.shd_diffs.diff_type != TextDifferences.EQUAL):
        has_small_diffs = True
        print_message("SHD diffs.")

    if entry.perf_log_diffs and (entry.perf_log_diffs.diff_type != TextDifferences.EQUAL):
        has_small_diffs = True
        print_message("PERF_LOG diffs.")

    # numeric diff
    if entry.ssz_diffs:
        has_diffs, has_small_diffs = process_diffs("SSZ", entry.ssz_diffs, has_diffs, has_small_diffs)

    # numeric diff
    if entry.zsz_diffs:
        has_diffs, has_small_diffs = process_diffs("ZSZ", entry.zsz_diffs, has_diffs, has_small_diffs)

    # numeric diff
    if entry.json_diffs:
        has_diffs, has_small_diffs = process_diffs("JSON", entry.json_diffs, has_diffs, has_small_diffs)

    if entry.table_diffs:
        if entry.table_diffs.big_diff_count > 0:
            has_diffs = True
            print_message("Table big diffs.")
        elif entry.table_diffs.small_diff_count > 0:
            has_small_diffs = True
            print_message("Table small diffs.")

    if entry.idf_diffs and (entry.idf_diffs.diff_type != TextDifferences.EQUAL):
        has_small_diffs = True
        print_message("IDF diffs.")

    if entry.stdout_diffs and (entry.stdout_diffs.diff_type != TextDifferences.EQUAL):
        has_small_diffs = True
        print_message("StdOut diffs.")

    if entry.stderr_diffs and (entry.stderr_diffs.diff_type != TextDifferences.EQUAL):
        has_small_diffs = True
        print_message("StdErr diffs.")

    if has_small_diffs:
        print("[decent_ci:test_result:warn]")

    if test_mode:
        print("Skipping Amazon upload in test_mode operation")
    elif has_small_diffs or has_diffs:  # pragma: no cover -- not testing the Amazon upload anytime soon
        import boto

        # so ... if you want to run tests of this script including the Amazon side, you need to pass in Amazon creds
        # to the boto connect_s3 method.  To run this test, put the amazon key and secret in a file, one per line.
        # Uncomment the next two lines, and change the first so that the path points to the credentials file.
        # Comment the empty connect_s3 call below it.  Then go to the test_main_function_not_test_mode() unit test and
        # enable it (disable skipping it).  Then it should run completely, posting fake but good results to an Amazon
        # bucket, making them public, and reporting the URL in the output

        # file_data = open('/path/to/s3/creds.txt').read().split('\n')
        # conn = boto.connect_s3(file_data[0], file_data[1])
        conn = boto.connect_s3()
        bucket_name = 'energyplus'
        bucket = conn.get_bucket(bucket_name)

        potential_files = get_diff_files(base_dir)

        date = datetime.now()
        date_str = "%d-%02d" % (date.year, date.month)
        file_dir = "regressions/{0}/{1}-{2}/{3}/{4}".format(date_str, base_sha, mod_sha, file_name, device_id)

        found_files = []
        for filename in potential_files:
            file_path_to_send = filename

            # print("Processing output file: {0}".format(filepath_to_send))
            if not os.path.isfile(file_path_to_send):
                continue
            if not os.stat(file_path_to_send).st_size > 0:
                print("File is empty, not sending: {0}".format(file_path_to_send))
                continue

            try:
                file_path = "{0}/{1}".format(file_dir, os.path.basename(filename))
                # print("Processing output file: {0}, uploading to: {1}".format(filepath_to_send, filepath))

                key = boto.s3.key.Key(bucket, file_path)
                with open(file_path_to_send, 'r') as file_to_send:
                    contents = file_to_send.read()
                    key.set_contents_from_string(contents)

                    if make_public:
                        key.make_public()

                    htmlkey = boto.s3.key.Key(bucket, file_path + ".html")

                    if file_path_to_send.endswith('.htm'):
                        htmlkey.set_contents_from_string(
                            contents,
                            headers={"Content-Type": "text/html", "Content-Disposition": "inline"}
                        )
                    else:
                        htmlkey.set_contents_from_string(
                            """
<!doctype html>
<html>
  <head>
     <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.6.0/styles/default.min.css">
      <script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.6.0/highlight.min.js"></script>
      <script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.6.0/languages/diff.min.js"></script>
  </head>
  <body>
    <pre><code class="diff">
""" + contents + """
    </code></pre>
    <script>hljs.highlightAll();</script>
  </body>
</html>
                            """,
                            headers={"Content-Type": "text/html"}
                        )

                if make_public:
                    htmlkey.make_public()

                found_files.append(filename)
            except Exception as e:
                success = False
                print("There was a problem processing file: %s" % e)

        if len(found_files) > 0:
            try:
                htmlkey = boto.s3.key.Key(bucket, file_dir + "/index.html")
                index = """
<!doctype html>
<html>
  <head>
    <!-- Latest compiled and minified CSS -->
    <link rel="stylesheet" href="//netdna.bootstrapcdn.com/bootstrap/3.1.1/css/bootstrap.min.css">

    <!-- Optional theme -->
    <link rel="stylesheet" href="//netdna.bootstrapcdn.com/bootstrap/3.1.1/css/bootstrap-theme.min.css">

    <!-- Latest compiled and minified JavaScript -->
    <script src="//netdna.bootstrapcdn.com/bootstrap/3.1.1/js/bootstrap.min.js"></script>

    <script src="//code.jquery.com/jquery-2.1.1.min.js"></script>
    <script src="//code.jquery.com/jquery-migrate-1.2.1.min.js"></script>
  </head>
  <body>

    <table class='table table-hover'>
      <tr><th>filename</th><th></th><th></th></tr>
                              """

                for filename in found_files:
                    filepath = "{0}/{1}".format(file_dir, os.path.basename(filename))
                    index += "<tr><td>"
                    index += os.path.basename(filename)
                    index += "</td><td><a href='/"
                    index += filepath
                    index += "'>download</a></td><td><a href='/"
                    index += filepath
                    index += ".html'>view</a></td></tr>"

                index += """
    </table>
  </body>
</html>
                        """

                htmlkey.set_contents_from_string(index, headers={"Content-Type": "text/html"})

                if make_public:
                    htmlkey.make_public()

                url = "http://{0}.s3-website-{1}.amazonaws.com/{2}".format(bucket_name, "us-east-1", file_dir)
                print("<a href='{0}'>Regression Results</a>".format(url))
            except Exception as e:
                success = False
                print("There was a problem generating results webpage: %s" % e)

    if success and not has_diffs:
        print("Success")


if __name__ == "__main__":  # pragma: no cover - testing function, not the __main__ entry point

    if len(sys.argv) < 8:
        print("syntax: %s file_name base_dir mod_dir base_sha mod_sha make_public device_id [test]" % sys.argv[0])
        sys.exit(1)

    arg_file_name = sys.argv[1]
    arg_base_dir = sys.argv[2]
    arg_mod_dir = sys.argv[3]
    arg_base_sha = sys.argv[4]
    arg_mod_sha = sys.argv[5]
    arg_make_public = sys.argv[6].lower() == "true".lower()
    arg_device_id = sys.argv[7]
    _test_mode = False
    if len(sys.argv) > 8 and sys.argv[8].upper() == 'TEST':
        _test_mode = True
    main_function(
        arg_file_name, arg_base_dir, arg_mod_dir, arg_base_sha, arg_mod_sha, arg_make_public, arg_device_id, _test_mode
    )
