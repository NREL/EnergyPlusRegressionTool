#!/usr/bin/env python
# -*- coding: utf-8 -*- 
from __future__ import unicode_literals

"""Takes two E+ html output files and compares them
usage:
    python TableDiff <in_file1> <in_file2> <out_abs_diff> <out_rel_diff> <err_log> <my_summary_file>

    <in_file1> = first input HTML file
    <in_file2> = second input HTML file
    <out_abs_file> = output HTML file of absolute differences
    <out_rel_file> = output HTML file of relative differences
    <out_err_log> = output HTML file of summary difference information
    <my_summary_file> = An overview (csv) of summary results, intended for multiple files appended
"""

# Copyright (C) 2009, 2010 Santosh Philip and Amir Roth 2013
# This file is part of tablediff.
# 
# tablediff is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# tablediff is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with tablediff.  If not, see <http://www.gnu.org/licenses/>.
# VERSION: 1.3

__author__ = "Santosh Philip (santosh_philip at yahoo dot com) and Amir Roth (amir dot roth at ee dot doe dot gov)"
__version__ = "1.4"
__copyright__ = "Copyright (c) 2009 Santosh Philip and Amir Roth 2013"
__license__ = "GNU General Public License Version 3"

import sys
import getopt
import os.path

from bs4 import BeautifulSoup, NavigableString, Tag
from epregressions import html_data
from epregressions import ThreshDict

help_message = __doc__

path = os.path.dirname(__file__)
script_dir = os.path.abspath(path)


class Usage(Exception):
    """ usage """

    def __init__(self, msg):
        self.msg = msg


def thresh_abs_rel_diff(abs_thresh, rel_thresh, x, y):
    if (x == y):
        return (0, 0, 'equal')
    try:
        fx = float(x)
        fy = float(y)

        abs_diff = abs(fx - fy)
        if (abs_diff == 0.0):
            return (0, 0, 'equal')

        rel_diff = abs((fx - fy) / fx) if abs(fx) > abs(fy) else abs((fy - fx) / fy)

        if (abs_diff > abs_thresh and rel_diff > rel_thresh):
            diff = 'big'
        elif (abs_diff > 0 and abs_diff <= abs_thresh) or (rel_diff > 0 and rel_diff <= rel_thresh):
            diff = 'small'
        else:
            diff = 'equal'
        return (abs_diff, rel_diff, diff)
    except:
        return ('%s vs %s' % (x, y), '%s vs %s' % (x, y), 'stringdiff')


def prev_sib(entity):
    """get soup.previousSibling ignoring stripping out all blank spaces"""
    prevs = entity
    i = 0
    while i == 0:
        prevs = prevs.previousSibling
        if type(prevs) == NavigableString:
            utxt = prevs.strip()
            if utxt == '':
                continue
        return prevs


def get_table_unique_heading(table):
    """return table unique name which should be in comment immediately before table"""
    try:
        return '%s' % (prev_sib(table))
    except:
        pass
    return None


def get_table_heading(table):
    """return a list of E+ table headings. All tags are removed 
    and some headings are modified."""
    # test for heading type 1
    # <b>heading1</b><br><br>
    # <table></table>
    try:
        pr1 = prev_sib(table)
        pr2 = prev_sib(pr1)
        soup = BeautifulSoup('')
        brtag = Tag(soup, 'br')
        if pr1 == brtag and pr2 == brtag:
            return '%s' % (prev_sib(prevs2).contents[0],)
    except  (IndexError, AttributeError):
        pass
    # test for heading type 2
    # <p>Report:<b>Name1</b></p><p>For:<b>Name2</b></p><p>Timestamp</p>
    # <table></table>
    try:
        prevs1 = prev_sib(table)
        prevs2 = prev_sib(prevs1)
        prevs3 = prev_sib(prevs2)
        if prevs2.contents[0] == u'For:':
            if prevs3.contents[0] == u'Report:':
                name1 = prevs3.contents[1].contents[0]
                name2 = prevs2.contents[1].contents[0]
                return '%s for %s' % (name1, name2)
    except (IndexError, AttributeError):
        pass
        # test for heading type 3
    # <p>Report:<b>Name1</b></p><p>For:<b>Name2</b></p><p>Timestamp</p>
    # Values in table are in hours.<br><br>
    # <table></table>
    try:
        pr1 = prev_sib(table)
        pr2 = prev_sib(pr1)
        pr3 = prev_sib(pr2)
        prevs1 = prev_sib(pr3)
        prevs2 = prev_sib(prevs1)
        prevs3 = prev_sib(prevs2)
        if prevs2.contents[0] == u'For:':
            if prevs3.contents[0] == u'Report:':
                name1 = prevs3.contents[1].contents[0]
                name2 = prevs2.contents[1].contents[0]
                return '%s for %s' % (name1, name2)
    except (IndexError, AttributeError):
        pass
    return None


