#!/usr/bin/env python

"""
So we are going to ReadVarsESO in a silly way
1) We are going to make it expect an eplusout.eso only - not managing rvi or mvi files
2) We expect this file to be JSON, and have one key: output
   The value of this key should be "base", "smalldiffs", or "bigdiffs"
   Based on this key, the value will write slightly different csv files
{
  "output": "base" / "smalldiffs" / "bigdiffs"
  }
}
"""

import json
import sys

with open('eplusout.eso') as f_idf:
    idf_body = f_idf.read()
    # noinspection PyBroadException
    try:
        output_mode = json.loads(idf_body)['output']
    except:
        sys.exit(0)

base_output = """Date/Time,Variable 1 [C](Hourly),Variable 2 [W](Hourly),Variable 3 [W](Hourly)
 01/21  01:00:00,20.5,40000.0,1.0
 01/21  02:00:00,20.5,40000.0,2.0
 01/21  03:00:00,20.5,40000.0,3.0
 01/21  04:00:00,20.5,40000.0,4.0"""
small_output = """Date/Time,Variable 1 [C](Hourly),Variable 2 [W](Hourly),Variable 3 [W](Hourly)
 01/21  01:00:00,20.5,40005.0,1.0
 01/21  02:00:00,20.5,40000.0,2.0
 01/21  03:00:00,20.5,40000.0,3.0
 01/21  04:00:00,20.5,40000.0,4.0"""
big_output = """Date/Time,Variable 1 [C](Hourly),Variable 2 [W](Hourly),Variable 3 [W](Hourly)
 01/21  01:00:00,20.5,50000.0,1.0
 01/21  02:00:00,20.5,40000.0,2.0
 01/21  03:00:00,20.5,40000.0,3.0
 01/21  04:00:00,20.5,40000.0,4.0"""

f_csv = open('eplusout.csv', 'w')
f_mtr = open('eplusmtr.csv', 'w')
f_zsz = open('epluszsz.csv', 'w')
f_ssz = open('eplusssz.csv', 'w')
if output_mode == 'base':
    written = True
    f_csv.write(base_output)
    f_mtr.write(base_output)
    f_zsz.write(base_output)
    f_ssz.write(base_output)
elif output_mode == 'smalldiffs':
    written = True
    f_csv.write(small_output)
    f_mtr.write(small_output)
    f_zsz.write(small_output)
    f_ssz.write(small_output)
elif output_mode == 'bigdiffs':
    written = True
    f_csv.write(big_output)
    f_mtr.write(big_output)
    f_zsz.write(big_output)
    f_ssz.write(big_output)
else:
    written = False

f_csv.close()
f_mtr.close()
f_zsz.close()
f_ssz.close()

if written:
    sys.exit(0)
else:
    sys.exit(1)
