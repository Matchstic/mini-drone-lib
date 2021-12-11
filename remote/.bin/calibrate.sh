#!/bin/bash

.bin/deps.sh $1
.bin/pyboard.py -d $1 calibration.py