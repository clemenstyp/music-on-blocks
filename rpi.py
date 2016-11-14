import RPi.GPIO as GPIO
from rotary_class import RotaryEncoder
from ledPulse import LedPulse

class RaspberryPi(object):

    # we are hopefully on an rPi, so init all gpio stuff

    GPIO.setmode(GPIO.BOARD)
    # GPIO.setwarnings(False)

    # GP_6 = 22  #von Clemens NFC verwendet
    # GPIOS = Board Number
    GP_0 = 11
    GP_1 = 12
    GP_2 = 13  # nummer 2 auf johannes seiner Box
    GP_3 = 15
    GP_4 = 16
    GP_5 = 18  # nummer 1 auf Johannes seiner Box
    GP_7 = 7
    SDA = 3
    SCL = 5
    CE_1 = 26
    CE_1_BCM = 7

    NOGPIO = -1

    LED1_BCM = CE_1_BCM

    BUTTON_PLAY = NOGPIO
    BUTTON_PAUSE = NOGPIO
    BUTTON_PLAYPAUSE = GP_7
    BUTTON_NEXT = GP_0
    BUTTON_PREV = GP_1
    BUTTON_UNJOIN = GP_2
    BUTTON_VOL_UP = NOGPIO
    BUTTON_VOL_DOWN = NOGPIO
    BUTTON_SHUFFLE = GP_5

    ROTARY_1 = GP_4
    ROTARY_2 = GP_3
    ROTARY_BUTTON = NOGPIO

    rightRotaryTurn = None
    leftRotaryTurn = None
    rotaryTouch = None

    def rotaryEventHandler(self, event):
        if event == RotaryEncoder.CLOCKWISE:
            # print("Rotary CLOCKWISE")
            self.rightRotaryTurn(event)
        elif event == RotaryEncoder.ANTICLOCKWISE:
            # print("Rotary ANTICLOCKWISE")
            self.leftRotaryTurn(event)
        elif event == RotaryEncoder.BUTTONDOWN:
            # print("Rotary Button down event")
            self.rotaryTouch(event)
        elif event == RotaryEncoder.BUTTONUP:
            print("Rotary Button up event")

    def startOnePulseLed(self):
        self.ledPulse.startOnePulseLed()


    def __init__(self, readerType, pause, play, togglePlayPause, toggleNext, togglePrev, toggleUnjoin, toggleVolUp, toggleVolDown, toggleShuffle, rightRotaryTurn, leftRotaryTurn, rotaryTouch):
        self.rightRotaryTurn = rightRotaryTurn
        self.leftRotaryTurn = leftRotaryTurn
        self.rotaryTouch = rotaryTouch
        self.readerType = readerType

        # set all gpios
        if not self.BUTTON_PAUSE == self.NOGPIO:
            GPIO.setup(self.BUTTON_PAUSE, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
            GPIO.add_event_detect(self.BUTTON_PAUSE, GPIO.RISING, callback=pause, bouncetime=200)

        if not self.BUTTON_PLAY == self.NOGPIO:
            GPIO.setup(self.BUTTON_PLAY, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
            GPIO.add_event_detect(self.BUTTON_PLAY, GPIO.RISING, callback=play, bouncetime=200)

        if not self.BUTTON_PLAYPAUSE == self.NOGPIO:
            GPIO.setup(self.BUTTON_PLAYPAUSE, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
            GPIO.add_event_detect(self.BUTTON_PLAYPAUSE, GPIO.RISING, callback=togglePlayPause, bouncetime=800)

        if not self.BUTTON_NEXT == self.NOGPIO:
            GPIO.setup(self.BUTTON_NEXT, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
            GPIO.add_event_detect(self.BUTTON_NEXT, GPIO.RISING, callback=toggleNext, bouncetime=200)

        if not self.BUTTON_PREV == self.NOGPIO:
            GPIO.setup(self.BUTTON_PREV, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
            GPIO.add_event_detect(self.BUTTON_PREV, GPIO.RISING, callback=togglePrev, bouncetime=200)

        if not self.BUTTON_UNJOIN == self.NOGPIO:
            GPIO.setup(self.BUTTON_UNJOIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
            GPIO.add_event_detect(self.BUTTON_UNJOIN, GPIO.RISING, callback=toggleUnjoin, bouncetime=200)

        if not self.BUTTON_VOL_UP == self.NOGPIO:
            GPIO.setup(self.BUTTON_VOL_UP, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
            GPIO.add_event_detect(self.BUTTON_VOL_UP, GPIO.RISING, callback=toggleVolUp, bouncetime=200)

        if not self.BUTTON_VOL_DOWN == self.NOGPIO:
            GPIO.setup(self.BUTTON_VOL_DOWN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
            GPIO.add_event_detect(self.BUTTON_VOL_DOWN, GPIO.RISING, callback=toggleVolDown, bouncetime=200)

        if not self.BUTTON_SHUFFLE == self.NOGPIO:
            GPIO.setup(self.BUTTON_SHUFFLE, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
            GPIO.add_event_detect(self.BUTTON_SHUFFLE, GPIO.RISING, callback=toggleShuffle, bouncetime=200)

        if self.ROTARY_1 != self.NOGPIO & self.ROTARY_2 != self.NOGPIO:
            print("Rotary found")
            encoder = RotaryEncoder(self.ROTARY_1, self.ROTARY_2, self.rotaryEventHandler)
            if self.ROTARY_BUTTON != self.NOGPIO:
                encoder.setupButton(self.ROTARY_BUTTON)

        # To show that everythin is startet: pulse the led for 5 seconds:
        if self.LED1_BCM != self.NOGPIO:
            self.ledPulse = LedPulse(self.LED1_BCM)
            self.ledPulse.startPulseLedForSeconds(10)
            # ledPulse.startPulseLed()

        if self.readerType == 'pn532':
            import nfc
            # pn532_uart:/dev/ttyAMA0
            print("Setting up reader...")
            self.reader = nfc.ContactlessFrontend('tty:AMA0:pn53x')
            print(self.reader)
            print("Ready!")
            print("")

        elif self.readerType == 'MFRC522':
            import MFRC522

            print("Setting up reader...")
            # Create an object of the class MFRC522
            self.MIFAREReader = MFRC522.MFRC522()

            # Welcome message
            print("Welcome to the MFRC522 data read example")
            print("Press Ctrl-C to stop.")

            self.lastTagUid = 'stop'
            self.oldStatus = 0
            # This loop keeps checking for chips. If one is near it will get the UID and authenticate

    def readNFC(self, touchCallback, releaseCallback):
        if self.readerType == 'pn532':
            self.reader.connect(rdwr={'on-connect': touchCallback})
            print("Tag released")
            releaseCallback()
            print("")
            sleep(0.1);

        elif self.readerType == 'MFRC522':
            # Scan for cards
            (status, TagType) = self.MIFAREReader.MFRC522_Request(self.MIFAREReader.PICC_REQIDL)
            # If a card is found
            # Get the UID of the card
            (status, uid) = self.MIFAREReader.MFRC522_Anticoll()
            # If we have the UID, continue
            if status == self.MIFAREReader.MI_OK:
                tagUid = str(uid).encode("hex")  # get the UID of the touched tag
                if self.lastTagUid != tagUid:
                    touchCallback(uid)
                    self.lastTagUid = tagUid
            elif self.oldStatus == status:
                # else:
                # print ("No Card detected")
                if self.lastTagUid != 'stop':
                    releaseCallback()
                    self.lastTagUid = 'stop'
            self.oldStatus = status
            # sleep(0.1);


    # Capture SIGINT for cleanup when the script is aborted
    def end_read(self, signal, frame):
        global continue_reading
        print("Ctrl+C captured, ending read.")
        continue_reading = False
        GPIO.cleanup()

        # Hook the SIGINT
        signal.signal(signal.SIGINT, self.end_read)


