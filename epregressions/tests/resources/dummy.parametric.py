#!/usr/bin/env python

import shutil

file_contents = open('in.idf').read().upper()

if 'PARAMETRIC:' in file_contents:
    shutil.copy('in.idf', 'in-01.idf')
    shutil.copy('in.idf', 'in-02.idf')
    shutil.copy('in.idf', 'in-03.idf')
