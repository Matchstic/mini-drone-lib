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

import time

class Throttle():
    """
    Throttle is driven by linear acceleration in the z axis.

    The idea is that the user's movement is tracked to find the peak
    acceleration before movement slows again. This is then translated
    into a decay function, which reduces the throttle over time.

    The greater the acceleration, the longer this decay occurs, resulting
    in a longer period of acceleration on the remote hardware. As a result,
    this produces a larger vertical translation.
    """

    BASE          = 0
    PEAK          = 1
    WAIT          = 2

    state         = BASE
    direction     = 0
    value         = 0.5
    previous      = []
    peakValue     = 0.0
    waitStart     = 0
    waitDuration  = 0
    peakStart     = 0
    peakToggled   = False

    PEAK_TIMEOUT  = 500

    def sign(self, value):
        return (value > 0) - (value < 0)

    def tick(self, vel, midpoint):
        # State handling
        if self.state == Throttle.BASE:
            # Check that previous values are also matching these conditions
            if vel > midpoint:
                self.state = Throttle.PEAK
                self.direction = 1
                self.peakStart = time.ticks_ms()
            elif vel < 0 - midpoint:
                self.state = Throttle.PEAK
                self.direction = -1
                self.peakStart = time.ticks_ms()

        elif self.state == Throttle.PEAK:
            directionCheck = False

            if self.direction == 1:
                directionCheck = vel < self.peakValue
                self.peakValue = vel if vel >= self.peakValue else self.peakValue
            elif self.direction == -1:
                directionCheck = vel > self.peakValue
                self.peakValue = vel if vel <= self.peakValue else self.peakValue

            # Only change current throttle when heading towards peak, and ignore
            # lower values when velocity is dropped due to reduced motion.
            if not directionCheck:
                self.value = ((self.peakValue * 1.82) + 100) / 200.0

            # Check previous and current, then see if we're in the endgame
            allInBounds = True
            for prev in self.previous:
                if not (prev > 0 - midpoint and prev < midpoint):
                    allInBounds = False

            diff = time.ticks_diff(time.ticks_ms(), self.peakStart)

            if diff > Throttle.PEAK_TIMEOUT:
                self.state = Throttle.BASE
                self.value = 0.5
                self.peakValue = 0.0
                self.peakToggled = False
            elif self.sign(vel) != self.sign(self.peakValue):
                # Switched over now
                self.peakToggled = True
            elif (self.peakToggled and
                  self.sign(vel) == self.sign(self.peakValue) and
                  vel > 0 - (midpoint / 2) and
                  vel < (midpoint / 2) and
                  allInBounds):

                self.waitStart = time.ticks_ms()
                self.waitDuration = abs(((self.value - 0.5) * 2) * 120) + 60
                self.state = Throttle.WAIT

        elif self.state == Throttle.WAIT:
            diff = time.ticks_diff(time.ticks_ms(), self.waitStart)

            if diff > self.waitDuration:
                self.waitStart = 0
                self.state = Throttle.BASE
                self.value = 0.5
                self.peakValue = 0.0
                self.peakToggled = False

        if len(self.previous) >= 3:
            self.previous.pop()

        self.previous.append(vel)

    def compute(self):
        return self.value