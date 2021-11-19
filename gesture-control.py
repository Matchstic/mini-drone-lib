import struct
import socket
import time
import math
import network

from bno055 import *
import machine
from dotstar import DotStar

WIRELESS_SSID = 'MINI RC_6DC444'

#############################################################################
# Command generation
#############################################################################

def generateDroneIdCommand(id):
    return b'\x0f\xc0\xa8\x01' + struct.pack('B', id)

def generateSetDateCommand(now):
    # This command is a straight-up binary version of the below
    payload = 'date -s \"' + '2021-11-06 18:22:35' + '\"'
    return payload.encode()

def generateHeartbeatCommand():
    return b'\x00\x01\x02\x03\x04\x05\x06\x07\x08\x09\x25\x25'

def generateSecondSetupCommand():
    # No idea what these do
    param1 = 0x0b
    param2 = 0x06
    param3 = 0x00
    param4 = 0x12
    param5 = 0x16
    param6 = 0x24

    return b'\x26\xe5\x07\x00\x00' + struct.pack('IIIIII', int(param1), int(param2), int(param3), int(param4), int(param5), int(param6))

def generateControlCommand(throttle, pitch, roll, yaw, command = 0x01, leftTrim = 0x10, rightTrim = 0x10, pitchTrim = 0x10):
    # params are floats between 0.0 and 1.0

    # throttle is 2 bytes between 003d and ff3b
    # 50% (default) == 7f40

    header = b'\xff\x08'

    throttleScaled = 0xff * throttle
    if throttleScaled > 0xff: throttleScaled = 0xff
    elif throttleScaled < 0x00: throttleScaled = 0x00

    pitchScaled = 0x80 * pitch
    if pitchScaled >= 0x7e: pitchScaled = 0x7f
    elif pitchScaled < 0x00: pitchScaled = 0x00

    rollScaled = 0x80 * roll
    if rollScaled >= 0x7e: rollScaled = 0x7f
    elif rollScaled < 0x00: rollScaled = 0x00

    yawScaled = 0x80 * yaw
    if yawScaled >= 0x7e: yawScaled = 0x7f
    elif yawScaled < 0x00: yawScaled = 0x00

    endByte = endByteCalc(int(throttleScaled), int(yawScaled), int(pitchScaled), int(rollScaled), leftTrim, rightTrim, pitchTrim)
    if endByte < 0x0:
        endByte = 0x0 - endByte
    elif endByte > 0xff:
        endByte = endByte - 0xff - 1

    return header + struct.pack('BBBBBBBBB', int(throttleScaled), int(yawScaled), int(pitchScaled), int(rollScaled), leftTrim, pitchTrim, rightTrim, command, int(endByte))

# No idea what this value represents, but this appears to calculate it correctly
def endByteCalc(throttle, yaw, pitch, roll, leftTrim, rightTrim, pitchTrim):
    return 0x87 + (0x7f - throttle) + (0x40 - yaw) + (0x40 - pitch) + (0x40 - roll) + (0x10 - leftTrim) + (0x10 - rightTrim) + (0x10 - pitchTrim)

#############################################################################
# Control logic
#############################################################################

class State():
    INIT              = 0
    SEARCHING_WIFI    = 1
    CONNECTING_WIFI   = 2
    SOCKET_CREATE     = 3
    SOCKET_CONNECTING = 4
    SOCKET_CONNECTED  = 5
    CONTROL_LOOP      = 6
    CALIBRATION       = 7

# Current application state - start at connecting to the remote socket for
# local control
state = State.INIT

wlan = None

udpsocket = None
tcpsocket = None

i2c = machine.SoftI2C(scl=machine.Pin(22), sda=machine.Pin(21), timeout=1000)
imu = BNO055(i2c)
spi = machine.SoftSPI(sck=machine.Pin(12), mosi=machine.Pin(13), miso=machine.Pin(18))
dotstar = DotStar(spi, 1)

throttleStartTime = 0
throttleMagnitude = 0
throttleSign      = 0
throttleValue     = 0.5
throttleAcc       = 0

