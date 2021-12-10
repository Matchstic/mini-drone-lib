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
            print('Calibration required: sys {} gyro {} accel {} mag {}'.format(*imu.cal_status()))

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