# -*- coding: utf-8 -*-

"""
The watchdog is responsible for the rerun queue.
"""

"""
################################################################################

Queue structur:

    rerun_queue = (request_id, domain, counter, rerun_modules, date_time)

        request_id = int
        domain = str
        counter = int
        rerun_modules = [module, ...]

            module = str

        date_time = datetime

################################################################################
"""

import os
import ast
import time
import threading
from datetime import datetime

from additional import Config
from additional.Logging import Logging

class Watchdog(threading.Thread):
    """
    This class restores a backup of the rerun queue if one found, checks the
    rerun queue continuously for new tasks, starts the scheduler if a new task
    is available and backups the rerun queue in case of a shutdown.
    """

    def __init__(self, scheduler, db, running_event, rerun_queue):

        threading.Thread.__init__(self)
        self._db = db
        self._scheduler = scheduler
        self._running_event = running_event
        self._rerun_queue = rerun_queue

        self._log = Logging(self.__class__.__name__).get_logger()

        ########################################################################

        # restores a possibly created backup

        if os.path.isfile(Config.rerun_queue_backup_path):
            self._restore_backup(rerun_queue, Config.rerun_queue_backup_path)

    ############################################################################

    def run(self):
        """
        Method to check the rerun queue continuously for new tasks and start
        the scheduler if a new task is available.
        """

        while self._running_event.is_set():

            time.sleep(Config.rerun_queue_check_delay)

            ####################################################################

            if self._rerun_queue.empty():
                continue

            self._log.info('Items in queue: {}'
                .format(self._rerun_queue.qsize()))

            ####################################################################

            task = self._rerun_queue.get()

            request_id, domain, counter, rerun_modules, date_time = task

            self._rerun_queue.task_done()

            ####################################################################

            # gets the right item from rerun thresholds

            items_count = len(Config.rerun_thresholds)

            if counter < items_count:
                rerun_thresholds = Config.rerun_thresholds[counter - 1] * 60

            else:
                rerun_thresholds = Config.rerun_thresholds[items_count - 1] * 60

            ####################################################################

            # checks if task should rerun

            timedelta = datetime.now() - date_time

            if timedelta.seconds < rerun_thresholds:
                self._rerun_queue.put(task)

            else:

                self._scheduler.start_modules(request_id, domain, counter,
                    rerun_modules)

        ########################################################################

        # creates a backup from the rerun queue

        if not self._rerun_queue.empty():

            self._create_backup(self._rerun_queue,
                Config.rerun_queue_backup_path)

    ###########################################################################

    def _restore_backup(self, backup_queue, backup_path):
        """
        Method to restore a backup and add the tasks to the given queue.

        @param backup_queue: the queue to backup
        @param backup_path:  the location of the backup
        """

        with open(backup_path, 'r', encoding='utf-8') as backup_file:

            for line in backup_file:

                try:

                    entry = ast.literal_eval(line)

                    if self._is_backup_entry_valid:

                        backup_queue.put(entry)

                        self._log.debug('Task recovered: {}'.format(line))

                    else:
                        raise SyntaxError

                except SyntaxError:

                    if Config.debug_mode:
                        raise

                    self._log.error('Not a valid entry: {}'.format(line))

        os.remove(backup_path)

        self._log.info('Backup recovery finished: {}'.format(backup_path))

    ###########################################################################

    def _is_backup_entry_valid(self, entry):
        """
        Method to check if a backup entry is valid.

        @param entry: (request_id, domain, counter, rerun_modules)

        @return: True if valid, False otherwise
        """

        # validates entry structure

        if not(
            isinstance(entry, tuple) and isinstance(entry[0], int) and \
            isinstance(entry[1], str) and isinstance(entry[2], int) and \
            isinstance(entry[3], set) and isinstance(entry[4], datetime)):

            return False

        for module in entry[3]:

            if not isinstance(module, str):
                return False

        # validates module instantiation in scheduler

        for module in entry[3]:

            if not self._scheduler.is_module_instantiated(module):
                return False

        # validates request in database
        if not self._db.is_request_valid(entry[0], entry[1]):
            return False

        # validates temporal relevance of the request

        timedelta = datetime.now() - entry[4]

        return timedelta.days < Config.request_expiration_time

    ############################################################################

    def _create_backup(self, backup_queue, backup_path):
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

        self._log.info('Generation of backup succeeded: {}'.format(backup_path))
