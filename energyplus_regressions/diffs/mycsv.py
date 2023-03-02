# Copyright (C) 2009 Santosh Philip
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

import csv
import sys


class MyCsv(Exception):
    pass


class BadMatrice(MyCsv):
    pass


class BadInput(MyCsv):
    pass


def readcsv(filename):
    """read csv file fname into a matrice mat
    Also reads a string instead of a file
    """
    try:
        with open(filename) as f:
            reader = csv.reader(f)  # if it is a file
            data = []
            for line in reader:
                # print ("%s : %s" % (filename, line))
                data.append(line)
            return data
    except:
        try:
            lines = filename.split('\n')
            data = []
            for line in lines:
                if line.strip() == '':
                    break
                # print ("%s : %s" % (filename, line))
                data.append(line.strip().split(','))
            return data
        except:
            raise BadInput('csv source is neither a file nor a file object')


def writecsv(mat, outfile=None, mode='w'):
    """write the matrice mat into a file fname
    """
    if not ismatrice(mat):
        raise BadMatrice('The input is not a matrice')
    if outfile:
        with open(outfile, mode) as f_out:
            writer = csv.writer(f_out)
            writer.writerows(mat)
    else:
        out_str = ''
        for row in mat:
            for i, cell in enumerate(row):
                max_col_num = len(row) - 1
                if i < max_col_num:
                    out_str += str(cell) + ','
                else:
                    out_str += str(cell) + '\n'
        return out_str


def ismatrice(mat):
    """test if the matrice mat is a csv matrice
    """
    # test for iterability over rows
    try:
        iter(mat)
    except TypeError:
        return False
    # test for rows
    for row in mat:
        if type(row) != list:
            return False
    # test if cell is float, int or string
    for row in mat:
        for cell in row:
            if type(cell) not in (float, int):
                if sys.version_info[0] == 2:
                    # I would like to just redefine basestring to str on Python 2 but I don't have time right now
                    if not isinstance(cell, basestring):  # noqa: F821  # pragma: no cover
                        return False
                else:  # python 3
                    if not isinstance(cell, str):
                        return False
    return True


def transpose2d(mtx):
    """Transpose a 2d matrix
       [
            [1,2,3],
            [4,5,6]
            ]
        becomes
        [
            [1,4],
            [2,5],
            [3,6]
            ]
    """
    trmtx = [[] for _ in mtx[0]]
    for i in range(len(mtx)):
        for j in range(len(mtx[i])):
            trmtx[j].append(mtx[i][j])
    return trmtx


# from python cookbook 2nd edition page 162

def getlist(fname):
    """Gets a list from a csv file
    If the csv file has only one column:
        it returns [a,b,c,d,e]
    if it has more than one column:
        it returns [[a,s],[3,r],[v,g]]
    This should work with a text file of one column
    """
    mat = readcsv(fname)
    onecolumn = True
    for row in mat:
        if len(row) != 1:
            onecolumn = False
            break
    if onecolumn:
        mat = transpose2d(mat)[0]
        mat[0] = mat[0].strip()
    else:
        # trim extraneous whitespace from csv headers
        mat[0] = [x.strip() for x in mat[0]]

    return mat
