"""
Matt Clarke 2021.
Script using to calibrate the BNO055, and save the results to a file.

You likely will need to tweak line 23 to match your hardware configuration.

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

from bno055 import *
import machine
import time

i2c = machine.SoftI2C(scl=machine.Pin(22), sda=machine.Pin(21), timeout=1000)
imu = BNO055(i2c)

def main():
    while True:
        time.sleep(0.1)
        if not imu.calibrated():
            # Do calibration routine, and save sensor offsets
            print('Calibration status: sys {} gyro {} accel {} mag {}'.format(*imu.cal_status()))

        else:
            # Save offsets to file, and exit
            offsets = imu.sensorOffsets()
            print(offsets)

            f = open('calibration.bin', 'w')
            f.write(offsets)
            f.close()

            print('Saved calibration offsets to file')

            break

if __name__ == '__main__':
    main()