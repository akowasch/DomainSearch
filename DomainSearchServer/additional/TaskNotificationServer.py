# -*- coding: utf-8 -*-

"""
The TastNotificationServer handles incoming scan_tak_finished and
review_task_finished requests.
"""

"""
################################################################################


Messages:

    DomainSearchScanner -> TaskNotificationServer: scan finished

        "notification": {
            "scan": {
                "domain": "example.com",
                "request_id": 1
            }
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

Queue structur:

    scanned_domain_request_queue = (request_id, domain)

        request_id = int
        domain = str

################################################################################
"""

import json
import socketserver

from additional.Logging import Logging

################################################################################

class BasicThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    pass

class TaskNotificationServer(BasicThreadedTCPServer):

    # if the server stops/starts quickly, don't fail because of "port in use"
    allow_reuse_address = True

    def __init__(self, addr, handler, arguments):

        self.db = arguments[0]
        self.scanned_domain_request_queue = arguments[1]

        self.log = Logging(self.__class__.__name__).get_logger()

        BasicThreadedTCPServer.__init__(self, addr, handler)

################################################################################

class TaskNotificationHandler(socketserver.BaseRequestHandler):
    """
    This class updates database tables for incoming scan_task_finished or
    review_task_finished requests. It also puts finished tasks from
    scan_task_finished to the scanned_domain_request queue.
    """

    def handle(self):
        """
        Method to handle the request.
        """

        try:

            data = self.request.recv(1024).decode('UTF-8').strip()
            message = json.loads(data)

            # accepts only valid messages containing a notification
            if 'notification' not in message:
                raise ValueError

            message = message['notification']

        except ValueError:

            self.server.log.error('Invalid message: {}'.format(data))

            return

        except (ConnectionAbortedError, ConnectionResetError,
            ConnectionRefusedError):

            self.server.log.error('Connection aborted: {}'
                .format(self.client_address))

            return

        ########################################################################

        self.server.log.info('Received task-done notification: {}'
            .format(message))

        ########################################################################

        # checks if message is a finished scan task

        if 'scan' in message and \
            'domain' in message['scan'] and \
            'request_id' in message['scan']:

            message = message['scan']
            domain = message['domain']
            request_id = message['request_id']

            # validates task in database
            if not self.server.db.is_request_valid(request_id, domain):

                self.server.log.error('Invalid request: {}'.format(message))

                return

            # updates the request entry
            self.server.db.update_data('''
                UPDATE requests
                SET state = 'scanned',
                    comment = ''
                WHERE id = %s''', (request_id,))

            # adds the domain to the scanned domain request queue
            self.server.scanned_domain_request_queue.put((request_id, domain))

        ########################################################################

        # checks if message is a finished review task

        elif 'review' in message and \
            'domain' in message['review'] and \
            'request_id' in message['review'] and \
            'access' in message['review']:

            message = message['review']
            domain = message['domain']
            request_id = message['request_id']
            access = message['access']
            comment = message['comment'] if message['comment'] else ''

            # validates task in database
            if not self.server.db.is_request_valid(request_id, domain):

                self.server.log.error('Invalid request: {}'.format(message))

                return

            # updates the request entry
            self.server.db.update_data('''
                UPDATE requests
                SET state = %s,
                    comment = %s
                WHERE id = %s''',
                (access, comment, request_id,))

            # updates the domain entry
            self.server.db.update_data('''
                UPDATE domains
                SET state = %s,
                    comment = %s
                WHERE name = %s''', (access, comment, domain,))

        ########################################################################

        # reject invalid message

        else:

            self.server.log.error(
                'Received message is not a valid notification: {}'
                .format(data))
