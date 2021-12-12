#!/bin/bash

.bin/deps.sh $1
.bin/pyboard.py -d $1 -f cp main.py :main.py