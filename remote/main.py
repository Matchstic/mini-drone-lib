"""
Matt Clarke 2021.
Script using the drone library on an ESP32 device hooked up to a BNO055, for
full motion control.

You likely will need to tweak lines 49 and 50 to match your hardware
configuration.

This program is free software: you can redistribute it and/or modify it under
the terms of the GNU General Public License as published by the Free Software
Foundation, either version 3 of the License, or (at your option) any later
version.

This program is distributed in the hope that it will be useful, but WITHOUT
ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
You should have received a copy of the GNU General Public License along with
this program. If not, see <http://www.gnu.org/licenses/>.
"""

import time
import math
import network

from bno055 import *
import machine
from dotstar import DotStar
from throttle import Throttle

from drone import Drone

WIRELESS_SSID = 'MINI RC_6DC444'

class State():
    INIT              = 0
    SEARCHING_WIFI    = 1
    CONNECTING_WIFI   = 2
    SOCKET_CREATE     = 3
    SOCKET_CONNECTED  = 4
    TAKEOFF           = 5
    CONTROL_LOOP      = 6
    CALIBRATION       = 7

# Current application state - start at connecting to the remote socket for
# local control
state = State.INIT

wlan = None

i2c = machine.SoftI2C(scl=machine.Pin(22), sda=machine.Pin(21), timeout=1000)
spi = machine.SoftSPI(sck=machine.Pin(12), mosi=machine.Pin(13), miso=machine.Pin(18))
imu = BNO055(i2c)
dotstar = DotStar(spi, 1)
throttleManager = Throttle()
drone = Drone()

def computeControlState():
    global throttleManager

    rollFactor = 180
    pitchFactor = 155

    yaw = 0.5

    [x,y,z] = imu.lin_acc()
    [heading, roll, pitch] = imu.euler()

    ACCEL_VEL_TRANSITION =  10.0 / 1000.0
    DEG_2_RAD = 0.01745329251

    zVel = (ACCEL_VEL_TRANSITION * z / math.cos(DEG_2_RAD * z)) * 1000.0

    throttleManager.tick(zVel, 4)
    throttle = throttleManager.compute()

    if throttle > 1.0: throttle = 1.0
    elif throttle < 0.0: throttle = 0.0
    elif throttle > 0.48 and throttle < 0.52: throttle = 0.5

    if abs(pitch) > 140:
        return [0.0, 0.5, 0.5, 0.5]

    # Euler angle handling
    roll = 1.0 - ((roll / rollFactor) + 0.5)
    if roll > 1.0: roll = 1.0
    elif roll < 0.0: roll = 0.0
    elif roll > 0.44 and roll < 0.56: roll = 0.5

    pitch = 1.0 - ((pitch / pitchFactor) + 0.5)
    if pitch > 1.0: pitch = 1.0
    elif pitch < 0.0: pitch = 0.0
    elif pitch > 0.44 and pitch < 0.56: pitch = 0.5

    return [throttle, pitch, roll, yaw]

if __name__ == '__main__':
    # Turn on LED
    machine.Pin(13, machine.Pin.OUT, None)
    machine.Pin(13).value(False)

    # Create control loop
    while True:
        try:
            if state == State.INIT:
                dotstar[0] = (128, 0, 0) # Red

                [system, gyro, acc, mag] = imu.cal_status()
                if gyro != 3 or acc != 3:
                    state = State.CALIBRATION
                    continue

                wlan = network.WLAN(network.STA_IF)
                if wlan.isconnected():
                    wlan.disconnect()

                wlan.active(True)

                state = State.SEARCHING_WIFI

                print('Initialised')
            elif state == State.SEARCHING_WIFI:
                dotstar[0] = (128, 0, 0) # Red

                wlan.connect(WIRELESS_SSID, '')
                state = State.CONNECTING_WIFI

                print('Connecting to ' + WIRELESS_SSID)

            elif state == State.CONNECTING_WIFI:
                dotstar[0] = (128, 100, 0) # Orange

                if not wlan.isconnected():
                    time.sleep(0.1)
                elif wlan.status() == network.STAT_GOT_IP:
                    state = State.SOCKET_CREATE
                elif wlan.status() != network.STAT_CONNECTING:
                    state = State.SEARCHING_WIFI

            elif state == State.SOCKET_CREATE:
                print('Socket creation')

                if drone.connect():
                    state = State.SOCKET_CONNECTED

            elif state == State.SOCKET_CONNECTED:
                print('Socket connected')

                try:
                    drone.setup()
                    state = State.TAKEOFF
                except Exception as e:
                    state = State.SOCKET_CREATE

            elif state == State.TAKEOFF:
                dotstar[0] = (0, 128, 0) # Green

                if not wlan.isconnected():
                    state = State.CONNECTING_WIFI
                    continue

                [throttle, pitch, roll, yaw] = computeControlState()
                if roll != 0.5:
                    print('Sending takeoff command')

                    startTime = time.ticks_ms()

                    while time.ticks_diff(time.ticks_ms(), startTime) < 500:
                        drone.takeoff()
                        time.sleep(0.01)

                    state = State.CONTROL_LOOP
                else:
                    drone.idle()

            elif state == State.CONTROL_LOOP:
                if not wlan.isconnected():
                    state = State.CONNECTING_WIFI
                    continue

                [throttle, pitch, roll, yaw] = computeControlState()
                drone.control(throttle, pitch, roll, yaw)

            elif state == State.CALIBRATION:
                try:
                    f = open('calibration.bin', 'r')
                    bytes = bytearray(f.read())
                    f.close()

                    imu.setOffsets(bytes)

                    time.sleep(1)

                    # Check status
                    [system, gyro, acc, mag] = imu.cal_status()
                    if gyro != 3 or acc != 3:
                        print('FAILED CALIBRATION! Please run calibration.py')
                    else:
                        print('Loaded calibration from file')
                        state = State.INIT

                except Exception as e:
                    print(e)
                    print('FAILED CALIBRATION! Please run calibration.py')

        except Exception as e:
            print(e)

            wlan.disconnect()

            state = State.SEARCHING_WIFI
