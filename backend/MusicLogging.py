import logging
import logging.handlers
import os

import errno

from Singleton import Singleton

import sys
sys.path.insert(0,'..')

import settings as settings

@Singleton
class MusicLogging:
    # make logger configuration
    log_filename = 'log/blocks.log'
    if not os.path.exists(os.path.dirname(log_filename)):
        try:
            os.makedirs(os.path.dirname(log_filename))
        except OSError as exc:  # Guard against race condition
            if exc.errno != errno.EEXIST:
                raise



    log_format = '%(asctime)s.%(msecs)03d [%(name)s.%(funcName)s] %(levelname)s: %(message)s'
    date_format = '%m/%d/%Y %H:%M:%S'
    logging.basicConfig(level=logging.INFO)

    def __init__(self):
        self.logger = logging.getLogger()
        # Add the log message handler to the logger
        fileHandler = logging.handlers.RotatingFileHandler(filename=self.log_filename, maxBytes=(20 * 1024 * 1024),
                                                           backupCount=50)
        fileHandler.setLevel(logging.INFO)
        fileHandler.setFormatter(logging.Formatter(fmt=self.log_format, datefmt=self.date_format))
        self.logger.addHandler(fileHandler)

        if settings.LOG_TO_CONSOLE:
            # create console handler and set level to debug
            consoleHandler = logging.StreamHandler()
            consoleHandler.setLevel(logging.DEBUG)
            # create formatter and add formatter to ch
            consoleHandler.setFormatter(logging.Formatter(fmt=self.log_format, datefmt=self.date_format))
            self.logger.addHandler(consoleHandler)


    def debug(self, logMessage):
        self.logger.debug(logMessage)

    def info(self, logMessage):
        self.logger.info(logMessage)

    def error(self, logMessage):
        self.logger.error(logMessage)

    def filename(self):
        return 'log/blocks.log'