'''
Debug script to log IMU data
'''

from bno055 import *
import machine
import time

i2c = machine.SoftI2C(scl=machine.Pin(22), sda=machine.Pin(21), timeout=1000)
imu = BNO055(i2c)
calibrated = False

def clear():
    print("\x1B\x5B2J", end="")
    print("\x1B\x5BH", end="")

def logLoop():
    global calibrated
    global imu

    while True:
        time.sleep(0.05)
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