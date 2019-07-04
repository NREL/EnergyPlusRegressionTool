#!/usr/bin/env python

"""
So we are going to replicate just a few of the core functions of E+ in this binary...in a super silly way
1) We are going to make it expect an in.idf - not doing the full CLI
2) We expect this file to be JSON
  2a) If it's not JSON, E+ will just exit with zero and do nothing
  2b) If it is JSON, we will try to use the inputs to create the outputs...here are the possible config options
{
  "config": {
    "run_time_string": "01hr 20min  0.17sec",
    "num_warnings": 1,
    "num_severe": 0,
    "end_state": "fatal" / "success" / "crash" / "unknown",
    "eso_results": "base" / "smalldiffs" / "bigdiffs",
    "txt_results": "base" / "diffs",
    "extra_data": "<freeform>" -- this is something like a flag for auxiliary tools to pick up
  }
}
"""

import json
import sys

with open('in.idf') as f_idf:
    idf_body = f_idf.read()
    # noinspection PyBroadException
    try:
        config = json.loads(idf_body)['config']
    except:
        sys.exit(0)

if 'eso_results' in config:
    with open('eplusout.eso', 'w') as f_eso:
        f_eso.write(json.dumps({'output': config['eso_results']}))

if 'txt_results' in config:
    f_audit = open('eplusout.audit', 'w')
    f_bnd = open('eplusout.bnd', 'w')
    f_dxf = open('eplusout.dxf', 'w')
    f_eio = open('eplusout.eio', 'w')
    f_mdd = open('eplusout.mdd', 'w')
    f_mtd = open('eplusout.mtd', 'w')
    f_rdd = open('eplusout.rdd', 'w')
    f_shd = open('eplusout.shd', 'w')
    f_err = open('eplusout.err', 'w')
    f_delightin = open('eplusout.delightin', 'w')
    f_delightout = open('eplusout.delightout', 'w')
    if config['txt_results'] == 'base':
        f_audit.write('Line 1\nLine 2\n(idf)=hello')
        f_bnd.write('Line 1\nLine 2')
        f_dxf.write('Line 1\nLine 2')
        f_eio.write('Line 1\nLine 2')
        f_mdd.write('Line 1\nLine 2')
        f_mtd.write('Line 1\nLine 2')
        f_rdd.write('Line 1\nLine 2')
        f_shd.write('Line 1\nLine 2')
        f_err.write('Line 1\nLine 2')
        f_delightin.write('Line 1\nLine 2')
        f_delightout.write('Line 1\nLine 2')
    else:
        f_audit.write('Line 1\nLine 3\n(idf)=world')  # note this will always be different but should not cause diffs
        f_bnd.write('Line 1\nLine 3')
        f_dxf.write('Line 1\nLine 3')
        f_eio.write('Line 1\nLine 3')
        f_mdd.write('Line 1\nLine 3')
        f_mtd.write('Line 1\nLine 3')
        f_rdd.write('Line 1\nLine 3')
        f_shd.write('Line 1\nLine 3')
        f_err.write('Line 1\nLine 3')
        f_delightin.write('Line 1\nLine 3')
        f_delightout.write('Line 1\nLine 3')
    f_audit.close()
    f_bnd.close()
    f_dxf.close()
    f_eio.close()
    f_mdd.close()
    f_mtd.close()
    f_rdd.close()
    f_shd.close()
    f_err.close()
    f_delightin.close()
    f_delightout.close()

with open('eplustbl.htm', 'w') as f_tbl:
    f_tbl.write("""<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN""http://www.w3.org/TR/html4/loose.dtd">
<html>
<head>
<title> Building FRESNO ANN HTG 99% CONDNS DB **
  2018-11-05
  09:17:42
 - EnergyPlus</title>
</head>
<body>
<b></b><br><br>
<b>Site and Source Energy</b><br><br>
<!-- FullName:Annual Building Utility Performance Summary_Entire Facility_Site and Source Energy-->
<table border="1" cellpadding="4" cellspacing="0">
  <tr><td></td>
    <td align="right">Total Energy [GJ]</td>
    <td align="right">Energy Per Total Building Area [MJ/m2]</td>
    <td align="right">Energy Per Conditioned Building Area [MJ/m2]</td>
  </tr>
  <tr>
    <td align="right">Total Site Energy</td>
    <td align="right">        0.00</td>
    <td align="right">        0.00</td>
    <td align="right">        0.00</td>
  </tr>
</table>
<br><br>
</body>
</html>
""")

# write some dummy text output files
dummy_text_files = [
    'readvars.audit',
    'eplusout.edd',
    'eplusout.wrl',
    'eplusout.sln',
    'eplusout.sci',
    'eplusout.map',
    'eplusout.dfs',
    'eplusscreen.csv'
]
for fn in dummy_text_files:
    with open(fn, 'w') as f:
        f.write('hello from ' + fn)

# and the glhe json file too
object_to_write = {
  "GHLE 1": {
    "Phys Data": {
      "BH Data": {
        "BH 1": {
          "X-Location": 0.0,
          "Y-Location": 0.0
        }
      },
      "BH Diameter": 0.114,
      "BH Length": 100.0,
      "BH Top Depth": 1.0,
      "Flow Rate": 0.00100944,
      "Grout k": 0.7443,
      "Grout rhoCp": 3900000.0,
      "Max Simulation Years": 1.0,
      "Pipe Diameter": 0.03341,
      "Pipe Thickness": 0.002984,
      "Pipe k": 0.3895,
      "Pipe rhoCP": 1770000.0,
      "Soil k": 2.5,
      "Soil rhoCp": 2500000.0,
      "U-tube Dist": 0.04913
    },
    "Response Factors": {
      "GFNC": [
        6.495588983283869
      ],
      "LNTTS": [
        -3.5
      ],
      "time": [
        33552648.247020558
      ]
    }
  }
}
with open('eplusout.glhe', 'w') as f_glhe:
    f_glhe.write(json.dumps(object_to_write))

# DO THIS LAST - it has sys.exit() calls - eplusout.end
num_warnings = config['num_warnings'] if 'num_warnings' in config else 0
num_severe = config['num_severe'] if 'num_severe' in config else 0
run_time = config['run_time_string'] if 'run_time_string' in config else '01hr 20min  0.17sec'
if 'end_state' in config and config['end_state'] == 'success':
    with open('eplusout.end', 'w') as f_end:
        f_end.write(
            'EnergyPlus Completed Successfully-- %s Warning; %s Severe Errors; Elapsed Time=%s' % (
                num_warnings, num_severe, run_time
            )
        )
    sys.exit(0)
elif 'end_state' in config and config['end_state'] == 'fatal':
    with open('eplusout.end', 'w') as f_end:
        f_end.write(
            'EnergyPlus Terminated--Fatal Error Detected. %s Warning; %s Severe Errors; Elapsed Time=%s' % (
                num_warnings, num_severe, run_time
            )
        )
    sys.exit(1)
elif 'end_state' in config and config['end_state'] == 'unknown':
    with open('eplusout.end', 'w') as f_end:
        f_end.write('Energ')  # maybe mimicking a weird out of disk space thing?
    sys.exit(1)
elif 'end_state' in config and config['end_state'] == 'crash':
    sys.exit(1)

# not sure what other condition would get us here, but ok
sys.exit(0)
