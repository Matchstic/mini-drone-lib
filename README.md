## MINI RC -based drone control

Mega barebones right now. Please bear with me as I build out this repo, as well as improving documentation.

This repo contains utils allowing you to control toy drones over WiFi that make use of the "MINI RC" app (or its many re-skins).

Need `pip install getkey` to run `localcontrol.py`. Keyboard controls:

- throttle -> arrow up/arrow down
- roll     -> arrow left/arrow right
- pitch    -> W/S
- yaw      -> A/D

### Knowledge source

I built this by reverse engineering the mentioned "MINI RC" app; via static analysis and by hooking method calls to AsyncSocket at runtime.

`minirclogger` is the iOSOpenDev-based tweak used to do runtime analysis.

### Usage (local testing)

1. Connect dev machine to hotspot of drone
2. Run `localcontrol.py`
3. Once you see payloads starting with `ff08` being sent in console, tap the up arrow key to arm
4. Takeoff with up arrow (will set throttle to 80%)
5. Land with down arrow

### Usage (remote)

0. Update scripts in `.bin/` to reflect the TTY of your board
1. Deploy dependencies to ESP32 -> `.bin/deps.sh`
2. Setup calibration of the IMU -> `.bin/pyboard.py -d /dev/<tty_of_board> calibration.py`
3. Deploy main application      -> `.bin/deploy.sh`

The drone should change visual state as if you'd connected a real controller to it.

To takeoff, move the IMU in a sharp upwards motion.

Flip the IMU upside down to force motors to 0% speed.

### License

GPL-3.0
