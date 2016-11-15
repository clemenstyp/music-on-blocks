#!/usr/bin/env python
from __future__ import print_function

import threading
from time import sleep

import pigpio

IS_OFF = 0
SHOULD_START = 1
IS_ON = 3
SHOULD_STOP = 4
RUN_ONE_CYCLE = 5
IS_STOPPING = 6


class LedPulse(object):
    # The run() method will be started and it will run in the background until the application exits.

    # Initialise rotary encoder object
    def __init__(self, ledPin):
        self.ledPin = ledPin
        self.state = IS_OFF
        # We pulse at 100 Hertz (cycles per second)

        self.hertz = 800
        self.speed = 0.005

        # GPIO.setup(ledPin, GPIO.OUT)
        # Initialize the software-PWM on our pin at the given rate of 100 Hertz
        # self.pulse = GPIO.PWM(ledPin, self.hertz)

        self.pi = pigpio.pi()  # connect to local Pi
        self.pi.set_PWM_range(self.ledPin, 100)
        self.pi.set_PWM_frequency(self.ledPin, self.hertz)
        print("new frequency: " + str(self.pi.get_PWM_frequency(self.ledPin)))

        thread = threading.Thread(target=self.run, args=())
        thread.daemon = True  # Daemonize thread
        thread.start()  # Start the execution

    def run(self):
        """ Method that runs forever """
        minValue = 5
        # Feel free to modify this interval to play with the pulsing speed

        level = minValue
        mod = 1

        while True:
            if self.state == SHOULD_START:
                # print("set pulse to: " + str(level))
                self.pi.set_PWM_dutycycle(self.ledPin, level)
                self.state = IS_ON

            if self.state == RUN_ONE_CYCLE:
                # print("set pulse to: " + str(level))
                self.pi.set_PWM_dutycycle(self.ledPin, level)
                self.state = IS_STOPPING

            if self.state == IS_ON or self.state == IS_STOPPING:
                level += mod

                # If max brightness or min brightness, revert direction
                if level >= 100:
                    level = 100
                    mod *= -1

                if level <= minValue:
                    if self.state != IS_STOPPING:
                        mod *= -1

                if level <= 0:
                    level = 0
                    self.state = SHOULD_STOP

                # The duty cycle determines the percentage of time the
                # pin is switched on (we will perceive this as the LEDs
                # brightness)
                # print("set pulse to: " + str(level))
                self.pi.set_PWM_dutycycle(self.ledPin, level)

            if self.state == SHOULD_STOP:
                # self.pulse.stop()
                level = minValue
                mod = 1
                self.pi.set_PWM_dutycycle(self.ledPin, 0)

            # if state == is_off: do nothing
            sleep(self.speed)

    def timer(self, seconds):
        """ Method that runs forever """
        sleep(self.speed)
        sleep(seconds)
        self.state = SHOULD_STOP

    def stopLed(self):
        self.state = SHOULD_STOP

    def startPulseLed(self):
        print("start pulse")
        self.state = SHOULD_START

    def startPulseLedForSeconds(self, seconds):
        self.state = SHOULD_START
        thread = threading.Thread(target=self.timer, args=(seconds,))
        thread.daemon = True  # Daemonize thread
        thread.start()

    def startOnePulseLed(self):
        print("start one pulse")
        self.state = RUN_ONE_CYCLE
