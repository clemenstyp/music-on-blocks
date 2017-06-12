#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Quick start example that presents how to use libnfc"""

import logging
import nfc

class NFC_PN532:
    def __init__(self):
        self.logger = logging.getLogger('blocks')
        # pn532_uart:/dev/ttyAMA0
        self.logger.info("Setting up reader...")
        with nfc.ContactlessFrontend('tty:AMA0:pn532') as aReader:
            self.reader = aReader
        self.logger.info("Ready!")
        self.logger.info("")



    def read(self):
        with nfc.ContactlessFrontend('tty:AMA0:pn532') as aReader:
            tag = aReader.connect(rdwr={'on-connect': lambda tag: False})
            return str(tag.identifier).encode("hex")
        return None







