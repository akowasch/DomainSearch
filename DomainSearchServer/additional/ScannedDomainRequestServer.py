# -*- coding: utf-8 -*-

"""
The ScannedDomainRequestServer handles incoming review_task requests.
"""

"""
################################################################################

Messages:

    DomainSearchReviewer -> ScannedDomainRequestServer:

        "request": "task"

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

################################################################################

Queue structur:

    scanned_domain_request_queue = (request_id, domain)

        request_id = int
        domain = str

################################################################################
"""

import time
import json
import queue
import socketserver

from additional import Config
from additional.Logging import Logging

################################################################################

class BasicThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    pass

class ScannedDomainRequestServer(BasicThreadedTCPServer):

    # if the server stops/starts quickly, don't fail because of "port in use"
    allow_reuse_address = True

    def __init__(self, addr, handler, arguments):

        self.reviewers = arguments[0]
        self.reviewers_lock = arguments[1]
        self.running_event = arguments[2]
        self.scanned_domain_request_queue = arguments[3]

        self.log = Logging(self.__class__.__name__).get_logger()

        BasicThreadedTCPServer.__init__(self, addr, handler)

################################################################################

class ScannedDomainRequestHandler(socketserver.BaseRequestHandler):
    """
    This class tries to get a new entry from scanned_domain_request_server queue
    as long as the server is in running state.
    """

    def add_reviewer(self):
        """
        Method to add a reviewer to the list of connected reviewers.
        """

        with self.server.reviewers_lock:

            self.server.reviewers[self.client_address[1]] = (
                self.client_address[0], time.strftime("%d.%m.%Y %H:%M:%S"))

    def remove_reviewer(self):
        """
        Method to remove a reviewer from the list of connected reviewers.
        """

        with self.server.reviewers_lock:
            self.server.reviewers.pop(self.client_address[1])

    ############################################################################

    def handle(self):
        """
        Method to handle the request.
        """

        # adds reviewer to the list of connected reviewers
        self.add_reviewer()

        last_request = None

        while self.server.running_event.is_set():

            try:

                data = self.request.recv(1024).decode('UTF-8').strip()

                # detects disconnected reviewer
                if not data:
                    raise ConnectionAbortedError

                message = json.loads(data)

                # validates message
                if 'request' not in message and message['request'] != 'task':
                    raise ValueError

            except ValueError:

                self.server.log.error('Invalid message: {}'.format(data))

                break

            except (ConnectionAbortedError, ConnectionResetError,
                ConnectionRefusedError):

                # adds the last task back to the queue if not None
                if last_request:
                    self.server.scanned_domain_request_queue.put(last_request)

                self.server.log.info('Connection aborted: {}:{}'
                    .format(self.client_address[0], self.client_address[1]))

                break

            ####################################################################

            self.server.log.info('Received scanned-domain request')

            ####################################################################

            while 1:

                # checks if server wants to shut down
                if not self.server.running_event.is_set():

                    # informs the reviewer of an upcoming server shutdown
                    self.request.sendall(bytes(json.dumps({
                        'response': {
                            'msg': 'shutdown'
                        }
                    }), 'UTF-8'))

                    break

                try:

                    # tries to get a request from scanned-domain-request queue
                    request = self.server.scanned_domain_request_queue.get(
                        timeout=Config.scanned_domain_request_server_timeout)

                    request_id = request[0]
                    domain = request[1]

                    # sends the received domain to the reviewer
                    self.request.sendall(bytes(json.dumps({
                        'response': {
                            'task': {
                                'domain': domain,
                                'request_id': request_id
                            }
                        }
                    }), 'UTF-8'))

                    # saves the last request to add it back to the queue if
                    # meanwhile the reviewer has disconnected
                    last_request = request

                    self.server.scanned_domain_request_queue.task_done()

                    break

                except queue.Empty:
                    pass

        self.remove_reviewer()
