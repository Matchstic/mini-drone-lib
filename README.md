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

### Known Supported Drones

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
| `connect()` | `ip (string)`: IP address of the drone. This is defaults to `192.168.1.1`, but may differ by manufacturer. | Sets up the sockets used for communication to the drone.<br /><br />It is expected that you have already connected to the drone's wireless network ahead of calling this method. | `True` if connection is established, otherwise `False` |
| `setup()` | - | Sends appropriate commands to arm the drone. After arming, videoType and firmware is available.<br /><br />Note: this will raise an exception if connection has been lost. | void |
| `idle()` | - | Sends an "idle" control command. This is needed for the drone to recognise that you have connected, before calling `takeoff()` or `arm()`.<br /><br />Execution time is 0.01s, suitable for calling at 100Hz.<br /><br />Note: this will raise an exception if connection has been lost. | void |
| `takeoff()` | - | Sends a takeoff command to the drone.<br /><br />You should call this in a loop for as long as you want the takeoff to run. A reasonable loop duration is 500ms.<br /><br />This is not strictly required to start a flight. You can instead call `arm()` then `control()` in sequence, to more finely control the takeoff.<br /><br />Note: this will raise an exception if connection has been lost. | void |
| `arm()` | - | Arms the drone for a manual takeoff, instead of calling takeoff().<br /><br />Once motors spin up, you need to call control() with a high enough throttle to takeoff, within a short timeframe. Otherwise, the drone will automatically disarm itself.<br /><br />Note: this will raise an exception if connection has been lost. | void |
| `control()` | `throttle (float)`: Throttle %, [0.0 to 1.0] (< 0.5 to descend, > 0.5 to ascend)<br />`pitch    (float)`: Pitch angle, [0.0 to 1.0] (< 0.5 backward, > 0.5 forward)<br />`roll     (float)`: Roll angle, [0.0 to 1.0] (< 0.5 left, > 0.5 right)<br />`yaw      (float)`: Yaw amount, [0.0 or 1.0] (0.0 == rotate left, 1.0 == rotate right) | Sends a control command to the drone, to set the current:<br /><br />- throttle<br />- pitch<br />- roll<br />- yaw<br /><br />Note: execution time is 0.01s, suitable for calling at 100Hz in a simple loop.<br /><br />Note: this will raise an exception if connection has been lost. | void |
| `firmware()` | - | The current firmware version of the drone.<br /><br />Only available after calling `setup()`. | A string of the form `"V6.1"`, or `None` |

### Example

An example script of controlling a drone is provided: `example.py`.

It has a single dependency, `getkey`, to use the keyboard as the control scheme.

You'll want to run `pip install getkey` to grab this.

Keyboard controls:
- ↑ / ↓: Throttle
- ← / →: Roll
- W / S: Pitch
- A / D: Yaw

### ESP32 and BNO055

This repo was created as a result of a project to control a toy drone using motion data from a BNO055 IMU.

All code relating to this can be found under [`remote/`](remote).

Please check out the YouTube video that corresponds to this:

