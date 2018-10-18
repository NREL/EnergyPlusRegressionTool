#!/usr/bin/python
# -*- coding: utf-8 -*- 
from __future__ import unicode_literals

import json
import sys
import os, shutil
import subprocess
import random
import glob

from datetime import datetime
from runtests import *
from Structures import *

# print os.environ

def get_diff_files(outdir):
    files = glob.glob(outdir + "/*.*.*")
    return files

def cleanup(outdir):
    for f in get_diff_files(outdir):
        os.remove(f)

def print_message(msg):
    print("[decent_ci:test_result:message] " + msg)

def process_diffs(diff_name, diffs, has_diffs, has_small_diffs):
    if diffs.diff_type == 'Big Diffs':
        has_diffs = True
        print_message(diff_name + " big diffs.")
    elif diffs.diff_type == 'Small Diffs':
        has_small_diffs = True
        print_message(diff_name + " small diffs.")

    return has_diffs, has_small_diffs;



if len(sys.argv) != 8:
    print("syntax: %s file_name base_dir mod_dir base_sha mod_sha make_public device_id" % sys.argv[0])
    sys.exit(1)


file_name = sys.argv[1]
base_dir = sys.argv[2]
mod_dir = sys.argv[3]
make_public = sys.argv[6].lower() == "true".lower()
device_id = sys.argv[7]

print("Device id: %s" % device_id)

# For ALL runs use BuildA
base   = SingleBuildDirectory(directory_path     = base_dir, 
                              executable_name    = "EnergyPlus", 
                              run_this_directory = False)
# If using ReverseDD, buildB can just be None
mod    = SingleBuildDirectory(directory_path     = mod_dir, 
                              executable_name    = "EnergyPlus", 
                              run_this_directory = False)

RunConfig = TestRunConfiguration(run_mathdiff       = True, 
                                 do_composite_err   = True, 
                                 force_run_type     = ForceRunType.DD, #ANNUAL, DD, NONE, REVERSEDD
                                 single_test_run    = True, 
                                 eplus_install_path = "",
                                 num_threads        = 1,
                                 report_freq        = ReportingFreq.HOURLY,
                                 buildA = base, 
                                 buildB = mod)

print("Comparing `{0}` with `{1}`".format(base_dir, mod_dir))
entry = TestEntry(file_name, "")
runner = TestSuiteRunner(RunConfig, [])

cleanup(mod_dir)
runner.process_diffs_for_one_case(entry, base_dir, mod_dir, mod_dir)

f = open('results.json', 'w')
f.write(json.dumps(entry, default=lambda o: o.__dict__, sort_keys=True, indent=4))

success = True
has_diffs = False
has_small_diffs = False



# Note, comment out any of the "has_diffs" below if you don't want
# it to generate an error condition

if entry.has_aud_diffs and (entry.aud_diffs.diff_type != TextDifferences.EQUAL):
    has_small_diffs = True
    print_message("AUD diffs.")

if entry.has_bnd_diffs and (entry.bnd_diffs.diff_type != TextDifferences.EQUAL):
    has_small_diffs = True
    print_message("BND diffs.")

if entry.has_dlin_diffs and (entry.dlin_diffs.diff_type != TextDifferences.EQUAL):
    has_small_diffs = True
    print_message("delightin diffs.")

if entry.has_dlout_diffs and (entry.dlout_diffs.diff_type != TextDifferences.EQUAL):
    has_small_diffs = True
    print_message("delightout diffs.")

if entry.has_dxf_diffs and (entry.dxf_diffs.diff_type != TextDifferences.EQUAL):
    has_small_diffs = True
    print_message("DXF diffs.")

if entry.has_eio_diffs and (entry.eio_diffs.diff_type != TextDifferences.EQUAL):
    has_small_diffs = True
    print_message("EIO diffs.")

if entry.has_err_diffs and (entry.err_diffs.diff_type != TextDifferences.EQUAL):
    has_small_diffs = True
    print_message("ERR diffs.")

# numeric diff
if entry.has_eso_diffs:
    has_diffs, has_small_diffs = process_diffs("ESO", entry.eso_diffs, has_diffs, has_small_diffs)

if entry.has_mdd_diffs and (entry.mdd_diffs.diff_type != TextDifferences.EQUAL):
    has_small_diffs = True
    print_message("MDD diffs.")

if entry.has_mtd_diffs and (entry.mtd_diffs.diff_type != TextDifferences.EQUAL):
    has_small_diffs = True
    print_message("MTD diffs.")

#numeric diff
if entry.has_mtr_diffs:
    has_diffs, has_small_diffs = process_diffs("MTR", entry.mtr_diffs, has_diffs, has_small_diffs)

if entry.has_rdd_diffs and (entry.rdd_diffs.diff_type != TextDifferences.EQUAL):
    has_small_diffs = True
    print_message("RDD diffs.")

if entry.has_shd_diffs and (entry.shd_diffs.diff_type != TextDifferences.EQUAL):
    has_small_diffs = True
    print_message("SHD diffs.")

