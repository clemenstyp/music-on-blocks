#!/usr/bin/env python
#
# Raspberry Pi Rotary Encoder Class
# $Id: rotary_class.py,v 1.2 2014/01/31 13:34:48 bob Exp $
#
# Author : Bob Rathbone
# Site   : http://www.bobrathbone.com
#
# This class uses standard rotary encoder with push switch
# 
#

import RPi.GPIO as GPIO
import logging
logger = logging.getLogger('blocks')

# noinspection PyPep8Naming,PyPep8Naming,PyPep8Naming,PyPep8Naming
class RotaryEncoder(object):
    CLOCKWISE = 1
    ANTICLOCKWISE = 2
    BUTTONDOWN = 3
    BUTTONUP = 4

    rotary_a = 0
    rotary_b = 0
    rotary_c = 0
    last_state = 0
    direction = 0

    # Initialise rotary encoder object

    def __init__(self, pinA, pinB, callback):
        self.pinA = pinA
        self.pinB = pinB
        self.callback = callback

        GPIO.setmode(GPIO.BOARD)

        # The following lines enable the internal pull-up resistors
        # on version 2 (latest) boards
        GPIO.setwarnings(False)
        GPIO.setup(self.pinA, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        GPIO.setup(self.pinB, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

        # Add event detection to the GPIO inputs
        GPIO.add_event_detect(self.pinA, GPIO.RISING, callback=self.switch_event)
        GPIO.add_event_detect(self.pinB, GPIO.RISING, callback=self.switch_event)

    def setupButton(self, button):
        GPIO.setup(button, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        GPIO.add_event_detect(button, GPIO.RISING, callback=self.button_event, bouncetime=200)

        # Call back routine called by switch events

    # noinspection PyUnusedLocal
    def switch_event(self, switch):
        if GPIO.input(self.pinA):
            self.rotary_a = 1
        else:
            self.rotary_a = 0

        if GPIO.input(self.pinB):
            self.rotary_b = 1
        else:
            self.rotary_b = 0

        self.rotary_c = self.rotary_a ^ self.rotary_b
        new_state = self.rotary_a * 4 + self.rotary_b * 2 + self.rotary_c * 1
        delta = (new_state - self.last_state) % 4
        # if delta > 0:
        # logger.info("delta: " + str(delta))
        self.last_state = new_state
        event = 0

        if delta == 1:
            if self.direction == self.CLOCKWISE:
                # print "Clockwise"
                event = self.direction
                self.direction = 0
            else:
                self.direction = self.CLOCKWISE
        elif delta == 3:
            if self.direction == self.ANTICLOCKWISE:
                # print "Anticlockwise"
                event = self.direction
                self.direction = 0
            else:
                self.direction = self.ANTICLOCKWISE
        if event > 0:
            self.callback(event)
        return


        # Push button up event

    # noinspection PyUnusedLocal
    def button_event(self, button):
        # if GPIO.input(button):
        #	event = self.BUTTONUP
        # else:
        #	event = self.BUTTONDOWN
        event = self.BUTTONDOWN
        self.callback(event)
        return

        # Get a switch state

    @staticmethod
    def getSwitchState(switch):
        return GPIO.input(switch)

        # End of RotaryEncoder class