[![YouTube: I hacked a drone to fly using motion control](https://img.youtube.com/vi/ygtreF12Hks/maxresdefault.jpg)](https://www.youtube.com/watch?v=ygtreF12Hks)

## Knowledge source

I built this by reverse engineering the mentioned "MINI RC" app; via static analysis and by hooking method calls to `AsyncSocket` at runtime.

`reversing/minirclogger` is the iOSOpenDev-based tweak used to do runtime analysis.

### Connectivity

The remote drone advertises an unsecured WiFi network at 2.4GHz.

In the case of the drone I used for research, the SSID was of the form `"MINI RC_<3 bytes>"`.

### Sockets

Two sockets are exposed:

- UDP on port 8080
- TCP on port 8888

The UDP socket accepts control signals (e.g., throttle), as well as handling the setup handshake and any query commands.

Conversely, the TCP socket appears to be solely for video. In this library, this socket is connected but ignored.

All commands are sent as big endian.

### Setup Handshake

To initiate setup, multiple messages are exchanged with the drone on the UDP socket. Chronologically, these are:

1. Specify the ID of the controller: `0fc0a801 01`
2. Set the current date: `64617465 202d7320 22323032 312d3131 2d303620 31383a32 323a3335 22`<br/>This is literally just `date -s "2021-11-06 18:22:35"` encoded into bytes.
3. Unknown command: `26e50700 000b0000 00060000 00000000 00120000 00160000 00230000 00`

### Data Retrieval

We can also retrieve data from the drone after the setup handshake. This is done by sending a single magic byte, and then doing a blocking read on the UDP socket.

Known commands are as follows:

| Name | Command Byte | Result |
| ---- | ------------ | ------ |
| Firmware version  | `28` | `"V6.1"` |
| Video type  | `42` | unknown |

### Control Format

The control scheme is fairly straightfowards.

Here's an example packet sent to the drone by the `idle()` method:

```
ff087f40 40401010 100187
```

This can be broken down as follows:

| Header | Throttle | Yaw | Pitch | Roll | Throttle trim | Pitch trim | Roll trim | Flags | Checksum |
| ------ | -------- | --- | ----- | ---- | ------------- | ---------- | --------- | ----- | -------- |
| `ff08` | `7f` | `40` | `40` | `40` | `10` | `10` | `10` | `01` | `87` |

Each value has slightly different ranges:

| Name | Range | Value at idle |
| ---- | ----- | ------------- |
| Throttle | [`00`, `ff`] | `7f` |
| Yaw | [`00` or `7f`] | `40` |
| Pitch | [`00`, `7f`] | `40` |
| Roll | [`00`, `7f`] | `40` |
| Throttle trim | [`00`, `20`] | `10` |
| Pitch trim | [`00`, `20`] | `10` |
| Roll trim | [`00`, `20`] | `10` |

This control message should be sent at around 100Hz for responsive control.

#### Throttle

A value above `0x7f` represents raising the current throttle to ascend. The reverse then applies for descending.

If the drone is currently in an armed state (see below), sending a throttle value of `0x00` will then disarm the drone.

Furthermore, the drone should automatically disarm itself when landing when setting throttle low.

#### Yaw

Yaw is a strange one. It must be set to either `00` or `7f` to rotate anti-clockwise and clockwise respectively.

#### Pitch

A value less than `0x40` represents pitching forward, whereas a greater value is to pitch backwards.

#### Roll

A value less than `0x40` represents roll to the left, whereas a greater value is to roll rightwards.

#### Trim

Most control values have a corresponding trim control. I didn't do much research around this.

#### Flags

There are number of values that can be passed to the Flags fields:

| Name         | Value    |
| ------------ | -------- |
| Slow speed   | `0x[?]0` |
| Medium speed | `0x[?]1` |
| Fast speed   | `0x[?]2` |
| Reversed controls | `0x[?]4` |
| Return (not sure what this is) | `0x[?]8` |
| Headless mode | `0x1[?]` |
| Stop motors | `0x2[?]` |
| Start flight | `0x4[?]` |
| Land | `08[?]` |

Please note that this library doesn't correctly compute the checksum when a flag other than `0x01` is passed. This results in
the drone ignoring the sent command.

#### Checksum

At the end of every control message is a checksum byte. This is calculated in relation to all the preceeding bytes, excluding the header.

I was unable to derive the exact method to calculate this, but was able to approximate it using the following:

```
def __endByteCalc(self, throttle, yaw, pitch, roll, throttleTrim, rollTrim, pitchTrim, command):
        return 0x87 + (0x7f - throttle) + (0x40 - yaw) + (0x40 - pitch) + (0x40 - roll) + (0x10 - throttleTrim) + (0x10 - rollTrim) + (0x10 - pitchTrim) + (0x01 - command)
```

### Idling

At idle (post-handshake, but before flight), the drone expects the control format to be sent at 100Hz with idle values:

```
ff087f40 40401010 100187
```

This appears to be used internally as a "is a controller connected?" check by the drone, and is needed to
indicate a "Connected" status by e.g. status LEDs on the drone.

### Arming

There are two ways to arm the drone (and subsequently do a takeoff).

The easiest way is to set the current throttle to be > 80%, and then returning to the idle state. This starts the motors spinning for about 10 seconds.

To then takeoff from this state, raise the throttle again until the drone begins to fly.

Alternatively, it is possible to send a takeoff command:

```
ff087f40 40409010 1041c7
```

The drone firmware expects this command to be sent continuously for the duration of the takeoff procedure. For example, by sending it at 100Hz in a loop running for 500ms.

### Heartbeat

On the TCP socket, it appears a heartbeat is sent every 100ms to keep video data alive.

This is of the form:

```
00010203 04050607 08092525
```

## Licensing

All code is available under the GPLv3
