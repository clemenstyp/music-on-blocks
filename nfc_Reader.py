import logging

class NFC_READER:
    lastTagUid = ''

    def __init__(self):
       self.logger = logging.getLogger('blocks')

    def startReader(self, type):
        self.readerType = type

        if self.readerType == 'pn532':
            import nfc_pn532
            self.reader = nfc_pn532.NFC_PN532()

        elif self.readerType == 'MFRC522':
            import nfc_MFRC522

            self.logger.info("Setting up reader...")
            # Create an object of the class MFRC522
            self.reader = nfc_MFRC522.MFRC522()

            # Welcome message
            self.logger.info("Welcome to the MFRC522 reader")

            self.lastTagUid = 'stop'
            self.oldStatus = 0
            # This loop keeps checking for chips. If one is near it will get the UID and authenticate
        else:
            import nfc_DEMO
            self.logger.info("NFC Demo, no reader connected")
            self.reader = nfc_DEMO.NFC_DEMO()




    def readNFC(self):
        if self.readerType == 'pn532':
            return self.foundTag(self.reader.read())


        elif self.readerType == 'MFRC522':
            # Scan for cards
            # noinspection PyUnusedLocal,PyUnusedLocal
            (status, TagType) = self.MIFAREReader.MFRC522_Request(self.MIFAREReader.PICC_REQIDL)
            # If a card is found
            # Get the UID of the card
            (status, uid) = self.MIFAREReader.MFRC522_Anticoll()
            # If we have the UID, continue
            if status == self.MIFAREReader.MI_OK:
                tagUid = str(uid).encode("hex")  # get the UID of the touched tag

                return self.foundTag(tagUid)

            else:
                return None
        else:
            return self.foundTag(self.reader.read())

    def foundTag(self, newtag):
        if self.lastTagUid != newtag:
            self.lastTagUid = newtag
            self.logger.info("found Tag: " + newtag)
            return newtag
        else:
            return None