## MINI RC -based drone control

Mega barebones right now. This repo contains utils allowing you to control toy drones over WiFi that make use of the "MINI RC" app (or its many re-skins).

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


### Deployment

To deploy everything to your ESP32 device, run `.bin/deploy.sh`

### License

GPL-3.0
