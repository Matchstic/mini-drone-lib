"""
Matt Clarke 2021.

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

import struct
import time
import socket

class Drone:
    """
    This class handles sending commands to the remote drone.

    Exported methods:
    - videoType()
    - firmware()
    - connect()
    - setup()
    - takeoff()
    - arm()
    - control(throttle, pitch, roll, yaw)

    Note: no internal state keeping is done internally. This means
    you technically can call any method at any time. It is up to you to
    handle the current state!
    """

    udpsocket = None
    tcpsocket = None

    videoType_ = None
    firmware_  = None

    def videoType(self):
        """
        A getter for the type of video output the drone supports.

        Note: no implementation is provided to access this feed.

        Returns:
            A string or None
        """

        return self.videoType_


    def firmware(self):
        """
        A getter for the firmware version of the drone.

        For example, "V6.1".

        Returns:
            A string or None
        """

        return self.firmware_

    def connect(self, ip = '192.168.1.1'):
        """
        Sets up the sockets used for communication to the drone.

        It is expected that you have already connected to the drone's wireless network
        ahead of calling this method.

        Parameters:
            ip (string): IP address of the drone. This is defaults to 192.168.1.1, but may differ by manufacturer.

        Returns:
            `True` if connection is established, otherwise `False`
        """

        self.udpsocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udpsocket.connect((ip, 8080))

        self.tcpsocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.tcpsocket.connect((ip, 8888))

        # Validate the connection worked
        droneIdCommand = self.__generateDroneIdCommand(1)

        try:
            self.udpsocket.send(droneIdCommand)
            return True
        except:
           return False

    def setup(self):
        """
        Sends appropriate commands to arm the drone. After arming, videoType and firmware
        is available.

        Note: this will raise an exception if connection has been lost.
        """

        droneIdCommand = self.__generateDroneIdCommand(1)
        dateCommand    = self.__generateSetDateCommand(None)
        unknownCommand = self.__generateSecondSetupCommand()

        # No data to recieve on these two
        self.safeSend(droneIdCommand)
        self.safeSend(dateCommand)
        self.safeSend(unknownCommand)

        # Get drone video type
        self.safeSend(b'\x42')
        self.videoType_ = self.recieve(6).decode('ascii')

        # Get drone firmware
        # Due to seemingly a drone-side bug, gotta call this twice
        self.safeSend(b'\x28')
        self.recieve(6)
        self.safeSend(b'\x28')
        self.firmware_ = self.recieve(6).decode('ascii')

        # Send first heartbeat
        self.safeSendTcp(self.__generateHeartbeatCommand())
        self.recieveTcp(20) # ignore


    def idle(self):
        """
        Sends an "idle" control command. This is needed for the drone to recognise
        that you have connected, before calling takeoff() or arm().

        Note: execution time is 0.01s, suitable for calling at 100Hz.

        Note: this will raise an exception if connection has been lost.
        """

        controlPacket = self.__generateControlCommand(0.5, 0.5, 0.5, 0.5)
        self.safeSend(controlPacket)


    def takeoff(self):
        """
        Sends a takeoff command to the drone

        You should call this in a loop for as long as you want the takeoff to run.
        A reasonable loop duration is 500ms.

        Note: this is not strictly required to start a flight. You can instead call
        arm() then control() in sequence, to more finely control the takeoff.

        Note: this will raise an exception if connection has been lost.
        """

        controlPacket = self.__generateTakeoffCommand()
        self.safeSend(controlPacket)

    def arm(self):
        """
        Arms the drone for a manual takeoff, instead of calling takeoff().

        Once motors spin up, you need to call control() with a high enough throttle
        to takeoff, within a short timeframe. Otherwise, the drone will automatically
        disarm itself.

        Note: this will raise an exception if connection has been lost.
        """

        self.control(1.0, 0.5, 0.5, 0.5)
        self.control(0.5, 0.5, 0.5, 0.5)

    def control(self, throttle, pitch, roll, yaw):
        """
        Sends a control command to the drone, to set the current:

        - throttle
        - pitch
        - roll
        - yaw

        Note: execution time is 0.01s, suitable for calling at 100Hz in a simple loop.
        Note: this will raise an exception if connection has been lost.

        Parameters:
            throttle (float): Throttle %, [0.0 to 1.0] (< 0.5 to descend, > 0.5 to ascend)
            pitch    (float): Pitch angle, [0.0 to 1.0] (< 0.5 backward, > 0.5 forward)
            roll     (float): Roll angle, [0.0 to 1.0] (< 0.5 left, > 0.5 right)
            yaw      (float): Yaw amount, [0.0 | 1.0] (0.0 == rotate left, 1.0 == rotate right)
        """

        controlPacket = self.__generateControlCommand(throttle, pitch, roll, yaw)
        self.safeSend(controlPacket)

    #############################################################################
    # Private - Communication
    #############################################################################

    # Sends data to the remote socket. On error, will change state as expected
    def safeSend(self, data):
        try:
            time.sleep(0.01)
            self.udpsocket.send(data)
        except KeyboardInterrupt as e:
            raise e
        except Exception as e:
            print('send ' + str(e))
            raise e

    def safeSendTcp(self, data):
        try:
            time.sleep(0.01)
            self.tcpsocket.send(data)
        except KeyboardInterrupt as e:
            raise e
        except Exception as e:
            print('send (tcp) ' + str(e))
            raise e

    # Recieves data from the remote
    def recieve(self, bufferSize):
        try:
            return self.udpsocket.recv(bufferSize)
        except Exception as e:
            print('recv ' + str(e))
            return None

    def recieveTcp(self, bufferSize):
        try:
            return self.tcpsocket.recv(bufferSize)
        except Exception as e:
            print('recv ' + str(e))
            return None

    #############################################################################
    # Private - Command generation
    #############################################################################

    def __generateDroneIdCommand(self, id):
        return b'\x0f\xc0\xa8\x01' + struct.pack('B', id)

    def __generateSetDateCommand(self, now):
        # This command is a straight-up binary version of the below
        payload = 'date -s \"' + '2021-11-06 18:22:35' + '\"'
        return payload.encode()

    def __generateHeartbeatCommand(self):
        return b'\x00\x01\x02\x03\x04\x05\x06\x07\x08\x09\x25\x25'

    def __generateSecondSetupCommand(self):
        # No idea what these do
        param1 = 0x0b
        param2 = 0x06
        param3 = 0x00
        param4 = 0x12
        param5 = 0x16
        param6 = 0x24

        return b'\x26\xe5\x07\x00\x00' + struct.pack('IIIIII', int(param1), int(param2), int(param3), int(param4), int(param5), int(param6))

    def __generateControlCommand(self, throttle, pitch, roll, yaw, command = 0x01, throttleTrim = 0x10, rollTrim = 0x10, pitchTrim = 0x10):
        # params are floats between 0.0 and 1.0

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

        endByte = self.__endByteCalc(int(throttleScaled), int(yawScaled), int(pitchScaled), int(rollScaled), throttleTrim, rollTrim, pitchTrim, command)
        if endByte < 0x0:
            endByte = 0x0 - endByte
        elif endByte > 0xff:
            endByte = endByte - 0xff - 1

        return header + struct.pack('BBBBBBBBB', int(throttleScaled), int(yawScaled), int(pitchScaled), int(rollScaled), throttleTrim, pitchTrim, rollTrim, command, int(endByte))

    # No idea what this value represents, but this appears to calculate it correctly
    def __endByteCalc(self, throttle, yaw, pitch, roll, throttleTrim, rollTrim, pitchTrim, command):
        return 0x87 + (0x7f - throttle) + (0x40 - yaw) + (0x40 - pitch) + (0x40 - roll) + (0x10 - throttleTrim) + (0x10 - rollTrim) + (0x10 - pitchTrim) + (0x01 - command)

    def __generateTakeoffCommand(self):
        return b'\xff\x08\x7f\x40\x40\x40\x90\x10\x10\x41\xc7'