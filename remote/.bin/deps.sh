#!/bin/bash

.bin/pyboard.py -d $1 -f cp micropython-bno055/bno055.py :bno055.py
.bin/pyboard.py -d $1 -f cp micropython-bno055/bno055_base.py :bno055_base.py
.bin/pyboard.py -d $1 -f cp micropython-dotstar/micropython_dotstar.py :dotstar.py
.bin/pyboard.py -d $1 -f cp ../lib/drone.py :drone.py
.bin/pyboard.py -d $1 -f cp throttle.py :throttle.py