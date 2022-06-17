#!/bin/bash
index=${1:-4}
python develop/csc_command.py --index=${index} disable
python develop/csc_command.py --index=${index} standby
python develop/csc_command.py --index=${index} exitControl
