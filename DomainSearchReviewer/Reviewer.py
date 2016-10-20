#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
The Reviewer component of the DomainSearch application.
"""

"""
################################################################################

Messages:

    ScannedDomainRequestServer -> DomainSearchReviewer: review request

        "response": {
            "task": {
                "domain": "example.com",
                "request_id": 1
            }
        }

    ScannedDomainRequestServer -> DomainSearchReviewer: shutdown triggered

        "response": {
            "msg": "shutdown"
        }

    DomainSearchReviewer -> TaskNotificationServer: review finished (permitted)

        "notification": {
            "review": {
                "domain": "example.com",
                "request_id": 1,
                "access": "permitted"
            }
        }

    DomainSearchReviewer -> TaskNotificationServer: review finished (denied)

        "notification": {
            "review": {
                "domain": "example.com",
                "request_id": 1,
                "access": "denied",
                "comment": "reason for the denial"
            }
        }

################################################################################
"""

import os
import sys
import json
import signal
import socket
import threading

from additional import Config
from additional.Database import Database
from additional.Logging import Logging

from pymysql import DatabaseError

################################################################################

def start_reviewer():
    """
    Method to start the reviewer.
    """

    scanned_domain_request_server = (
        Config.scanned_domain_request_server['host'],
        Config.scanned_domain_request_server['port'])

    try:

        with socket.create_connection(scanned_domain_request_server) as sock:

            while running_event.is_set():

                try:

                    # requests the server for new task
                    sock.sendall(bytes(json.dumps({
                        'request': 'task'
                    }), 'UTF-8'))

                    ############################################################

                    # receives the response from the server
                    data = sock.recv(1024).decode('UTF-8').strip()

                    if not data:
                        raise ConnectionAbortedError

                    message = json.loads(data)

                    ############################################################

                    # validates message
                    if not 'response' in message:
                        raise ValueError

                    message = message['response']

                    ############################################################

                    if 'task' in message and 'domain' in message['task'] and \
                        'request_id' in message['task']:

                        task = message['task']
                        domain = task['domain']
                        domain = domain.lower().strip()
                        request_id = task['request_id']

                        # validates task in database
                        if not db.is_request_valid(request_id, domain):
                            raise ValueError

                        log.info('Task received - Request ID: {} - Domain: {}'
                            .format(request_id, domain))

                    elif 'msg' in message and message['msg'] == 'shutdown':

                        log.info('Server is shutting down')

                        running_event.clear()

                    else:
                        raise ValueError

                except ValueError:

                    log.error('Invalid message: {}'.format(data))

                    running_event.clear()

    except ConnectionRefusedError:

        log.error('Connection to server refused')

        clean_shutdown(1)

    except ConnectionAbortedError:

        log.error('Connection to server aborted')

        clean_shutdown(1)

################################################################################

def clean_shutdown(exit_code):
    """
    Method to cleanly shutdown the reviewer.

    @param exit_code: the exit code to use
    """

    # informs about an upcoming shutdown
    running_event.clear()

    ############################################################################

    # closes the databse connection
    if 'db' in globals():
        db.close_connection()

    ############################################################################

    # removes running file
    if os.path.isfile(Config.running_path):
        os.remove(Config.running_path)

    ############################################################################

    log.info('Reviewer is shutting down')

    sys.exit(exit_code)

################################################################################

def validate_configuration():
    """
    Method to validate the configuration file.
    """

    for var in [value for key, value in \
        Config.__dict__.items() if not key.startswith('__')]:

        if not isinstance(var, (int, float, str, tuple, list, set, dict)):

            log.error('Configurtion error! Please check configuration file')
            clean_shutdown(1)

################################################################################

def signal_handler(signal, frame):
    """
    Method to handle signals.

    @param signal: the signal number
    @param frame:  the current stack frame
    """

    clean_shutdown(0)

################################################################################
################################################################################

if __name__ == '__main__':

    print('''\
  ____                        _         ____                      _
 |  _ \\  ___  _ __ ___   __ _(_)_ __   / ___|  ___  __ _ _ __ ___| |__
 | | | |/ _ \\| '_ ` _ \\ / _` | | '_ \\  \\___ \\ / _ \\/ _` | '__/ __| '_ \\
 | |_| | (_) | | | | | | (_| | | | | |  ___) |  __/ (_| | | | (__| | | |
 |____/ \\___/|_| |_| |_|\\__,_|_|_| |_| |____/ \\___|\\__,_|_|  \\___|_| |_|
  ____            _                          _   _   ___
 |  _ \\ _____   _(_) _____      _____ _ __  / | / | / _ \\
 | |_) / _ \\ \\ / / |/ _ \\ \\ /\\ / / _ \\ '__| | | | || | | |
 |  _ <  __/\\ V /| |  __/\\ V  V /  __/ |    | |_| || |_| |
 |_| \\_\\___| \\_/ |_|\\___| \\_/\\_/ \\___|_|    |_(_)_(_)___/
''')

    ############################################################################

    # running event will be cleared if shutdown command has been sent
    running_event = threading.Event()
    running_event.set()

    # forwards interrupt signal to application
    signal.signal(signal.SIGINT, signal_handler)

    ############################################################################

    # initialises the logger
    log = Logging('DomainSearchReviewer').get_logger()

    log.info('Reviewer is starting up')

    ############################################################################

    # checks if another instance of this apllication is already running

    if os.path.isfile(Config.running_path):

        log.error('Reviewer is already started')

        sys.exit(1)

    ############################################################################

    # validates the configuration file
    validate_configuration()

    ############################################################################

    # writes the current pid to the running file

    with open(Config.running_path, 'w', encoding='utf-8') as running_file:

        pid = os.getpid()
        running_file.write(str(pid))

    ############################################################################

    # initialises the database

    try:
        db = Database()

    except DatabaseError:

        if Config.debug_mode:
            raise

        log.error('Connection to Database failed')

        clean_shutdown(1)

    ############################################################################

    # starts the reviewer
    start_reviewer()

    ############################################################################

    # exits the application cleanly
    clean_shutdown(0)
