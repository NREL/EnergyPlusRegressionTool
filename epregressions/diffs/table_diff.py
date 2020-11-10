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
from epregressions.diffs.thresh_dict import ThreshDict

help_message = __doc__

path = os.path.dirname(__file__)
script_dir = os.path.abspath(path)

title_css = """<!DOCTYPE html PUBLIC "-
//W3C//DTD XHTML 1.0 Strict//EN"
"http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd"><html xmlns="http://www.w3.org/1999/xhtml">
<head><title>%s</title>  <style type="text/css"> %s </style>
<meta name="generator" content="BBEdit 8.2" /></head>
<body></body></html>
"""

title_html = """<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN"
        "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
    <title>%s</title>
    <meta name="generator" content="BBEdit 8.2" />
</head>
<body>

</body>
</html>
"""

the_css = """td.big {
    background-color: #FF969D;
}

td.small {
    background-color: #FFBE84;
}

td.equal {
    background-color: #CBFFFF;
}

td.table_size_error {
    background-color: #FCFF97;
}
.big {
    background-color: #FF969D;
}

.small {
    background-color: #FFBE84;
}

"""


def thresh_abs_rel_diff(abs_thresh, rel_thresh, x, y):
    if x == y:
        return 0, 0, 'equal'
    # noinspection PyBroadException
    try:
        diff = 'equal'

        fx = float(x)
        fy = float(y)

        abs_diff = abs(fx - fy)

        # the following two lines were here, but I don't see how they could be hit, I'm commenting for now
        # if abs_diff == 0.0:
        #     return 0, 0, 'equal'

        rel_diff = abs((fx - fy) / fx) if abs(fx) > abs(fy) else abs((fy - fx) / fy)

        if abs_diff > abs_thresh and rel_diff > rel_thresh:
            diff = 'big'
        elif (0 < abs_diff <= abs_thresh) or (0 < rel_diff <= rel_thresh):
            diff = 'small'
        # the following else clause was here, but again, I don't see how it could be hit, commenting
        # else:
        #     diff = 'equal'
        return abs_diff, rel_diff, diff
    except:
        return '%s vs %s' % (x, y), '%s vs %s' % (x, y), 'stringdiff'


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
    # noinspection PyBroadException
    try:
        val = prev_sib(table)
        if val:
            return '%s' % val
        else:
            return None
    except:  # pragma: no cover - AFAIK the prev_sib will always return _something_, including None, but I can't be sure
        return None


def hdict2soup(soup, heading, num, hdict, tdict, horder):
    """Create soup table (including anchor and heading) from header dictionary and error dictionary"""
    # Append table anchor
    atag = Tag(soup, name='a', attrs=[('name', '%s%s' % ('tablehead', num,))])
    soup.body.append(atag)

    # Append table heading
    htag = Tag(soup, name='b')
    htag.append(heading)
    soup.body.append(htag)

    # Append table
    tabletag = Tag(soup, name='table', attrs=[('border', '1')])
    soup.body.append(tabletag)

    # Append column headings
    trtag = Tag(soup, name='tr')
    tabletag.append(trtag)
    for h in horder:
        tdtag = Tag(soup, name='th')
        if h != 'DummyPlaceholder':
            tdtag.append(str(h))
        else:
            tdtag.append('')
        trtag.append(tdtag)

    # Append column thresholds
    trtag = Tag(soup, name='tr')
    tabletag.append(trtag)
    for h in horder:
        tdtag = Tag(soup, name='td')
        trtag.append(tdtag)
        if h in tdict:
            (abs_thresh, rel_thresh) = tdict[h]
            tdtag.append(str(abs_thresh))
        else:
            tdtag.append('Absolute threshold')

    trtag = Tag(soup, name='tr')
    tabletag.append(trtag)
    for h in horder:
        tdtag = Tag(soup, name='td')
        trtag.append(tdtag)
        if h in tdict:
            (abs_thresh, rel_thresh) = tdict[h]
            tdtag.append(str(rel_thresh))
        else:
            tdtag.append('Relative threshold')

    # Append table rows
    for i in range(0, len(hdict[horder[0]])):
        trtag = Tag(soup, name='tr')
        tabletag.append(trtag)
        for h in horder:
            if h not in hdict:
                tdtag = Tag(soup, name='td', attrs=[("class", "big")])
                tdtag.append('ColumnHeadingDifference')
            elif h == 'DummyPlaceholder' or h == 'Subcategory':
                # Some tables such as the Source Energy End Use Components
                # have a blank row full of `<td>&nbsp;</td>` which won't be
                # decoded nicely
                tdtag = Tag(soup, name='td')
                val = hdict[h][i]
                try:
                    tdtag.append(str(val))
                except Exception:  # pragma: no cover
                    val = val.encode('ascii', 'ignore').decode('ascii')
                    tdtag.append(str(val))
            else:
                (diff, which) = hdict[h][i]
                tdtag = Tag(soup, name='td', attrs=[('class', which)])
                try:
                    tdtag.append(str(diff))
                except Exception:  # pragma: no cover
                    diff = diff.encode('ascii', 'ignore').decode('ascii')
                    tdtag.append(str(diff))
            trtag.append(tdtag)


