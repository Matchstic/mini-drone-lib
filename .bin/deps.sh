#!/bin/bash

.bin/pyboard.py -d /dev/tty.usbserial-0238732D -f cp bno055.py :bno055.py
.bin/pyboard.py -d /dev/tty.usbserial-0238732D -f cp bno055_base.py :bno055_base.py
.bin/pyboard.py -d /dev/tty.usbserial-0238732D -f cp dotstar.py :dotstar.py
.bin/pyboard.py -d /dev/tty.usbserial-0238732D -f cp throttle.py :throttle.py