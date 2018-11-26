#!/usr/bin/env python

import json
import sys

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
    "end_state": "fatal" / "success" / "crash"
    
    

"""

with open('in.idf') as f_idf:
    idf_body = f_idf.read()
    # noinspection PyBroadException
    try:
        config = json.loads(idf_body)['config']
    except:
        sys.exit(0)

# DO THIS LAST - it has sys.exit() calls - eplusout.end
num_warnings = config['num_warnings'] if 'num_warnings' in config else 0
num_severe = config['num_severe'] if 'num_severe' in config else 0
run_time = config['run_time_string'] if 'run_time_string' in config else '01hr 20min  0.17sec'
if 'end_state' in config and config['end_state'] == 'success':
    with open('eplusout.end') as f_end:
        f_end.write(
            'EnergyPlus Completed Successfully-- %s Warning; %s Severe Errors; Elapsed Time=%s' % (
                num_warnings, num_severe, run_time
            )
        )
    sys.exit(0)
elif 'end_state' in config and config['end_state'] == 'fatal':
    with open('eplusout.end') as f_end:
        f_end.write(
            'EnergyPlus Terminated--Fatal Error Detected. %s Warning; %s Severe Errors; Elapsed Time=%s' % (
                num_warnings, num_severe, run_time
            )
        )
    sys.exit(1)
elif 'end_state' in config and config['end_state'] == 'crash':
    sys.exit(1)

# not sure what other condition would get us here, but ok
sys.exit(0)