def hdict2soup(soup, heading, num, hdict, tdict, horder):
    """Create soup table (including anchor and heading) from header dictionary and error dictionary"""
    # Append table anchor
    atag = Tag(soup, 'a', [('name', '%s%s' % ('tablehead', num,))])
    soup.body.append(atag)

    # Append table heading
    htag = Tag(soup, 'b')
    htag.append(heading)
    soup.body.append(htag)

    # Append table
    tabletag = Tag(soup, 'table', [('border', '1')])
    soup.body.append(tabletag)

    # Append column headings
    trtag = Tag(soup, 'tr')
    tabletag.append(trtag)
    for h in horder:
        tdtag = Tag(soup, 'th')
        if h != 'DummyPlaceholder':
            tdtag.append(str(h))
        else:
            tdtag.append('')
        trtag.append(tdtag)

    # Append column thresholds
    trtag = Tag(soup, 'tr')
    tabletag.append(trtag)
    for h in horder:
        tdtag = Tag(soup, 'td')
        trtag.append(tdtag)
        if h in tdict:
            (abs_thresh, rel_thresh) = tdict[h]
            tdtag.append(str(abs_thresh))
        else:
            tdtag.append('Absolute threshold')

    trtag = Tag(soup, 'tr')
    tabletag.append(trtag)
    for h in horder:
        tdtag = Tag(soup, 'td')
        trtag.append(tdtag)
        if h in tdict:
            (abs_thresh, rel_thresh) = tdict[h]
            tdtag.append(str(rel_thresh))
        else:
            tdtag.append('Relative threshold')

    # Append table rows
    for i in range(0, len(hdict[horder[0]])):
        trtag = Tag(soup, 'tr')
        tabletag.append(trtag)
        for h in horder:
            if h == 'DummyPlaceholder' or h == 'Subcategory':
                tdtag = Tag(soup, 'td')
                tdtag.append((hdict[h][i]).encode('utf-8'))
                trtag.append(tdtag)
            else:
                (diff, which) = hdict[h][i]
                tdtag = Tag(soup, 'td', [('class', which)])
                tdtag.append(str(diff))
                trtag.append(tdtag)


# Convert html table to heading dictionary (and header list) in single
# step
def table2hdict_horder(table):
    hdict = {}
    horder = []
    trows = table('tr')

    # Create dictionary headings
    for htd in trows[0]('td'):
        try:
            hcontents = htd.contents[0]
        except IndexError as e:
            hcontents = 'DummyPlaceholder'

        hdict[hcontents] = []
        horder.append(hcontents)

    for trow in trows[1:]:
        for htd, td in zip(trows[0]('td'), trow('td')):
            try:
                hcontents = htd.contents[0]
            except IndexError as e:
                hcontents = 'DummyPlaceholder'

            try:
                contents = td.contents[0]
            except IndexError as e:
                contents = ''

            hdict[hcontents].append(contents)

    return hdict, horder


