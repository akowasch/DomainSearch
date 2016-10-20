#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
The Server component of the DomainSearch application.

Running Console, RatingRequestServer, QueuedDomainRequestServer,
        TaskNotofocationServer, ScannedDomainRequestServer.
"""

"""
################################################################################

Queue structur:

    queued_domain_request_queue = (request_id, domain)

        request_id = int
        domain = str

    scanned_domain_request_queue = (request_id, domain)

        request_id = int
        domain = str

################################################################################
"""

import os
import ast
import sys
import queue
import signal
import threading

from pymysql import DatabaseError

from additional import Config
from additional.Database import Database
from additional.Logging import Logging

from additional.Console import Console
from additional.RatingRequestServer import RatingRequestServer
from additional.RatingRequestServer import RatingRequestHandler
from additional.QueuedDomainRequestServer import QueuedDomainRequestServer
from additional.QueuedDomainRequestServer import QueuedDomainRequestHandler
from additional.TaskNotificationServer import TaskNotificationServer
from additional.TaskNotificationServer import TaskNotificationHandler
from additional.ScannedDomainRequestServer import ScannedDomainRequestServer
from additional.ScannedDomainRequestServer import ScannedDomainRequestHandler

################################################################################

def create_database_tables():
    """
    Method to create the required database tables.
    """

    db.create_table('''
        CREATE TABLE IF NOT EXISTS domains (
            id INT AUTO_INCREMENT NOT NULL,
            name VARCHAR(255) UNIQUE NOT NULL,
            state VARCHAR(10) DEFAULT 'permitted' NOT NULL,
            comment VARCHAR(255),
            updated DATETIME ON UPDATE CURRENT_TIMESTAMP
                             DEFAULT CURRENT_TIMESTAMP
                             NOT NULL,
            PRIMARY KEY (id)
        )''')

    db.create_table('''
        CREATE TABLE IF NOT EXISTS requests (
            id INT AUTO_INCREMENT NOT NULL,
            domain_id INT NOT NULL,
            state VARCHAR(10) DEFAULT 'queued' NOT NULL,
            comment VARCHAR(255),
            created DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
            PRIMARY KEY (id),
            FOREIGN KEY (domain_id) REFERENCES domains(id)
        )''')

    db.create_table('''
        CREATE TABLE IF NOT EXISTS errors (
            id INT AUTO_INCREMENT NOT NULL,
            request_id INT NOT NULL,
            module VARCHAR(50) NOT NULL,
            comment VARCHAR(255),
            created DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
            PRIMARY KEY (id),
            FOREIGN KEY (request_id) REFERENCES requests(id)
        )''')

    db.create_table('''
        CREATE TABLE IF NOT EXISTS versions (
            id INT AUTO_INCREMENT NOT NULL,
            module VARCHAR(50) NOT NULL,
            version INT NOT NULL,
            updated DATETIME ON UPDATE CURRENT_TIMESTAMP
                             DEFAULT CURRENT_TIMESTAMP
                             NOT NULL,
            PRIMARY KEY (id)
        )''')

################################################################################

def restore_backup(backup_queue, backup_path):
    """
    Method to restore a backup and add the tasks to the given queue.

    @param backup_queue: the queue to backup
    @param backup_path:  the location of the backup
    """

    with open(backup_path, 'r', encoding='utf-8') as backup_file:

        for line in backup_file:

            try:

                entry = ast.literal_eval(line)

                if is_backup_entry_valid(entry):

                    backup_queue.put(entry)

                    log.debug('Task recovered: {}'.format(line))

                else:
                    raise SyntaxError

            except SyntaxError:

                if Config.debug_mode:
                    raise

                log.error('Not a valid entry: {}'.format(line))

    os.remove(backup_path)

    log.info('Backup recovery finished: {}'.format(backup_path))

################################################################################

def is_backup_entry_valid(entry):
    """
    Method to check if a backup entry is valid.

    @param entry: (request_id, domain)

    @return: True if valid, False otherwise
    """

    # validates entry structure

    if not(
        isinstance(entry, tuple) and isinstance(entry[0], int) and \
        isinstance(entry[1], str)):

        return False

    # validates request in database
    return db.is_request_valid(entry[0], entry[1])

################################################################################

def create_backup(backup_queue, backup_path):
    """
    Method to create a backup from the given queue.

    @param backup_queue: the queue to backup
    @param backup_path:  the location of the backup
    """

    with open(backup_path, 'w', encoding='utf-8') as backup_file:

        while not backup_queue.empty():

            entry = backup_queue.get()
            backup_file.write(str(entry) + '\n')
            backup_queue.task_done()

    log.info('Generation of backup succeeded: {}'.format(backup_path))

################################################################################

def clean_shutdown(exit_code):
    """
    Method to cleanly shutdown the server.

    @param exit_code: the exit code to use
    """

    # informs about an upcoming shutdown
    running_event.clear()

    ############################################################################

    # shuts down the server components cleanly and waits until all open requests
    # are processed

    if 'rating_request_server' in globals():
        rating_request_server.shutdown()

    if 'queued_domain_request_server' in globals():
        queued_domain_request_server.shutdown()

    if 'scanned_domain_request_server' in globals():
        scanned_domain_request_server.shutdown()

    ############################################################################

    # creates a backup from queued-domain-request queue
    if 'queued_domain_request_queue' in globals() and \
        not queued_domain_request_queue.empty():

        create_backup(queued_domain_request_queue,
            Config.queued_domain_requests_backup_path)

    # creates a backup from scanned-domain-request queue
    if 'scanned_domain_request_queue' in globals() and \
        not scanned_domain_request_queue.empty():

        create_backup(scanned_domain_request_queue,
            Config.scanned_domain_requests_backup_path)

    ############################################################################

    # closes the databse connection
    if 'db' in globals():
        db.close_connection()

    ############################################################################

    # removes running file
    if os.path.isfile(Config.running_path):
        os.remove(Config.running_path)

    ############################################################################

    log.info('Server is shutting down')

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

if __name__ == "__main__":

    print('''\
  ____                        _         ____                      _
 |  _ \\  ___  _ __ ___   __ _(_)_ __   / ___|  ___  __ _ _ __ ___| |__
 | | | |/ _ \\| '_ ` _ \\ / _` | | '_ \\  \\___ \\ / _ \\/ _` | '__/ __| '_ \\
 | |_| | (_) | | | | | | (_| | | | | |  ___) |  __/ (_| | | | (__| | | |
 |____/ \\___/|_| |_| |_|\\__,_|_|_| |_| |____/ \\___|\\__,_|_|  \\___|_| |_|
  ____                             _   _   ___
 / ___|  ___ _ ____   _____ _ __  / | / | / _ \\
 \\___ \\ / _ \\ '__\\ \\ / / _ \\ '__| | | | || | | |
  ___) |  __/ |   \\ V /  __/ |    | |_| || |_| |
 |____/ \\___|_|    \\_/ \\___|_|    |_(_)_(_)___/
''')

    ############################################################################

    # running event will be cleared if shutdown command has been sent
    running_event = threading.Event()
    running_event.set()

    # forwards interrupt signal to application
    signal.signal(signal.SIGINT, signal_handler)

    ############################################################################

    # initialises the logger
    log = Logging('DomainSearchServer').get_logger()

    log.info('Server is starting up')

    ############################################################################

    # checks if another instance of this application is already running

    if os.path.isfile(Config.running_path):

        log.error('Server is already started')

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

        log.error('Connection to database failed')

        clean_shutdown(1)

    ############################################################################

    # creates the required database tables

    try:
        create_database_tables()

    except DatabaseError:

        if Config.debug_mode:
            raise

        log.error('Creation of database tables failed')

        clean_shutdown(1)

    ############################################################################

    # queue of queued-domain requests
    queued_domain_request_queue = queue.Queue()

    # queue of scanned-domain requests
    scanned_domain_request_queue = queue.Queue()

    ############################################################################

    # restores a possibly created backup

    if os.path.isfile(Config.queued_domain_requests_backup_path):

        restore_backup(queued_domain_request_queue,
            Config.queued_domain_requests_backup_path)

    if os.path.isfile(Config.scanned_domain_requests_backup_path):

        restore_backup(scanned_domain_request_queue,
            Config.scanned_domain_requests_backup_path)

    ############################################################################

    # dictionary of connected scanners

    scanners = {}
    scanners_lock = threading.Lock()

    # dictionary of connected reviewers

    reviewers = {}
    reviewers_lock = threading.Lock()

    ############################################################################

    # starts request handler for incomming rating requests

    rating_request_server = RatingRequestServer((
        Config.rating_request_server['host'],
        Config.rating_request_server['port']),
        RatingRequestHandler,
        (db, queued_domain_request_queue))

    rating_request_server_thread = \
        threading.Thread(target=rating_request_server.serve_forever)
    rating_request_server_thread.daemon = True
    rating_request_server_thread.start()

    ############################################################################

    # starts request handler for incomming queued-domain requests

    queued_domain_request_server = QueuedDomainRequestServer((
        Config.queued_domain_request_server['host'],
        Config.queued_domain_request_server['port']),
        QueuedDomainRequestHandler,
        (scanners, scanners_lock, running_event, queued_domain_request_queue))

    queued_domain_request_server_thread = \
        threading.Thread(target=queued_domain_request_server.serve_forever)
    queued_domain_request_server_thread.daemon = True
    queued_domain_request_server_thread.start()

    ############################################################################

    # starts request handler for incomming task notifications

    tast_notification_server = TaskNotificationServer((
        Config.task_notification_server['host'],
        Config.task_notification_server['port']),
        TaskNotificationHandler,
        (db, scanned_domain_request_queue))

    tast_notification_server_thread = \
        threading.Thread(target=tast_notification_server.serve_forever)
    tast_notification_server_thread.daemon = True
    tast_notification_server_thread.start()

    ############################################################################

    # starts request handler for incomming scanned-domain requests

    scanned_domain_request_server = ScannedDomainRequestServer((
        Config.scanned_domain_request_server['host'],
        Config.scanned_domain_request_server['port']),
        ScannedDomainRequestHandler,
        (reviewers, reviewers_lock, running_event, scanned_domain_request_queue))

    scanned_domain_request_server_thread = \
        threading.Thread(target=scanned_domain_request_server.serve_forever)
    scanned_domain_request_server_thread.daemon = True
    scanned_domain_request_server_thread.start()

    ############################################################################

    # starts the console communiation

    console = Console((
        db, scanners, scanners_lock, reviewers, reviewers_lock, running_event,
        queued_domain_request_queue, scanned_domain_request_queue))
    console.handle()

    ############################################################################

    # exists the application cleanly
    clean_shutdown(0)
