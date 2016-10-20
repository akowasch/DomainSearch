# -*- coding: utf-8 -*-

"""
The QueuedDomainRequestServer handles incoming scan_task requests.
"""

"""
################################################################################

Messages:

    DomainSearchScanner -> QueuedDomainRequestServer:

        "request": "task"

    QueuedDomainRequestServer -> DomainSearchScanner: scan request

        "response": {
            "task": {
                "domain": "example.com",
                "request_id": 1
            }
        }

    QueuedDomainRequestServer -> DomainSearchScanner: shutdown triggered

        "response": {
            "msg": "shutdown"
        }

################################################################################

Queue structur:

    queued_domain_request_queue = (request_id, domain)

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

class QueuedDomainRequestServer(BasicThreadedTCPServer):

    # if the server stops/starts quickly, don't fail because of "port in use"
    allow_reuse_address = True

    def __init__(self, addr, handler, arguments):

        self.scanners = arguments[0]
        self.scanners_lock = arguments[1]
        self.running_event = arguments[2]
        self.queued_domain_request_queue = arguments[3]

        self.log = Logging(self.__class__.__name__).get_logger()

        BasicThreadedTCPServer.__init__(self, addr, handler)

################################################################################

class QueuedDomainRequestHandler(socketserver.BaseRequestHandler):
    """
    This class tries to get a new entry from queued_domain_request queue as long
    as the server is in running state.
    """

    def _add_scanner(self):
        """
        Method to add a scanner to the list of connected scanners.
        """

        with self.server.scanners_lock:

            self.server.scanners[self.client_address[1]] = (
                self.client_address[0], time.strftime("%d.%m.%Y %H:%M:%S"))

    def _remove_scanner(self):
        """
        Method to remove a scanner from the list of connected scanners.
        """

        with self.server.scanners_lock:
            self.server.scanners.pop(self.client_address[1])

    ############################################################################

    def handle(self):
        """
        Method to handle the request.
        """

        # adds scanner to the list of connected scanners
        self._add_scanner()

        last_request = None

        while self.server.running_event.is_set():

            try:

                data = self.request.recv(1024).decode('UTF-8').strip()

                # detects disconnected scanner
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
                    self.server.queued_domain_request_queue.put(last_request)

                self.server.log.info('Connection aborted: {}:{}'
                    .format(self.client_address[0], self.client_address[1]))

                break

            ####################################################################

            self.server.log.info('Received queued-domain request')

            ####################################################################

            while 1:

                # checks if server wants to shut down
                if not self.server.running_event.is_set():

                    # informs the scanner of an upcoming server shutdown
                    self.request.sendall(bytes(json.dumps({
                        'response': {
                            'msg': 'shutdown'
                        }
                    }), 'UTF-8'))

                    break

                try:

                    # tries to get a request from queued-domain-request queue
                    request = self.server.queued_domain_request_queue.get(
                        timeout=Config.queued_domain_request_server_timeout)

                    request_id = request[0]
                    domain = request[1]

                    # sends the received domain to the scanner
                    self.request.sendall(bytes(json.dumps({
                        'response': {
                            'task': {
                                'domain': domain,
                                'request_id': request_id
                            }
                        }
                    }), 'UTF-8'))

                    # saves the last request to add it back to the queue if
                    # meanwhile the scanner has disconnected
                    last_request = request

                    self.server.queued_domain_request_queue.task_done()

                    break

                except queue.Empty:
                    pass

        self._remove_scanner()
