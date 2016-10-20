# -*- coding: utf-8 -*-

"""
The RatingRequestServer handles incoming rating requests.
"""

"""
################################################################################

Messages:

    Client -> RatingRequestServer:

        "request": {
            "rating": {
                "domain": "example.com"
            }
        }

    RatingRequestServer -> Client: invalid request

        "response": {
            "msg": "invalid request"
        }

    RatingRequestServer -> Client: permitted request

        "response": {
            "rating": {
                "domain": "example.com",
                "access": "permitted"
            }
        }

    RatingRequestServer -> Client: denied request

        "response": {
            "rating": {
                "domain": "example.com",
                "access": "denied",
                "comment": "reason for the denial"
            }
        }

################################################################################

Queue structur:

    queued_domain_request_queue = (request_id, domain)

        request_id = int
        domain = str

################################################################################
"""

import json
import socket
import socketserver
from datetime import datetime

from additional import Config
from additional.Logging import Logging

################################################################################

class BasicThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    pass

class RatingRequestServer(BasicThreadedTCPServer):

    # if the server stops/starts quickly, don't fail because of "port in use"
    allow_reuse_address = True

    def __init__(self, addr, handler, arguments):

        self.db = arguments[0]
        self.queued_domain_request_queue = arguments[1]

        self.log = Logging(self.__class__.__name__).get_logger()

        BasicThreadedTCPServer.__init__(self, addr, handler)

################################################################################

class RatingRequestHandler(socketserver.BaseRequestHandler):
    """
    This class searches for an existing and valid entry for the given domain in
    the database and responds it if one was found. If no entry was found, one
    will be created and added to the queue.
    """

    def handle(self):
        """
        Method to handle the request.
        """

        try:

            data = self.request.recv(1024).decode('UTF-8').strip()
            message = json.loads(data)

            # validates message
            if 'request' not in message and \
                'rating' not in message['request'] and \
                'domain' not in message['request']['rating']:

                raise ValueError

            domain = message['request']['rating']['domain']
            domain = domain.lower().strip()

        except ValueError:

            self.server.log.error('Invalid message: {}'.format(data))

            self.request.sendall(bytes(json.dumps({
                'response': {
                    'msg': 'invalid request'
                }
            }), 'UTF-8'))

            return

        except (ConnectionAbortedError, ConnectionResetError,
            ConnectionRefusedError):

            self.server.log.error('Connection aborted: {}'
                .format(self.client_address))

            return

        ########################################################################

        self.server.log.info('Received rating request: {}'.format(domain))

        ########################################################################

        try:

            socket.getaddrinfo(domain, None, family=socket.AF_INET,
                proto=socket.IPPROTO_TCP)

        except socket.gaierror:

            self.server.log.error('Invalid domain: {}'.format(domain))

            self.request.sendall(bytes(json.dumps({
                'response': {
                    'msg': 'invalid domain'
                }
            }), 'UTF-8'))

            return

        ########################################################################

        # checks if the domain already exists in the database
        result = self.server.db.select_data('''
            SELECT id, state, comment, datetime
            FROM domains
            WHERE name = %s''', (domain,))

        ########################################################################

        if result: # domain found

            domain_id = result[0][0]
            domain_state = result[0][1]
            domain_comment = result[0][2]
            domain_updated = result[0][3]

            ####################################################################

            # checks the state of the domain entry

            if domain_state == 'permitted':

                # sends a response to permit the domain
                self.request.sendall(bytes(json.dumps({
                    'response': {
                        'rating': {
                            'domain': domain,
                            'access': 'permitted'
                        }
                    }
                }), 'UTF-8'))

            ####################################################################

            else:

                # sends a response to deny the domain with a comment
                self.request.sendall(bytes(json.dumps({
                    'response': {
                        'rating': {
                            'domain': domain,
                            'access': 'denied',
                            'comment': domain_comment
                        }
                    }
                }), 'UTF-8'))

            ####################################################################

            # checks if the domain entry is expired

            timedelta = datetime.now() - domain_updated

            if timedelta.days < Config.domain_expiration_time:
                return

            ####################################################################

            # gets the most recently request of the domain from the database
            result = self.server.db.select_data('''
                SELECT created
                FROM requests
                WHERE domain_id = %s
                ORDER BY id DESC
                LIMIT 1''', (domain_id,))

            ####################################################################

            if result: # request found

                request_created = result[0][0]

                ################################################################

                # checks if the request entry is expired

                timedelta = datetime.now() - request_created

                if timedelta.days < Config.request_expiration_time:
                    return

        ########################################################################

        else: # domain not found

            # sends a response to permit the domain
            self.request.sendall(bytes(json.dumps({
                'response': {
                    'rating': {
                        'domain': domain,
                        'access': 'permitted'
                    }
                }
            }), 'UTF-8'))

            # creates a new domain entry
            domain_id = self.server.db.insert_data('''
                INSERT INTO domains (name)
                VALUES(%s)''', (domain,))

        ########################################################################

        # creates a new request entry
        request_id = self.server.db.insert_data('''
            INSERT INTO requests (domain_id)
            VALUES(%s)''', (domain_id,))

        # adds the domain to the domain queue with a priority
        self.server.queued_domain_request_queue.put((request_id, domain))

        self.server.log.info('Domain successfully added to the queue: {}'
            .format(domain))
