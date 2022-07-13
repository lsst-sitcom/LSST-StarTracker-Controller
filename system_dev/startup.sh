#!/bin/bash
index=${1:-4}
if [ $1 -eq 4 ]; then
  config="--override=dsmdev.yaml"
else
  config=""
fi
python develop/csc_command.py --index=${index} start ${config}
python develop/csc_command.py --index=${index} enable