#numeric diff
if entry.has_ssz_diffs:
    has_diffs, has_small_diffs = process_diffs("SSZ", entry.ssz_diffs, has_diffs, has_small_diffs)

#numeric diff
if entry.has_zsz_diffs:
    has_diffs, has_small_diffs = process_diffs("ZSZ", entry.zsz_diffs, has_diffs, has_small_diffs)

if entry.has_table_diffs:
    if entry.table_diffs.bigdiff_count > 0:
        has_diffs = True
        print_message("Table big diffs.")
    elif entry.table_diffs.smalldiff_count > 0:
        has_small_diffs = True
        print_message("Table small diffs.")

if has_small_diffs:
    print("[decent_ci:test_result:warn]")

if has_small_diffs or has_diffs:
    import boto
    conn = boto.connect_s3();
    bucketname = 'energyplus'
    bucket = conn.get_bucket(bucketname)

    potential_files = get_diff_files(mod_dir)

    date = datetime.now()
    datestr = "%d-%02d" % (date.year, date.month)
    filedir = "regressions/{0}/{1}-{2}/{3}/{4}".format(datestr, sys.argv[4], sys.argv[5], sys.argv[1], device_id)

    found_files = []
    for filename in potential_files:
        filepath_to_send = filename

        #print("Processing output file: {0}".format(filepath_to_send))
        if not os.path.isfile(filepath_to_send):
            continue
        if not os.stat(filepath_to_send).st_size > 0:
            print("File is empty, not sending: {0}".format(filepath_to_send))
            continue



        try:
            filepath = "{0}/{1}".format(filedir, os.path.basename(filename))
            #print("Processing output file: {0}, uploading to: {1}".format(filepath_to_send, filepath))

            key = boto.s3.key.Key(bucket, filepath)
            file_to_send = open(filepath_to_send, 'r')
            key.set_contents_from_string(file_to_send.read())

            if make_public:
                key.make_public()

            htmlkey = boto.s3.key.Key(bucket, filepath + ".html")
            htmlkey.set_contents_from_string("""
                    <!doctype html>
                    <html>
                      <head>
                        <script src="//code.jquery.com/jquery-2.1.1.min.js"></script>
                        <script src="//code.jquery.com/jquery-migrate-1.2.1.min.js"></script>
                        <link href="//alexgorbatchev.com/pub/sh/current/styles/shCore.css" rel="stylesheet" type="text/css" />
                        <link href="//alexgorbatchev.com/pub/sh/current/styles/shThemeDefault.css" rel="stylesheet" type="text/css" />
                        <script src="//alexgorbatchev.com/pub/sh/current/scripts/shCore.js" type="text/javascript"></script>
                        <script src="//alexgorbatchev.com/pub/sh/current/scripts/shAutoloader.js" type="text/javascript"></script>
                        <script src="//alexgorbatchev.com/pub/sh/current/scripts/shBrushPhp.js" type="text/javascript"></script>
                        <script src="//alexgorbatchev.com/pub/sh/current/scripts/shBrushPlain.js" type="text/javascript"></script>
                        <script src="//alexgorbatchev.com/pub/sh/current/scripts/shBrushDiff.js" type="text/javascript"></script>
                      </head>
                      <body>

                        <script>
                          filename = '/""" + filepath + """'
                        </script>

                        <div id="codeholder">
                        </div>

                        <script>
                          $.get(filename , function( data ) {
                            elem = document.createElement("pre");
                            brush = "plain";
                            if (filename.indexOf(".dif") != -1)
                            {
                              brush = "diff";
                            } 
                            elem.setAttribute("class", "brush: " + brush + "; gutter: true;");
                            elem.appendChild(document.createTextNode(data.replace("<", "&lt;")));
                            document.getElementById("codeholder").appendChild(elem);
                            SyntaxHighlighter.highlight(elem);
                          });

                          SyntaxHighlighter.all();
                        </script>
                      </body>
                    </html>""", headers={"Content-Type": "text/html"})

            if make_public:
                htmlkey.make_public()

            found_files.append(filename)
        except Exception as e:
            success = False
            print("There was a problem processing file: %s" % e)

    if len(found_files) > 0:
        try:
            htmlkey = boto.s3.key.Key(bucket, filedir + "/index.html")
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
                          <tr><th>filename</th><th></th><th></th></tr>"""

            for filename in found_files:
                filepath = "{0}/{1}".format(filedir, os.path.basename(filename))
                index += "<tr><td>" + os.path.basename(filename) + "</td><td><a href='/" + filepath + "'>download</a></td><td><a href='/" + filepath + ".html'>view</a></td></tr>"

            index += """
                        </table>
                      </body>
                    </html>"""

            htmlkey.set_contents_from_string(index, headers={"Content-Type": "text/html"})

            if make_public:
                htmlkey.make_public()

            url = "http://{0}.s3-website-{1}.amazonaws.com/{2}".format(bucketname, "us-east-1", filedir)
            print("<a href='{0}'>Regression Results</a>".format(url))
        except Exception as e:
            success = False
            print("There was a problem generating results webpage: %s" % e)

if success and not has_diffs:
    print("Success")


