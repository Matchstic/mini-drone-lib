import struct
from enum import Enum
import threading
import socket
import time
from datetime import datetime
from getkey import getkey, keys

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

class State(Enum):
    SEARCHING_WIFI    = 1
    SOCKET_CREATE     = 2
    SOCKET_CONNECTING = 3
    SOCKET_CONNECTED  = 4
    CONTROL_LOOP      = 5
    INTERRUPT         = 6

# Useful when translated to MiniPython for embedded platform
wifiConnected = True

# Current application state - start at connecting to the remote socket for
# local control
state = State.SOCKET_CREATE

controlState = {
    'throttle': 0.5,
    'pitch': 0.5,
    'roll': 0.5,
    'yaw': 0.5
}

lastKeyChange = 0

udpsocket = None
tcpsocket = None

# Thread used to monitor keyboard input for control state
def keycodeThread():
    global lastKeyChange
    global controlState

    while state != State.INTERRUPT:

        key = getkey(blocking=True)

        # throttle
        if key == keys.UP:
            controlState['throttle'] = 0.85
        elif key == keys.DOWN:
            controlState['throttle'] = 0.0
        else:
            controlState['throttle'] = 0.5

        # roll
        if key == keys.LEFT:
            controlState['roll'] = 0.3
        elif key == keys.RIGHT:
            controlState['roll'] = 0.7
        else:
            controlState['roll'] = 0.5

        # pitch
        if key == 'w':
            controlState['pitch'] = 0.3
        elif key == 's':
            controlState['pitch'] = 0.7
        else:
            controlState['pitch'] = 0.5

        # yaw - note: its 100% or 0% for yaw, no scaling
        if key == 'a':
            controlState['yaw'] = 0.0
        elif key == 'd':
            controlState['yaw'] = 1.0
        else:
            controlState['yaw'] = 0.5

        lastKeyChange = int(round(time.time() * 1000))

def keytimeoutThread():
    # wtf is this. why is blocking a thing boooooooooo

    global lastKeyChange
    global controlState

    while state != State.INTERRUPT:
        if lastKeyChange > 0:
            now = int(round(time.time() * 1000))

            if now - lastKeyChange > 200:
                controlState = {
                    'throttle': 0.5,
                    'pitch': 0.5,
                    'roll': 0.5,
                    'yaw': 0.5
                }


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
    # Setup keycode thread
    keycodes = threading.Thread(target=keycodeThread, daemon=True)
    keycodes.start()

    keycodesHack = threading.Thread(target=keytimeoutThread, daemon=True)
    keycodesHack.start()

    # Create control loop
    try:
        while True:

            if state == State.SEARCHING_WIFI:
                # Not implemented for local control
                pass
            elif state == State.SOCKET_CREATE:
                print('Socket created')

                # Create socket connections
                udpsocket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
                udpsocket.connect(('192.168.1.1', 8080))

                tcpsocket = socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM)
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
                except KeyboardInterrupt as e:
                    raise e
                except:
                    # recreate the socket and reconnect
                    state = State.SOCKET_CREATE

            elif state == State.SOCKET_CONNECTED:
                print('Socket connected')

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
                # Poll socket data
                # Send control packet
                # Send keep-alive?

                # Get drone firmware as a keep-alive
                safeSend(b'\x28')
                recieve(6)

                # Send heartbeat + flush TCP buffer
                safeSendTcp(generateHeartbeatCommand())
                recieveTcp(20)

                controlPacket = generateControlCommand(controlState['throttle'], controlState['pitch'], controlState['roll'], controlState['yaw'])
                safeSend(controlPacket)

                print('sent ' + str(controlPacket.hex()))

    except KeyboardInterrupt as e:
        state = State.INTERRUPT

        udpsocket.close()
        tcpsocket.close()

    # keycodes.join()
    # keycodesHack.join()