'''
Throttle is driven by linear acceleration in the z axis.

The idea is that the user's movement is tracked to find the peak
acceleration before movement slows again. This is then translated
into a decay function, which reduces the throttle over time.

The greater the acceleration, the longer this decay occurs, resulting
in a longer period of acceleration on the remote hardware. As a result,
this produces a larger vertical translation.
'''
class Throttle():
    MINIMUM       = 0
    PEAK_POS      = 1
    PEAK_NEG      = 2
    DECAY         = 3

    NEXT_PEAK_POS = 1
    NEXT_PEAK_NONE = 0
    NEXT_PEAK_NEG = -1

    INITIAL_SCALE = 2.5

    state = MINIMUM
    nextPeakState = NEXT_PEAK_NONE

    lastPeakAcc   = 0
    value         = 0.5
    decayStart    = 0
    decayModifier = 0.5
    decayFn       = lambda time : 0.5
    decayExit     = lambda value : True

    def applyScale(self, x, scaleFactor):
        pow = 0
        if x < 0:
            pow = -((-x) ** scaleFactor)
        elif x > 0:
            pow = x ** scaleFactor

        res = (pow + 64.0) / 128.0

        if res > 1.0: res = 1.0
        elif res < 0.0: res = 0.0

        return res

    def tick(self, acc, midpoint):
        if self.state == Throttle.MINIMUM:

            # If beyond the midpoint value, then start trying to record the current peak
            # in this acceleration phase. Additionally, record which direction the acceleration
            # is heading
            if acc > midpoint:
                self.nextPeakState = Throttle.NEXT_PEAK_POS
                if acc > self.lastPeakAcc:
                    self.lastPeakAcc = acc
                    self.value = self.applyScale(acc, Throttle.INITIAL_SCALE)

                    print('new peak acc (pos),' + str(self.lastPeakAcc) + ',' + str(self.value))

            elif acc < 0 - midpoint:
                self.nextPeakState = Throttle.NEXT_PEAK_NEG
                if acc < self.lastPeakAcc:
                    self.lastPeakAcc = acc
                    self.value = self.applyScale(acc, Throttle.INITIAL_SCALE) * 0.7

                    print('new peak acc (neg),' + str(self.lastPeakAcc) + ',' + str(self.value))

            elif self.nextPeakState != Throttle.NEXT_PEAK_NONE:
                # Move to peak state now that we're at midpoint again
                self.state = Throttle.PEAK_POS if self.nextPeakState == Throttle.NEXT_PEAK_POS else Throttle.PEAK_NEG

                self.lastPeakAcc = 0
                self.nextPeakState = Throttle.NEXT_PEAK_NONE

        elif self.state == Throttle.PEAK_POS:
            # Setup the decay phase

            self.decayModifier = self.value
            self.decayFn       = lambda time : 0.4 * ((0.0 - (time ** 3))) + self.decayModifier
            self.decayExit     = lambda value : value < 0.56
            self.decayStart = time.ticks_ms()

            self.state = Throttle.DECAY

        elif self.state == Throttle.PEAK_NEG:
            # Setup the decay phase

            self.decayModifier = self.value
            self.decayFn       = lambda time : (0.4 * (time ** 3)) + self.decayModifier
            self.decayExit     = lambda value : value > 0.44
            self.decayStart = time.ticks_ms()

            self.state = Throttle.DECAY

        elif self.state == Throttle.DECAY:
            # Compute the decay

            # New movement during decay, cycle back around and restart
            #if acc > midpoint or acc < 0.0 - midpoint:
            #    print('Midpoint exceeded during decay, restart')
            #    self.state = Throttle.MINIMUM
            #    self.tick(acc, midpoint)
            #
            #    return

            # Compute decayed throttle value, and exit if needed
            diff = time.ticks_diff(time.ticks_ms(), self.decayStart) / 1000.0
            self.value = self.decayFn(diff)

            if self.decayExit(self.value):
                self.value = 0.5
                self.state = Throttle.MINIMUM

            print('decayed,' + str(acc) + ',' + str(self.value))

    def compute(self):
        return self.value

throttleManager = Throttle()

def computeControlState():
    global throttleManager

    rollFactor = 180
    pitchFactor = 180

    yaw = 0.5

    [x,y,z] = imu.lin_acc()
    [heading, roll, pitch] = imu.euler()

    throttleManager.tick(z, 0.3)
    throttle = throttleManager.compute()

    # Euler angle handling
    roll = 1.0 - ((roll / rollFactor) + 0.5)
    if roll > 1.0: roll = 1.0
    elif roll < 0.0: roll = 0.0
    elif roll > 0.44 and roll < 0.56: roll = 0.5

    pitch = 1.0 - ((pitch / pitchFactor) + 0.5)
    if pitch > 1.0: pitch = 1.0
    elif pitch < 0.0: pitch = 0.0
    elif pitch > 0.44 and pitch < 0.56: roll = 0.5

    return [throttle, pitch, roll, yaw]

