#!/usr/bin/env python
# encoding: utf-8

"""
    configuration file math_diff.config customizes absolute and relative difference thresholds
    for different unit/aggregation pairs, for instance:
               C,* = 0.1, 0.005
    means that all in fields reported in C (degrees celsius) will be compared with an absolute
    difference tolerance of 0.1 degree C and 0.005 (0.5%) relative difference tolerance.
"""

# Copyright (C) 2013 Amir Roth
# This file is part of mathdiff.
# 
# mathdiff is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# mathdiff is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with mathdiff.  If not, see <http://www.gnu.org/licenses/>.
# VERSION: 1.3


__author__ = "Amir Roth (amir dot roth at ee dot doe dot gov)"
__version__ = "1.4"
__copyright__ = "Copyright (c) 2013 Amir Roth"
__license__ = "GNU General Public License Version 3"

import sys
import re
import traceback

# Load threshold dictionary from math_diff.config file
class ThreshDict(object):

    def __init__(self, tdname):
        self.tdict = {}
        f = open(tdname, 'r')
        while f:
            l = f.readline().rstrip('\n')
            l = l.strip()
            if l == '':
                break
            # Ignore comment lines
            if l[0] == '#':
                continue
            try:
                # Split off end-of-line comments
                if l.find('#') > -1:
                    l = l[:l.find('#')]

                [unit,agg,abs_thresh,rel_thresh] = [x.strip() for x in re.split(',|=',l) if x != '']
                tag = unit+'|'+agg
            
                if tag in self.tdict:
                    print >> sys.stderr, 'Over-riding existing entry for %s in threshold dictionary math_diff.config' % (tag)

                self.tdict[tag] = (float(abs_thresh), float(rel_thresh))
            except:
                print >> sys.stderr, 'Skipping line <%s>' % (l)

        f.close()


    def lookup(self, hstr):
        # Lookup a threshold value in the dictionary using a report column
        # header string and a differncing type (relative or absolute)

        if hstr == 'Date/Time' or hstr == 'Time':
            return (0.0, 0.0)

        # Parse hstr (column header) to extract Unit and Aggregation 
        
        try: 
            if hstr.find('[]') == -1 and hstr.find('[') > -1:
                tokens = [x.strip() for x in re.split('\[|\]', hstr) if x.strip() != '']
                unit = tokens[1] if len(tokens) > 1 else tokens[0]
            else:
                unit = '*'
            if hstr.find('{}') == -1 and hstr.find('{') > -1:
                tokens = [x.strip() for x in re.split('\{|\}', hstr) if x.strip() != '']
                agg = tokens[1] if len(tokens) > 1 else tokens[0]
            else:
                agg = '*'
                
        except:
            # print >> sys.stderr, 'PROBLEM: cannot figure out unit/aggregation for ' + hstr + ', defaulting to *,*'
            unit = '*'
            agg = '*'
            
        tag = unit+'|'+agg
        tag_d1 = unit+'|*'
        tag_d2 = '*|*'
        # Look for matching Quantity and Aggregation
        if tag in self.tdict:
            return self.tdict[tag]
        # Then just matching Quantity
        elif tag_d1 in self.tdict:
            return self.tdict[tag_d1]
        # Then the global default
        elif tag_d2 in self.tdict:
            return self.tdict[tag_d2]
        else:
            return (0.0, 0.0)

