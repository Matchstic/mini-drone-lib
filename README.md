# MINI Drone Library

This library supports communication to various toy drones that use the "MINI RC" companion app on iOS and Android.

### Supported devices

The "MINI RC" app itself is redistributed under other names with whitelabelled branding:

- AIRFUN UFO
- DH-UFO
- Exploration_UFO
- Jamara F1-X
- Gadnic UfO
- HT SMART
- Quadrone Hylander
- MINI ORION FPV
- MINI RC
- Polaroid PL300
- Promark VR
- RC-PRO
- S-IDEE S181W-S183W
- SH WIFI
- Sky Rider Breeze
- Vuelo Cosmos
- XHTECH
- XTREM RAIDERS

(I'm pretty sure that even "MINI RC" is a whitelabel rebrand of the original application)

In *theory* this library should support any small drone that use any of the above applications. If your drone is not supported
but DOES use one of the above apps, please check the host IP address of the drone - if not `192.168.1.1`, make sure to call
`connect('IP addr')` with the correct address.

**Known Supported Drones**
| Name | Link (e.g. Amazon) |
| ----------- | ----------- |
| tech rc Mini Drone | https://www.amazon.co.uk/dp/B07SW3YYTQ |

Please let me know if your drone works with this library, so that the above table can be expanded.

## Library

All library code is found inside `lib/` (surprise!).

To start using it, just import and create an instance:

```
from lib.drone import Drone

if drone.connect():
    drone.setup()
    drone.takeoff()
```

### Usage

| Method Name | Arguments   | Description | Return value |
| ----------- | ----------- | ----------- | ------------ |
| `connect()` | `ip (string)`: IP address of the drone. This is defaults to `192.168.1.1`, but may differ by manufacturer. | Sets up the sockets used for communication to the drone.<br />It is expected that you have already connected to the drone's wireless network ahead of calling this method. | `True` if connection is established, otherwise `False` |
| `setup()` | - | Sends appropriate commands to arm the drone. After arming, videoType and firmware is available.<br /><br />Note: this will raise an exception if connection has been lost. | void |
| `idle()` | - | Sends an "idle" control command. This is needed for the drone to recognise that you have connected, before calling `takeoff()` or `arm()`.<br /><br />Note: execution time is 0.01s, suitable for calling at 100Hz.<br /><br />Note: this will raise an exception if connection has been lost. | void |
| `takeoff()` | - | Sends a takeoff command to the drone.<br /><br />You should call this in a loop for as long as you want the takeoff to run. A reasonable loop duration is 500ms.<br /><br />Note: this is not strictly required to start a flight. You can instead call `arm()` then `control()` in sequence, to more finely control the takeoff.<br /><br />Note: this will raise an exception if connection has been lost. | void |
| `arm()` | - | Arms the drone for a manual takeoff, instead of calling takeoff().<br /><br />Once motors spin up, you need to call control() with a high enough throttle to takeoff, within a short timeframe. Otherwise, the drone will automatically disarm itself.<br /><br />Note: this will raise an exception if connection has been lost. | void |
| `control()` | `throttle (float)`: Throttle %, [0.0 to 1.0] (< 0.5 to descend, > 0.5 to ascend)<br />`pitch    (float)`: Pitch angle, [0.0 to 1.0] (< 0.5 backward, > 0.5 forward)<br />`roll     (float)`: Roll angle, [0.0 to 1.0] (< 0.5 left, > 0.5 right)<br />`yaw      (float)`: Yaw amount, [0.0 or 1.0] (0.0 == rotate left, 1.0 == rotate right) | Sends a control command to the drone, to set the current:<br /><br />- throttle<br />- pitch<br />- roll<br />- yaw<br /><br />Note: execution time is 0.01s, suitable for calling at 100Hz in a simple loop.<br /><br />Note: this will raise an exception if connection has been lost. | void |
| `firmware()` | - | The current firmware version of the drone.<br /><br />Only available after calling `setup()`. | A string of the form `"V6.1"`, or `None` |

### Example

An example script of controlling a drone is provided: `example.py`.

It has a single dependency, `getkey`, to use the keyboard as the control scheme.

You'll want to run `pip install getkey` to grab this.

Keyboard controls:
    ↑ / ↓: Throttle
    ← / →: Roll
    W / S: Pitch
    A / D: Yaw

### ESP32 and BNO055

This repo was created as a result of a project to control a toy drone using motion data from a BNO055 IMU.

All code relating to this can be found under [`remote/`](linkme).

Please check out the YouTube video that corresponds to this:

LINKME.

## Knowledge source

I built this by reverse engineering the mentioned "MINI RC" app; via static analysis and by hooking method calls to `AsyncSocket` at runtime.

`reversing/minirclogger` is the iOSOpenDev-based tweak used to do runtime analysis.

### Interesting things

### ???

## Licensing

All code is available under the GPLv3