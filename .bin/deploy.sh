#!/bin/bash

.bin/deps.sh
.bin/pyboard.py -d /dev/tty.usbserial-0238732D -f cp gesture-control.py :main.py