'''
Debug script to log IMU data
'''

from bno055 import *
import machine
import time
import math
from throttle import Throttle

i2c = machine.SoftI2C(scl=machine.Pin(22), sda=machine.Pin(21), timeout=1000)
imu = BNO055(i2c)
calibrated = False
throttleManager = Throttle()

def clear():
    print("\x1B\x5B2J", end="")
    print("\x1B\x5BH", end="")

def logLoop():
    global calibrated
    global imu

    xPos = 0
    yPos = 0
    zPos = 0
    zVel = 0

    try:
        f = open('calibration.bin', 'r')
        bytes = bytearray(f.read())
        f.close()

        imu.setOffsets(bytes)

        time.sleep(1)

        # Check status
        [sys, gyro, acc, mag] = imu.cal_status()
        if gyro != 3 or acc != 3:
            print('FAILED CALIBRATION! Please run calibration.py')
            return

    except Exception as e:
        print(e)
        print('FAILED CALIBRATION! Please run calibration.py')

        return

    while True:
        time.sleep(0.01)

        ACCEL_VEL_TRANSITION =  10.0 / 1000.0
        ACCEL_POS_TRANSITION = 0.5 * ACCEL_VEL_TRANSITION * ACCEL_VEL_TRANSITION
        DEG_2_RAD = 0.01745329251

        [x,y,z] = imu.lin_acc()

        xPos = xPos + ACCEL_POS_TRANSITION * x
        yPos = yPos + ACCEL_POS_TRANSITION * y
        zPos = zPos + ACCEL_POS_TRANSITION * z

        ACCEL_VEL_TRANSITION =  10.0 / 1000.0
        DEG_2_RAD = 0.01745329251

        zVel = (ACCEL_VEL_TRANSITION * z / math.cos(DEG_2_RAD * z)) * 1000.0

        throttleManager.tick(zVel, 2)
        throttle = throttleManager.compute()

        if throttle > 1.0: throttle = 1.0
        elif throttle < 0.0: throttle = 0.0
        elif throttle > 0.48 and throttle < 0.52: throttle = 0.5

        [heading, roll, pitch] = imu.euler()

        if abs(pitch) > 150:
            print('ABORT ABORT ABORT')

        rollFactor = 180
        pitchFactor = 180

        # Euler angle handling
        roll = 1.0 - ((roll / rollFactor) + 0.5)
        if roll > 1.0: roll = 1.0
        elif roll < 0.0: roll = 0.0
        elif roll > 0.44 and roll < 0.56: roll = 0.5

        pitch = 1.0 - ((pitch / pitchFactor) + 0.5)
        if pitch > 1.0: pitch = 1.0
        elif pitch < 0.0: pitch = 0.0
        elif pitch > 0.44 and pitch < 0.56: pitch = 0.5

        continue

        '''clear()
        if not calibrated:
            calibrated = imu.calibrated()
            print('Calibration required: sys {} gyro {} accel {} mag {}'.format(*imu.cal_status()))

        print('Temperature {}°C'.format(imu.temperature()))
        print('Mag       x {:5.0f}    y {:5.0f}     z {:5.0f}'.format(*imu.mag()))
        print('Gyro      x {:5.0f}    y {:5.0f}     z {:5.0f}'.format(*imu.gyro()))
        print('Accel     x {:5.1f}    y {:5.1f}     z {:5.1f}'.format(*imu.accel()))
        print('Lin acc.  x {:5.1f}    y {:5.1f}     z {:5.1f}'.format(*imu.lin_acc()))
        print('Gravity   x {:5.1f}    y {:5.1f}     z {:5.1f}'.format(*imu.gravity()))
        print('Heading     {:4.0f} roll {:4.0f} pitch {:4.0f}'.format(*imu.euler()))'''

        [x,y,z] = imu.lin_acc()

        throttleScale = 2.5
        rollScaling = 1.6
        pitchScaling = 1.6

        throttle = 0.5
        roll = 0.5
        pitch = 0.5

        def compute(x, scaleFactor):
            pow = 0
            if x < 0:
                pow = -((-x) ** scaleFactor)
            elif x > 0:
                pow = x ** scaleFactor

            res = (pow + 64.0) / 128.0

            if res > 1.0: res = 1.0
            elif res < 0.0: res = 0.0

            return res

        # Account for midpoint jitter
        if x < -0.3 or x > 0.3:
            roll = compute(x, rollScaling)
        if y < -0.3 or y > 0.3:
            pitch = compute(y, pitchScaling)
        if z < -0.3 or z > 0.3:
            throttle = compute(z, throttleScale)

        #print('throttle. raw: ' + str(z) + ', computed: ' + str(throttle))
        #print('pitch. raw: ' + str(y) + ', computed: ' + str(pitch))
        #print('roll. raw: ' + str(x) + ', computed: ' + str(roll))
        # print('' + str(z) + ',' + str(throttle))
        print('Heading     {:4.0f} roll {:4.0f} pitch {:4.0f}'.format(*imu.euler()))

        [heading, roll, pitch] = imu.euler()
        print((pitch / 100) + 0.5)

def main():
    logLoop()

if __name__ == '__main__':
    main()