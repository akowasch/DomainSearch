# -*- coding: utf-8 -*-

"""
The Logging component of the Viewer.
"""

import logging.handlers

################################################################################

class Logging:
    """
    This class handles the console and file logging.
    """

    def __init__(self, filename):

        self._logger = logging.getLogger(filename)
        self._logger.setLevel(logging.DEBUG)

        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)

        file_handler = logging.handlers.RotatingFileHandler(
            'logs/' + filename + '.log',
            encoding = 'utf8',
            maxBytes = 1048576, # 1 MB
            backupCount = 2)

        file_handler.setLevel(logging.DEBUG)

        console_formatter = logging.Formatter(
            "%(asctime)s - %(levelname)-7s - %(name)-21s - %(message)s",
            "%Y-%m-%d %H:%M:%S")

        file_formatter = logging.Formatter(
            "%(asctime)s - %(levelname)-7s - %(message)s",
            "%Y-%m-%d %H:%M:%S")

        console_handler.setFormatter(console_formatter)
        file_handler.setFormatter(file_formatter)

        self._logger.addHandler(console_handler)
        self._logger.addHandler(file_handler)

    ############################################################################

    def get_logger(self):
        """
        Method to return the logger.

        @return: the logger
        """

        return self._logger