# Sends data to the remote socket. On error, will change state as expected
def safeSend(data):
    global state
    global udpsocket

    try:
        time.sleep(0.01)
        udpsocket.send(data)
    except KeyboardInterrupt as e:
        raise e
    except Exception as e:
        print('send ' + str(e))

        # recreate the socket and reconnect
        state = State.SOCKET_CREATE

def safeSendTcp(data):
    global tcpsocket

    try:
        time.sleep(0.01)
        tcpsocket.send(data)
    except KeyboardInterrupt as e:
        raise e
    except Exception as e:
        print('send (tcp) ' + str(e))

# Recieves data from the remote
def recieve(bufferSize):
    global udpsocket

    try:
        return udpsocket.recv(bufferSize)
    except Exception as e:
        print('recv ' + str(e))
        return None

def recieveTcp(bufferSize):
    global tcpsocket

    try:
        return tcpsocket.recv(bufferSize)
    except Exception as e:
        print('recv ' + str(e))
        return None

if __name__ == '__main__':
    # Turn on LED
    machine.Pin(13, machine.Pin.OUT, None)
    machine.Pin(13).value(False)

    # Create control loop
    while True:
        try:
            if state == State.INIT:
                dotstar[0] = (128, 0, 0) # Red

                if imu.calibrated() == False:
                    state = State.CALIBRATION
                    continue

                wlan = network.WLAN(network.STA_IF)
                if wlan.isconnected():
                    wlan.disconnect()

                wlan.active(True)

                state = State.SEARCHING_WIFI

                print('Initialised')
            elif state == State.SEARCHING_WIFI:

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

                # Create socket connections
                udpsocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                udpsocket.connect(('192.168.1.1', 8080))

                tcpsocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                tcpsocket.connect(('192.168.1.1', 8888))

                state = State.SOCKET_CONNECTING

            elif state == State.SOCKET_CONNECTING:
                print('Socket connecting...')

                # Poll socket for connected status
                # Handle state of failed to connect -> pause
                # and then update state to recreate?

                # Using the drone ID command to check if the socket is open
                droneIdCommand = generateDroneIdCommand(1)

                try:
                    udpsocket.send(droneIdCommand)
                    state = State.SOCKET_CONNECTED
                except:
                    # recreate the socket and reconnect
                    state = State.SOCKET_CREATE

            elif state == State.SOCKET_CONNECTED:
                print('Socket connected')
                dotstar[0] = (0, 128, 0) # Green

                droneIdCommand = generateDroneIdCommand(1)
                dateCommand    = generateSetDateCommand(None)
                unknownCommand = generateSecondSetupCommand()

                # No data to recieve on these two
                safeSend(droneIdCommand)
                safeSend(dateCommand)
                safeSend(unknownCommand)

                # Get drone video type
                safeSend(b'\x42')
                print('Video type: ' + recieve(6).decode('ascii'))

                # Get drone firmware
                # Due to seemingly a drone-side bug, gotta call this twice
                safeSend(b'\x28')
                recieve(6)
                safeSend(b'\x28')
                print('Firmware: ' + recieve(6).decode('ascii'))

                # Send first heartbeat
                safeSendTcp(generateHeartbeatCommand())
                print('TCP recv: ' + recieveTcp(20).decode('ascii'))

                state = State.CONTROL_LOOP

            elif state == State.CONTROL_LOOP:
                if not wlan.isconnected():
                    state = State.CONNECTING_WIFI
                    continue

                [throttle, pitch, roll, yaw] = computeControlState()
                controlPacket = generateControlCommand(throttle, pitch, roll, yaw)
                safeSend(controlPacket)

                # print('sent ' + str(controlPacket))
            elif state == State.CALIBRATION:
                [sys, gyro, accel, mag] = imu.cal_status()
                print('Calibration required: sys {} gyro {} accel {} mag {}'.format(*imu.cal_status()))

                if accel == 3:
                    state = State.INIT

        except Exception as e:
            print(e)

            wlan.disconnect()

            state = State.SEARCHING_WIFI
