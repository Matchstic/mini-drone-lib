### ESP32 and BNO055 motion control

This package contains all code necessary to control a MINIRC-based drone from inside **MicroPython**.

It is assumed your hardware is ESP32 based, and you have connected a BNO055 IMU.

For my own setup, I used the following components:

- [TinyPICO V2](https://www.tinypico.com/)
- [BNO055 board](https://www.adafruit.com/product/4646)

### Setup procedure

## Repo

This repo makes use of submodules. Make sure they have been downloaded by running:

```
$ git submodule init && git submodule update
```

## Configuration

You will need to specify the SSID of your drone in code, before deploying it.

Simply update the value for `WIRELESS_SSID` in `main.py` for this. The wireless network should be
unencrypted, and not require a passphrase.

## Installation

After you've connected all your components, plug it into your dev machaine, and run the following from this folder:

```
$ .bin/deploy.sh /dev/<tty of your board>
```

This will deploy everything to your board, which should then start running everything.

### Usage

## Calibration

Before you can fly using this setup, you first need to calibrate the IMU.

To do this, make sure your board is connected to your dev machine, then run from this folder:

```
$ .bin/pyboard.py -d /dev/<tty of your board> calibration.py
```

In the terminal, you should see the current calibration status logged to the screen.

Follow the calibration instructions found [here](https://www.youtube.com/watch?v=Bw0WuAyGsnY) until all values are `3`.

At this point, the calibration state will be written to your board, and the script will exit.

## Flight

Control of the drone is as follows:

0. Hold the IMU in a level position
1. Wait for your drone to show it is in a connected state (e.g., it stops flashing LEDs)
2. Rotate the IMU either left or right, then quickly return it to a level position -> this starts the takeoff procedure

At this point, you can now rotate the IMU in any direction to control your drone.

Some important considerations:

- moving upwards (i.e., increasing throttle) is done with a short flick upwards of the IMU
- same applies in reverse for downwards
- to force a landing, flip the IMU upside. This will set throttle to 0.0.

If wireless connection is lost, due to e.g. turning off the drone, the codebase will switch back to attempting to connect to the drone again.

### Licensing

All code is available under the GPLv3