def make_err_table_row(err_soup, tabletag, uheading, count_of_tables, abs_diff_file, rel_diff_file,
                       small_diff, big_diff, equal, string_diff, size_error, not_in_1, not_in_2):
    # Create entry in error table
    trtag = Tag(err_soup, 'tr')
    tabletag.append(trtag)

    tdtag_name = Tag(err_soup, 'td')
    trtag.append(tdtag_name)
    tdtag_name.append(uheading)

    tdtag_abs_link = Tag(err_soup, 'td')
    trtag.append(tdtag_abs_link)

    tdtag_rel_link = Tag(err_soup, 'td')
    trtag.append(tdtag_rel_link)

    if small_diff > 0 or big_diff > 0 or string_diff > 0:
        atag = Tag(err_soup, 'a', [('href', '%s#tablehead%s' % (abs_diff_file, count_of_tables))])
        atag.append('abs file')
        tdtag_abs_link.append(atag)

        atag = Tag(err_soup, 'a', [('href', '%s#tablehead%s' % (rel_diff_file, count_of_tables))])
        atag.append('rel file')
        tdtag_rel_link.append(atag)

    tdtag_big_diff = Tag(err_soup, 'td', [('class', 'big')] if big_diff > 0 else [])
    trtag.append(tdtag_big_diff)
    tdtag_big_diff.append(str(big_diff))

    tdtag_small_diff = Tag(err_soup, 'td', [('class', 'small')] if small_diff > 0 else [])
    trtag.append(tdtag_small_diff)
    tdtag_small_diff.append(str(small_diff))

    tdtag_equal = Tag(err_soup, 'td', [])
    trtag.append(tdtag_equal)
    tdtag_equal.append(str(equal))

    tdtag_string_diff = Tag(err_soup, 'td', [('class', 'stringdiff')] if string_diff > 0 else [])
    trtag.append(tdtag_string_diff)
    tdtag_string_diff.append(str(string_diff))

    tdtag_table_size_error = Tag(err_soup, 'td', [
        ('class', 'table_size_error')] if size_error > 0 or not_in_1 > 0 or not_in_2 > 0 else [])
    trtag.append(tdtag_table_size_error)
    tdtag_table_size_error.append(
        'size mismatch' if size_error > 0 else 'not in 1' if not_in_1 > 0 else 'not in 2' if not_in_2 > 0 else '')