# Convert html table to heading dictionary (and header list) in single step
def table2hdict_horder(table):
    hdict = {}
    horder = []
    trows = table('tr')

    # Create dictionary headings
    for htd in trows[0]('td'):
        try:
            hcontents = htd.contents[0]
        except IndexError:
            hcontents = 'DummyPlaceholder'

        hdict[hcontents] = []
        horder.append(hcontents)

    for trow in trows[1:]:
        for htd, td in zip(trows[0]('td'), trow('td')):
            try:
                hcontents = htd.contents[0]
            except IndexError:
                hcontents = 'DummyPlaceholder'

            try:
                contents = td.contents[0]
            except IndexError:
                contents = ''

            hdict[hcontents].append(contents)

    return hdict, horder


def make_err_table_row(err_soup, tabletag, uheading, count_of_tables, abs_diff_file, rel_diff_file,
                       small_diff, big_diff, equal, string_diff, size_error, not_in_1, not_in_2):
    # Create entry in error table
    trtag = Tag(err_soup, name='tr')
    tabletag.append(trtag)

    tdtag_name = Tag(err_soup, name='td')
    trtag.append(tdtag_name)
    tdtag_name.append(uheading)

    tdtag_abs_link = Tag(err_soup, name='td')
    trtag.append(tdtag_abs_link)

    tdtag_rel_link = Tag(err_soup, name='td')
    trtag.append(tdtag_rel_link)

    if small_diff > 0 or big_diff > 0 or string_diff > 0:
        atag = Tag(err_soup, name='a', attrs=[('href', '%s#tablehead%s' % (abs_diff_file, count_of_tables))])
        atag.append('abs file')
        tdtag_abs_link.append(atag)

        atag = Tag(err_soup, name='a', attrs=[('href', '%s#tablehead%s' % (rel_diff_file, count_of_tables))])
        atag.append('rel file')
        tdtag_rel_link.append(atag)

    tdtag_big_diff = Tag(err_soup, name='td', attrs=[('class', 'big')] if big_diff > 0 else [])
    trtag.append(tdtag_big_diff)
    tdtag_big_diff.append(str(big_diff))

    tdtag_small_diff = Tag(err_soup, name='td', attrs=[('class', 'small')] if small_diff > 0 else [])
    trtag.append(tdtag_small_diff)
    tdtag_small_diff.append(str(small_diff))

    tdtag_equal = Tag(err_soup, name='td', attrs=[])
    trtag.append(tdtag_equal)
    tdtag_equal.append(str(equal))

    tdtag_string_diff = Tag(err_soup, name='td', attrs=[('class', 'stringdiff')] if string_diff > 0 else [])
    trtag.append(tdtag_string_diff)
    tdtag_string_diff.append(str(string_diff))

    tdtag_table_size_error = Tag(err_soup, name='td', attrs=[
        ('class', 'table_size_error')] if size_error > 0 or not_in_1 > 0 or not_in_2 > 0 else [])
    trtag.append(tdtag_table_size_error)
    tdtag_table_size_error.append(
        'size mismatch' if size_error > 0 else 'not in 1' if not_in_1 > 0 else 'not in 2' if not_in_2 > 0 else '')


