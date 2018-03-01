#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Quick start example that presents how to use libnfc"""

from MusicLogging import MusicLogging
import nfc

class NFC_PN532:
    reader = None
    def __init__(self):
        # pn532_uart:/dev/ttyAMA0
        self.startReader()

    def startReader(self):
        MusicLogging.Instance().info("Setting up reader...")
        try:
            self.reader = nfc.ContactlessFrontend('tty:AMA0:pn532')
        except:
            MusicLogging.Instance().info("Cannot setup to the reader!")

    def read(self):
        returnValue = ""
        try:
            tag = self.reader.connect(rdwr={'on-connect': lambda tag: False})
            returnValue = str(tag.identifier).encode("hex")
        except:
            MusicLogging.Instance().info("Cannot connect to the reader!")
            self.startReader()

        return returnValue


    def stop(self):
        if self.reader is not None:
            self.reader.close()
            MusicLogging.Instance().info("stopping reader")
        else:
            MusicLogging.Instance().info("cannot stop, because there was no reader")







