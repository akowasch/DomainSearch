# -*- coding: utf-8 -*-

"""
Collects Routing Information to the given Domain.
"""

import socket

from modules import DatasourceBase

################################################################################

class Traceroute(DatasourceBase):
    """
    Simple Version without parsing of the content.
    """

    # version of the module
    _version = 2015012401

    # dependencies of the module
    _dependencies = set()

    # database query strings of the module
    _queries = {
        'create' : '''
            CREATE TABLE IF NOT EXISTS module_Traceroute (
                id INT AUTO_INCREMENT NOT NULL,
                request_id INT NOT NULL,
                ttl INT NOT NULL,
                hostname VARCHAR(255),
                ip_address VARCHAR(15) NOT NULL,
                PRIMARY KEY (id),
                FOREIGN KEY (request_id) REFERENCES requests(id)
            )''',

        'insert' : '''
            INSERT INTO module_Traceroute (
                request_id, ttl, hostname, ip_address)
            VALUES (%s, %s, %s, %s)''',

        'select' : '''
            SELECT *
            FROM module_Traceroute
            WHERE request_id = %s'''
    }

    ############################################################################

    def __init__(self):
        super(Traceroute, self).__init__()

    ############################################################################

    def _search(self, request_id, domain, counter):
        """
        Inherited method to start the search. The result will be entered in the
        database.
        """

        # gets possible destination ip addresses from domain

        dest_addr = self._get_ip_addresses(domain)

        port = self._get_module_config('port')
        max_hops = self._get_module_config('max_hops')

        icmp = socket.getprotobyname('icmp')
        udp = socket.getprotobyname('udp')

        for ttl in range(1, max_hops):

            recv_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, icmp)
            send_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, udp)

            send_socket.setsockopt(socket.SOL_IP, socket.IP_TTL, ttl)
            recv_socket.settimeout(self._get_module_config('timeout'))

            recv_socket.bind(("", port))

            send_socket.sendto(bytes("", 'UTF-8'), (domain, port))

            curr_addr = None
            curr_name = ''

            try:

                _, curr_addr = recv_socket.recvfrom(512)
                curr_addr = curr_addr[0]

                try:
                    curr_name = socket.gethostbyaddr(curr_addr)[0]

                except socket.error:
                    pass

            except socket.error:
                pass

            finally:

                send_socket.close()
                recv_socket.close()

            if curr_addr is not None:

                self._log.debug(curr_name + ' - ' + curr_addr)

                self._db.insert_data(
                    self._queries['insert'],
                    (request_id, ttl, curr_name, curr_addr)
                )

            if curr_addr in dest_addr:
                break