def table_diff(thresh_dict, inputfile1, inputfile2, abs_diff_file, rel_diff_file, err_file, summary_file):
    """Compares two xxxTable.html files returning (<message>, <#tables>, <#big_diff>, <#small_diff>, <#equals>, <#string_diff>, <#size_diff>, <#not_in_file1>, <#not_in_file2>)"""
    # info('%s vs. %s\n' % (inputfile1, inputfile2), err_file)

    case_name = inputfile1.split(os.sep)[-2]

    # Test for existence of input files
    if not os.path.exists(inputfile1):
        # info('unable to open file <%s>' % (inputfile1), err_file)
        return ('unable to open file <%s>' % (inputfile1), 0, 0, 0, 0, 0)
    if not os.path.exists(inputfile2):
        # info('unable to open file <%s>' % (inputfile2), err_file)
        return ('unable to open file <%s>' % (inputfile2), 0, 0, 0, 0, 0)

    txt1 = open(inputfile1, 'r').read()
    txt2 = open(inputfile2, 'r').read()

    pagetitle = '%s vs %s' % (os.path.basename(inputfile1), os.path.basename(inputfile2))
    comparingthis = 'Comparing<br> %s<br> vs<br> %s<br><hr>' % (inputfile1, inputfile2)

    # Error soup
    err_soup = BeautifulSoup(html_data.titlecss % (pagetitle + ' -- summary', html_data.thecss,))

    # Abs diff soup
    abs_diff_soup = BeautifulSoup(html_data.titlecss % (pagetitle + ' -- absolute differences', html_data.thecss,))

    # Rel diff soup
    rel_diff_soup = BeautifulSoup(html_data.titlecss % (pagetitle + ' -- relative differences', html_data.thecss,))

    # Make error table 
    tabletag = Tag(err_soup, 'table', [('border', '1')])
    err_soup.body.append(tabletag)

    # Make error table headings
    trtag = Tag(err_soup, 'tr')
    tabletag.append(trtag)
    for title in ['Table', 'Abs file', 'Rel file', 'Big diffs', 'Small diffs', 'Equals', 'String diffs', 'Size diffs']:
        thtag = Tag(err_soup, 'th')
        trtag.append(thtag)
        thtag.append(title)

    # Soup up the HTML input files
    soup2 = BeautifulSoup(txt2)
    soup1 = BeautifulSoup(txt1)

    tables1 = soup1('table')
    tables2 = soup2('table')

    uheadings1 = map(get_table_unique_heading, tables1)
    uheadings2 = map(get_table_unique_heading, tables2)

    uhset1 = set(uheadings1)
    uhset2 = set(uheadings2)
    uhset_match = set.intersection(uhset1, uhset2)
    uhset_diff = set.symmetric_difference(uhset1, uhset2)

    count_of_tables = 0
    count_of_tables_diff = 0

    count_of_small_diff = 0
    count_of_big_diff = 0
    count_of_equal = 0
    count_of_string_diff = 0
    count_of_size_error = 0
    count_of_not_in_1 = 0
    count_of_not_in_2 = 0

    for i1 in range(0, len(uheadings1)):

        count_of_tables += 1

        table_small_diff = 0
        table_big_diff = 0
        table_equal = 0
        table_string_diff = 0
        table_size_error = 0
        table_not_in_1 = 0
        table_not_in_2 = 0

        uheading1 = uheadings1[i1]

        # Table missing in second input file
        if not uheading1 in uhset_match:
            table_not_in_2 = 1
            count_of_not_in_2 += table_not_in_2
            make_err_table_row(err_soup, tabletag, uheading1, count_of_tables, abs_diff_file, rel_diff_file,
                               table_small_diff, table_big_diff, table_equal, table_string_diff, table_size_error,
                               table_not_in_1, table_not_in_2)
            continue

        table1 = tables1[i1]
        table2 = tables2[uheadings2.index(uheading1)]

        # Table size error
        if (len(table1('tr')) != len(table2('tr')) or len(table1('td')) != len(table2('td'))):
            table_size_error = 1
            count_of_size_error += table_size_error
            make_err_table_row(err_soup, tabletag, uheading1, count_of_tables, abs_diff_file, rel_diff_file,
                               table_small_diff, table_big_diff, table_equal, table_string_diff, table_size_error,
                               table_not_in_1, table_not_in_2)
            continue

        hdict1, horder1 = table2hdict_horder(table1)
        hdict2, horder2 = table2hdict_horder(table2)

        # Dictionaries of absolute and relative differences
        diff_dict = {}
        h_thresh_dict = {}

        for h in horder1:
            if h == 'DummyPlaceholder':
                diff_dict[h] = hdict1[h]
            elif h not in horder2:
                continue
            else:
                (abs_thresh, rel_thresh) = thresh_dict.lookup(h)

                h_thresh_dict[h] = (abs_thresh, rel_thresh)
                diff_dict[h] = map(lambda x, y: thresh_abs_rel_diff(abs_thresh, rel_thresh, x, y), hdict1[h], hdict2[h])

                # Statistics local to this table
                table_small_diff += sum(1 for (abs, rel, diff) in diff_dict[h] if diff == 'small')
                table_big_diff += sum(1 for (abs, rel, diff) in diff_dict[h] if diff == 'big')
                table_equal += sum(1 for (abs, rel, diff) in diff_dict[h] if diff == 'equal')
                table_string_diff += sum(1 for (abs, rel, diff) in diff_dict[h] if diff == 'stringdiff')

                count_of_small_diff += table_small_diff
                count_of_big_diff += table_big_diff
                count_of_equal += table_equal
                count_of_string_diff += table_string_diff

        make_err_table_row(err_soup, tabletag, uheading1, count_of_tables, abs_diff_file, rel_diff_file,
                           table_small_diff, table_big_diff, table_equal, table_string_diff, table_size_error,
                           table_not_in_1, table_not_in_2)

        # If there were no differences, we are done
        if (table_small_diff == 0) and (table_big_diff == 0) and (table_string_diff == 0):
            continue

        # Add difference tables to absolute and relative difference soups
        abs_diff_dict = {}
        for h in horder1:
            if h not in horder2:
                continue
            abs_diff_dict[h] = diff_dict[h] if (h == 'DummyPlaceholder' or h == 'Subcategory') else list(map(lambda x_y_z: (x_y_z[0], x_y_z[2]), diff_dict[h]))  # EDWIN: Had to automate py 2-3 to convert lambda tuple parameter expansion
        hdict2soup(abs_diff_soup, uheading1, count_of_tables, abs_diff_dict, h_thresh_dict, horder1)

        rel_diff_dict = {}
        for h in horder1:
            if h not in horder2:
                continue
            rel_diff_dict[h] = diff_dict[h] if (h == 'DummyPlaceholder' or h == 'Subcategory') else list(map(lambda x_y_z: (x_y_z[1], x_y_z[2]), diff_dict[h]))  # EDWIN: Same here
        hdict2soup(rel_diff_soup, uheading1, count_of_tables, rel_diff_dict, h_thresh_dict, horder1)

        count_of_tables_diff += 1

    for uheading2 in uheadings2:
        if uheading2 not in uhset_match:
            count_of_tables += 1
            count_of_not_in_1 += 1
            make_err_table_row(err_soup, tabletag, uheading2, count_of_tables, abs_diff_file, rel_diff_file,
                               0, 0, 0, 0, 0, 1, 0)

    # Write error file
    err_txt = err_soup.prettify()
    open(err_file, 'w').write(err_txt)

    # Only write absolute and relative diff files if any tables were actually different
    if count_of_tables_diff > 0:
        abs_diff_txt = abs_diff_soup.prettify()
        open(abs_diff_file, 'w').write(abs_diff_txt)

        rel_diff_txt = rel_diff_soup.prettify()
        open(rel_diff_file, 'w').write(rel_diff_txt)

    if summary_file:
        if not os.path.exists(summary_file):
            with open(summary_file, 'w') as summarize:
                summarize.write(
                    "Case,TableCount,BigDiffCount,SmallDiffCount,EqualCount,StringDiffCount,SizeErrorCount,NotIn1Count,NotIn2Count\n")
        with open(summary_file, 'a') as summarize:
            summarize.write("%s,%s,%s,%s,%s,%s,%s,%s,%s\n" % (
            case_name, count_of_tables, count_of_big_diff, count_of_small_diff, count_of_equal, count_of_string_diff,
            count_of_size_error, count_of_not_in_1, count_of_not_in_2))

    return ('', count_of_tables, count_of_big_diff, count_of_small_diff, count_of_equal, count_of_string_diff,
            count_of_size_error, count_of_not_in_1, count_of_not_in_2)


def main(argv=None):
    if argv is None:
        argv = sys.argv
    try:
        opts, args = getopt.getopt(argv[1:], "ho:v", ["help", "output="])
    except getopt.error as msg:
        info(sys.argv[0].split("/")[-1] + ": " + str(msg) + "\n\t for help use --help")
        return -1

    # Test for correct number of arguments
    # prog_name = os.path.basename(sys.argv[0])
    # if len(args) == 5:
    [inputfile1, inputfile2, abs_diff_file, rel_diff_file, err_file, summary_file] = args
    # else:
    #    info('%s: incorrect operands: Try %s -h for more info' % (prog_name, prog_name))
    #    return -1

    # Load diffing threshold dictionary
    thresh_dict = ThreshDict.ThreshDict(os.path.join(script_dir, 'MathDiff.config'))

    # run the main program.
    table_diff(thresh_dict, inputfile1, inputfile2, abs_diff_file, rel_diff_file, err_file, summary_file)
    return 0


if __name__ == "__main__":
    sys.exit(main())