def table_diff(thresh_dict, inputfile1, inputfile2, abs_diff_file, rel_diff_file, err_file, summary_file):
    """
    Compares two xxxTable.html files returning
    (
        <message>, <#tables>, <#big_diff>,
        <#small_diff>, <#equals>, <#string_diff>,
        <#size_diff>, <#not_in_file1>, <#not_in_file2>
    )
    """

    case_name = inputfile1.split(os.sep)[-2]

    # Test for existence of input files
    if not os.path.exists(inputfile1):
        return 'unable to open file <%s>' % inputfile1, 0, 0, 0, 0, 0, 0, 0, 0
    if not os.path.exists(inputfile2):
        return 'unable to open file <%s>' % inputfile2, 0, 0, 0, 0, 0, 0, 0, 0

    with open(inputfile1, 'rb') as f_1:
        txt1 = f_1.read().decode('utf-8', errors='ignore')
    with open(inputfile2, 'rb') as f_2:
        txt2 = f_2.read().decode('utf-8', errors='ignore')

    pagetitle = '%s vs %s' % (os.path.basename(inputfile1), os.path.basename(inputfile2))

    # Error soup
    err_soup = BeautifulSoup(title_css % (pagetitle + ' -- summary', the_css,),
                             features='html.parser')

    # Abs diff soup
    abs_diff_soup = BeautifulSoup(title_css % (pagetitle + ' -- absolute differences', the_css,),
                                  features='html.parser')

    # Rel diff soup
    rel_diff_soup = BeautifulSoup(title_css % (pagetitle + ' -- relative differences', the_css,),
                                  features='html.parser')

    # Make error table
    tabletag = Tag(err_soup, name='table', attrs=[('border', '1')])
    err_soup.body.append(tabletag)

    # Make error table headings
    trtag = Tag(err_soup, name='tr')
    tabletag.append(trtag)
    for title in ['Table', 'Abs file', 'Rel file', 'Big diffs', 'Small diffs', 'Equals', 'String diffs', 'Size diffs']:
        thtag = Tag(err_soup, name='th')
        trtag.append(thtag)
        thtag.append(title)

    # Soup up the HTML input files
    soup2 = BeautifulSoup(txt2, features='html.parser')
    soup1 = BeautifulSoup(txt1, features='html.parser')

    tables1 = soup1('table')
    tables2 = soup2('table')

    uheadings1 = []
    uheadings2 = []
    for table in tables1:
        uheadings1.append(get_table_unique_heading(table))
    for table in tables2:
        uheadings2.append(get_table_unique_heading(table))

    if any([x is None for x in uheadings1]):
        return 'malformed comment/table structure in <%s>' % inputfile1, 0, 0, 0, 0, 0, 0, 0, 0
    if any([x is None for x in uheadings2]):
        return 'malformed comment/table structure in <%s>' % inputfile2, 0, 0, 0, 0, 0, 0, 0, 0

    uhset1 = set(uheadings1)
    uhset2 = set(uheadings2)
    uhset_match = set.intersection(uhset1, uhset2)

    count_of_tables = 0
    count_of_tables_diff = 0

    count_of_small_diff = 0
    count_of_big_diff = 0
    count_of_equal = 0
    count_of_string_diff = 0
    count_of_size_error = 0
    count_of_not_in_1 = 0
    count_of_not_in_2 = 0

    for i1 in range(0, len(list(uheadings1))):

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
        if uheading1 not in uhset_match:
            table_not_in_2 = 1
            count_of_not_in_2 += table_not_in_2
            make_err_table_row(err_soup, tabletag, uheading1, count_of_tables, abs_diff_file, rel_diff_file,
                               table_small_diff, table_big_diff, table_equal, table_string_diff, table_size_error,
                               table_not_in_1, table_not_in_2)
            continue

        table1 = tables1[i1]
        table2 = tables2[uheadings2.index(uheading1)]

        # Table size error
        if len(table1('tr')) != len(table2('tr')) or len(table1('td')) != len(table2('td')):
            table_size_error = 1
            count_of_size_error += table_size_error
            make_err_table_row(err_soup, tabletag, uheading1, count_of_tables, abs_diff_file, rel_diff_file,
                               table_small_diff, table_big_diff, table_equal, table_string_diff, table_size_error,
                               table_not_in_1, table_not_in_2)
            continue

        hdict1, horder1 = table2hdict_horder(table1)
        hdict2, horder2 = table2hdict_horder(table2)

        # honestly, if the column headings have changed, this should be an indicator to all reviewers that this needs
        # up close investigation.  As such, we are going to trigger the following things:
        # 1) a table_size_error, because even though the sizes are the "same", the sizes have sort-of changed due to the
        #    missing column and added column in the second table
        # 2) a table_string_diff, because if the columns have changed, there must be at least one title different (yes
        #    even if it is duplicate, it is different because there is another one)
        # 3) a table_big_diff here, because something has definitely changed that needs attention
        # 4) each datum in each row that doesn't have a match should trigger a big diff as well later
        if any([h not in horder2 for h in horder1]) or any([h not in horder1 for h in horder2]):
            table_size_error += 1
            count_of_size_error += 1
            table_string_diff += 1
            count_of_string_diff += 1
            table_big_diff += 1
            count_of_big_diff += 1

        # Dictionaries of absolute and relative differences
        diff_dict = {}
        h_thresh_dict = {}

        for h in horder1:
            if h == 'DummyPlaceholder':
                diff_dict[h] = hdict1[h]
            else:
                if h not in horder2:
                    diff_dict[h] = [[0, 0, 'big']] * (len(table1('tr')) - 1)
                else:
                    (abs_thresh, rel_thresh) = thresh_dict.lookup(h)
                    h_thresh_dict[h] = (abs_thresh, rel_thresh)
                    diff_dict[h] = []
                    for x, y in zip(hdict1[h], hdict2[h]):
                        diff_dict[h].append(thresh_abs_rel_diff(abs_thresh, rel_thresh, x, y))

                # Statistics local to this table
                for diff_result in diff_dict[h]:
                    diff_type = diff_result[2]
                    if diff_type == 'small':
                        table_small_diff += 1
                        count_of_small_diff += 1
                    elif diff_type == 'big':
                        table_big_diff += 1
                        count_of_big_diff += 1
                    elif diff_type == 'equal':
                        table_equal += 1
                        count_of_equal += 1
                    if diff_type == 'stringdiff':
                        table_string_diff += 1
                        count_of_string_diff += 1

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
            abs_diff_dict[h] = diff_dict[h] if (h == 'DummyPlaceholder' or h == 'Subcategory') else [
                (x_y_z[0], x_y_z[2]) for x_y_z in diff_dict[h]]
        hdict2soup(abs_diff_soup, uheading1, count_of_tables, abs_diff_dict.copy(), h_thresh_dict, horder1)

        rel_diff_dict = {}
        for h in horder1:
            if h not in horder2:
                continue
            rel_diff_dict[h] = diff_dict[h] if (h == 'DummyPlaceholder' or h == 'Subcategory') else [
                (x_y_z[1], x_y_z[2]) for x_y_z in diff_dict[h]]
        hdict2soup(rel_diff_soup, uheading1, count_of_tables, rel_diff_dict.copy(), h_thresh_dict, horder1)

        count_of_tables_diff += 1

    for uheading2 in uheadings2:
        if uheading2 not in uhset_match:
            count_of_tables += 1
            count_of_not_in_1 += 1
            make_err_table_row(err_soup, tabletag, uheading2, count_of_tables, abs_diff_file, rel_diff_file,
                               0, 0, 0, 0, 0, 1, 0)

    # Write error file
    err_txt = err_soup.prettify()
    with open(err_file, 'wb') as f_out:
        f_out.write(err_txt.encode('utf-8', errors='ignore'))

    # Only write absolute and relative diff files if any tables were actually different
    if count_of_tables_diff > 0:
        abs_diff_txt = abs_diff_soup.prettify()
        with open(abs_diff_file, 'wb') as f_abs:
            f_abs.write(abs_diff_txt.encode('utf-8', errors='ignore'))

        rel_diff_txt = rel_diff_soup.prettify()
        with open(rel_diff_file, 'wb') as f_rel:
            f_rel.write(rel_diff_txt.encode('utf-8', errors='ignore'))

    if summary_file:
        if not os.path.exists(summary_file):
            with open(summary_file, 'w') as summarize:
                summarize.write(
                    "Case,TableCount,BigDiffCount,SmallDiffCount,EqualCount,"
                    "StringDiffCount,SizeErrorCount,NotIn1Count,NotIn2Count\n"
                )
        with open(summary_file, 'a') as summarize:
            summarize.write("%s,%s,%s,%s,%s,%s,%s,%s,%s\n" % (
                case_name, count_of_tables, count_of_big_diff, count_of_small_diff, count_of_equal,
                count_of_string_diff,
                count_of_size_error, count_of_not_in_1, count_of_not_in_2))

    return ('', count_of_tables, count_of_big_diff, count_of_small_diff, count_of_equal, count_of_string_diff,
            count_of_size_error, count_of_not_in_1, count_of_not_in_2)


def main(argv=None):  # pragma: no cover
    if argv is None:
        argv = sys.argv
    try:
        opts, args = getopt.getopt(argv[1:], "ho:v", ["help", "output="])
    except getopt.error as msg:
        print(sys.argv[0].split("/")[-1] + ": " + str(msg) + "\n\t for help use --help")
        return -1

    # Test for correct number of arguments
    # prog_name = os.path.basename(sys.argv[0])
    # if len(args) == 5:
    [inputfile1, inputfile2, abs_diff_file, rel_diff_file, err_file, summary_file] = args
    # else:
    #    info('%s: incorrect operands: Try %s -h for more info' % (prog_name, prog_name))
    #    return -1

    # Load diffing threshold dictionary
    thresh_dict = ThreshDict(os.path.join(script_dir, 'math_diff.config'))

    # run the main program.
    table_diff(thresh_dict, inputfile1, inputfile2, abs_diff_file, rel_diff_file, err_file, summary_file)
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
