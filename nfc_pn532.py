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
        self.reader = nfc.ContactlessFrontend('tty:AMA0:pn532')
        self.logger.info("print reader:")
        self.logger.info(self.reader)
        self.logger.info("Ready!")
        self.logger.info("")



    def read(self):
        tag = self.reader.connect(rdwr={'on-connect': lambda tag: False})
        return str(tag.identifier).encode("hex")







