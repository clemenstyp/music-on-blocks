import RPi.GPIO as GPIO


from backend.ledPulse import LedPulse
from rotary_class import RotaryEncoder

from MusicLogging import MusicLogging

from backend import nfc_Reader


class RaspberryPi(object):
    # we are hopefully on an rPi, so init all gpio stuff

    GPIO.setmode(GPIO.BOARD)
    # GPIO.setwarnings(False)


    # GPIOS = Board Number
    GP_0 = 11
    GP_1 = 12
    GP_2 = 13
    GP_3 = 15
    GP_4 = 16
    GP_5 = 18
    GP_7 = 7
    SDA = 3
    SCL = 5
    CE_1 = 26
    CE_1_BCM = 7

    NOGPIO = -1

    LED1_BCM = CE_1_BCM

    BUTTON_PLAY = NOGPIO
    BUTTON_PAUSE = NOGPIO
    BUTTON_PLAYPAUSE = NOGPIO # GP_7 damit ist playpause abgeschaltet
    BUTTON_NEXT = GP_0
    BUTTON_PREV = GP_1
    BUTTON_UNJOIN = GP_2
    BUTTON_VOL_UP = NOGPIO
    BUTTON_VOL_DOWN = NOGPIO
    BUTTON_SHUFFLE = GP_5

    ROTARY_1 = GP_3  # GP_4 war das bei Clemens
    ROTARY_2 = GP_4  # GP_3 war das bei Clemens
    ROTARY_BUTTON = NOGPIO

    rightRotaryTurn = None
    leftRotaryTurn = None
    rotaryTouch = None

    def rotaryEventHandler(self, event):
        if event == RotaryEncoder.CLOCKWISE:
            MusicLogging.Instance().info("Rotary CLOCKWISE")
            self.rightRotaryTurn(event)
        elif event == RotaryEncoder.ANTICLOCKWISE:
            MusicLogging.Instance().info("Rotary ANTICLOCKWISE")
            self.leftRotaryTurn(event)
        elif event == RotaryEncoder.BUTTONDOWN:
            MusicLogging.Instance().info("Rotary Button down event")
            self.rotaryTouch(event)
        elif event == RotaryEncoder.BUTTONUP:
            MusicLogging.Instance().info("Rotary Button up event")

    def startOnePulseLed(self):
        try:
            self.ledPulse.startOnePulseLed()
        except:
            return

    def __init__(self, readerType, pause, play, togglePlayPause, toggleNext, togglePrev, toggleUnjoin, toggleVolUp,
                 toggleVolDown, toggleShuffle, rightRotaryTurn, leftRotaryTurn, rotaryTouch):
        self.rightRotaryTurn = rightRotaryTurn
        self.leftRotaryTurn = leftRotaryTurn
        self.rotaryTouch = rotaryTouch
        self.lastTagUid = None
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
            MusicLogging.Instance().info("Rotary found")
            encoder = RotaryEncoder(self.ROTARY_1, self.ROTARY_2, self.rotaryEventHandler)
            if self.ROTARY_BUTTON != self.NOGPIO:
                encoder.setupButton(self.ROTARY_BUTTON)

        # To show that everythin is startet: pulse the led for 5 seconds:
        if self.LED1_BCM != self.NOGPIO:
            self.ledPulse = LedPulse(self.LED1_BCM)
            self.ledPulse.startPulseLedForSeconds(10)
            # ledPulse.startPulseLed()

        self.reader = nfc_Reader.NFC_READER()
        self.reader.startReader(readerType)

    def readNFC(self, touchCallback, releaseCallback):
        tagUid = self.reader.readNFC()
        if self.lastTagUid != tagUid:
            self.lastTagUid = tagUid
            if tagUid is None:
                releaseCallback()
            else:
                touchCallback(tagUid)



    # Capture SIGINT for cleanup when the script is aborted
    # noinspection PyUnusedLocal
    def end_read(self, signal, frame):
        MusicLogging.Instance().info("Ctrl+C captured, ending read.")
        GPIO.cleanup()

        # Hook the SIGINT
        signal.signal(signal.SIGINT, self.end_read)
