"""
Matt Clarke 2021.
Example script to demonstrate usage of the Drone class.

Keyboard controls:
    ↑ / ↓: Throttle
    ← / →: Roll
    W / S: Pitch
    A / D: Yaw

Dependencies:
    - getkey

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

from enum import Enum
import threading
import time
from getkey import getkey, keys

from lib.drone import Drone

class State(Enum):
    SOCKET_CREATE     = 1
    SOCKET_CONNECTED  = 2
    TAKEOFF           = 3
    CONTROL_LOOP      = 4
    INTERRUPT         = 5

state = State.SOCKET_CREATE

controlState = {
    'throttle': 0.5,
    'pitch': 0.5,
    'roll': 0.5,
    'yaw': 0.5
}

lastKeyChange = 0

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
    # workaround for some weird blocking stuff with
    # getting currently pressed keys

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


if __name__ == '__main__':
    # Setup keycode thread
    keycodes = threading.Thread(target=keycodeThread, daemon=True)
    keycodes.start()

    # Hack for some input blocking related stuff
    keycodesHack = threading.Thread(target=keytimeoutThread, daemon=True)
    keycodesHack.start()

    drone = Drone()

    # Create control loop
    try:
        while True:

            if state == State.SOCKET_CREATE:

                if drone.connect():
                    state = State.SOCKET_CONNECTED

            elif state == State.SOCKET_CONNECTED:
                print('Socket connected')

                try:
                    drone.setup()
                    state = State.TAKEOFF
                except KeyboardInterrupt as e:
                    raise e
                except Exception as e:
                    state = State.SOCKET_CREATE

            elif state == State.TAKEOFF:
                if (controlState['throttle'] != 0.5 or
                    controlState['pitch'] != 0.5 or
                    controlState['roll'] != 0.5 or
                    controlState['yaw'] != 0.5):

                    startTime = time.time_ns() // 1_000_000

                    while (time.time_ns() // 1_000_000) - startTime < 500:
                        drone.takeoff()
                        time.sleep(0.01)

                    state = State.CONTROL_LOOP
                else:
                    drone.idle()

            elif state == State.CONTROL_LOOP:
                try:
                    drone.control(controlState['throttle'], controlState['pitch'], controlState['roll'], controlState['yaw'])
                except KeyboardInterrupt as e:
                    raise e
                except Exception as e:
                    state = State.SOCKET_CREATE

    except KeyboardInterrupt as e:
        state = State.INTERRUPT