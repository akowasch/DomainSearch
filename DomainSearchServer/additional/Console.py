# -*- coding: utf-8 -*-

"""
The Console handles the commandline communication of the server.
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

import socket
from datetime import datetime

from additional import Config
from additional.Logging import Logging

################################################################################

class Console():
    """
    This class handles the commandline input.
    """

    def __init__(self, arguments):

        self._db = arguments[0]
        self._scanners = arguments[1]
        self._scanners_lock = arguments[2]
        self._reviewers = arguments[3]
        self._reviewers_lock = arguments[4]
        self._running_event = arguments[5]
        self._queued_domain_request_queue = arguments[6]
        self._scanned_domain_request_queue = arguments[7]

        self._log = Logging(self.__class__.__name__).get_logger()

    ############################################################################

    def handle(self):
        """
        Method to handle the commandline input.
        """

        self._print_help()

        while self._running_event.is_set():

            try:
                user_input = input('Domain Search: ')
                user_input = user_input.strip()

            except EOFError:
                break

            ####################################################################

            if user_input.startswith('add domain') or \
                user_input.startswith('add file'):

                domains = set()
                counter = 0

                ################################################################

                # checks if user input is a domain or a file

                is_file_import = user_input.startswith('add file')

                ################################################################

                if is_file_import:

                    file_name = user_input.split(' ')[2]
                    file_path = 'resources/' + file_name

                    try:

                        with open(file_path, 'r', encoding='utf-8') as file:

                            for entry in file:

                                domain = entry.lower().strip()

                                try:

                                    socket.getaddrinfo(domain, None,
                                        family=socket.AF_INET,
                                        proto=socket.IPPROTO_TCP)

                                    domains.add(domain)

                                except socket.gaierror:
                                    pass

                    except IOError:

                        self._print('Error', 'File not found: {}'
                            .format(file_path))

                        continue

                ################################################################

                else:

                    domain = user_input.split(' ')[2]
                    domain = domain.lower().strip()

                    try:

                        socket.getaddrinfo(domain, None, family=socket.AF_INET,
                            proto=socket.IPPROTO_TCP)

                        domains.add(domain)

                    except socket.gaierror:

                        self._print('Error', 'Invalid domain. ' +
                            'Domain will not be added to the queue')

                        continue

                ################################################################

                for domain in domains:

                    # checks if the domain already exists in the database
                    result = self._db.select_data('''
                        SELECT id, updated
                        FROM domains
                        WHERE name = %s''', (domain,))

                    ############################################################

                    if result: # domain found

                        domain_id = result[0][0]
                        domain_updated = result[0][1]

                        ########################################################

                        # checks if the domain entry is expired

                        timedelta = datetime.now() - domain_updated

                        if timedelta.days < Config.domain_expiration_time:

                            if not is_file_import:

                                self._print('Info',
                                    'Valid domain entry found. ' +
                                    'Task will not be added to the queue')

                            continue

                        ########################################################

                        # gets the most recently request of the domain from the
                        # database
                        result = self._db.select_data('''
                            SELECT created
                            FROM requests
                            WHERE domain_id = %s
                            ORDER BY id DESC
                            LIMIT 1''', (domain_id,))

                        ########################################################

                        if result: # request found

                            request_created = result[0][0]

                            ####################################################

                            # checks if the request entry is expired

                            timedelta = datetime.now() - request_created

                            if timedelta.days < Config.request_expiration_time:

                                if not is_file_import:

                                    self._print('Info',
                                        'Valid request entry found. ' +
                                        'Task will not be added to the queue')

                                continue

                    ############################################################

                    else: # domain not found

                        domain_id = self._db.insert_data('''
                            INSERT INTO domains (name)
                            VALUES(%s)''', (domain,))

                    ############################################################

                    request_id = self._db.insert_data('''
                        INSERT INTO requests (domain_id)
                        VALUES(%s)''', (domain_id,))

                    self._queued_domain_request_queue.put((request_id, domain))

                    counter += 1

                    if not is_file_import:

                        self._print('Info',
                            'Task successfully added to the queue')

                if is_file_import:

                    self._print('Info',
                        '{} domain(s) successfully added to the queue'
                        .format(counter))

            ####################################################################

            elif user_input == 'show queued domains':

                queue_size = self._queued_domain_request_queue.qsize()

                self._print('Info', '{} domain(s) in the queue'
                    .format(queue_size))

            ####################################################################

            elif user_input == 'show scanned domains':

                queue_size = self._scanned_domain_request_queue.qsize()

                self._print('Info', '{} domain(s) in the queue'
                    .format(queue_size))

            ####################################################################

            elif user_input == 'show help':

                self._print_help()

            ####################################################################

            elif user_input == 'show scanners':
                self._print_connected(self._scanners, self._scanners_lock)

            ####################################################################

            elif user_input == 'show reviewers':
                self._print_connected(self._reviewers, self._reviewers_lock)

            ####################################################################

            elif user_input == 'shutdown':

                self._running_event.clear()

                self._print('Info', 'Server is shutting down')

                # waits until all scanners have closed the connection

                while 1:

                    with self._scanners_lock:

                        if not self._scanners:
                            break

                # waits until all reviewers have closed the connection

                while 1:

                    with self._reviewers_lock:

                        if not self._reviewers:
                            break

            ####################################################################

            else:

                self._print('Error', 'Command not found. ' + \
                    'Type "show help" to list available commands')

    ############################################################################

    def _print(self, msg_type, msg):
        """
        Method for decorated printing.

        @param msg_type: the type of the message (e.g. Info, Error)
        @param msg:      the message itself
        """

        print('\n', msg_type + ':', msg + '\n')

    ############################################################################

    def _print_help(self):

        print("""
 You can enter the following commands.

 add domain $domain   - adds a single domain to the queue
 add file $file       - adds all domains in the given file to the queue
 show queued domains  - prints the number of queued domains waiting to process
 show scanned domains - prints the number of scanned domains waiting to process
 show scanners        - prints all current connected scanners
 show reviewers       - prints all current connected reviewers
 show help            - prints this help text
 shutdown             - exits the application\n""")

    ############################################################################

    def _print_connected(self, connections, connections_lock):
        """
        Method to print established connections.

        @param connections:      dict of held connections
        @param connections_lock: lock object of the dict

        """

        with connections_lock:

            if not connections:
                self._print('Info', 'No established connection')

            else:

                print('')

                for key, value in connections.items():

                    print(' - Port: {} - IP: {} - Connected: {}'
                        .format(key, value[0], value[1]))

                print('')
