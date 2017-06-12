#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Quick start example that presents how to use libnfc"""

from MusicLogging import MusicLogging
import nfc

class NFC_PN532:
    def __init__(self):
        # pn532_uart:/dev/ttyAMA0
        MusicLogging.Instance().info("Setting up reader...")
        self.reader = nfc.ContactlessFrontend('tty:AMA0:pn532')
        MusicLogging.Instance().info("Ready!")
        MusicLogging.Instance().info("")



    def read(self):
        tag = self.reader.connect(rdwr={'on-connect': lambda tag: False})
        return str(tag.identifier).encode("hex")


    def stop(self):
        self.reader.close()
        MusicLogging.Instance().info("stopping reader")







