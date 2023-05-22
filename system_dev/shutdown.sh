#!/bin/bash
index=${1:-301}
python csc_command.py --index=${index} disable
python csc_command.py --index=${index} standby
python csc_command.py --index=${index} exitControl
