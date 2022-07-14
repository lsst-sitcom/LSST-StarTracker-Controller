#!/bin/bash
index=${1:-301}
if [ $1 -eq 301 ]; then
  config="--override=dsmdev.yaml"
else
  config=""
fi
python develop/csc_command.py --index=${index} start ${config}
python develop/csc_command.py --index=${index} enable

