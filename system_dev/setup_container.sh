#!/bin/bash
cd
mkdir data
cd develop/ts_config_ocs
eups declare -r . -t $USER ts_config_ocs
cd ../ts_genericcamera
eups declare -r . -t $USER ts_genericcamera
cd
