#!/usr/bin/env python3

"""
Module to check blacklisted domains on MXToolbox.com.
"""

import re
import socket
import collections

from modules import DatasourceBase

################################################################################

class MXToolbox(DatasourceBase):
    """
    This module connects to the mxtoolbox.com website and parses data about
    blacklisting of domains.
    """

    # version of the module
    _version = 2015012401

    # dependencies of the module
    _dependencies = set()

    # server to connect to
    _server_name = 'mxtoolbox.com'
    _server_port = 80

    # database query strings of the module
    _queries = {
        'create' : '''
            CREATE TABLE IF NOT EXISTS module_MXToolbox (
                id INT AUTO_INCREMENT NOT NULL,
                request_id INT NOT NULL,
                blacklist VARCHAR(255) NOT NULL,
                state BOOL NOT NULL,
                PRIMARY KEY (id),
                FOREIGN KEY (request_id) REFERENCES requests(id)
            )''',

        'insert' : '''
            INSERT INTO module_MXToolbox (request_id, blacklist, state)
            VALUES (%s, %s, %s)''',

        'select' : '''
            SELECT *
            FROM module_MXToolbox
            WHERE request_id = %s'''
    }

    ############################################################################

    def __init__(self):
        super(MXToolbox, self).__init__()

    ############################################################################

    def _search(self, request_id, domain, counter):
        """
        Inherited method to start the search. The result will be entered in the
        database.
        """

        blacklists = self._get_blacklists(domain)

        for blacklist in blacklists.keys():

            self._db.insert_data(
                self._queries['insert'],
                (request_id, blacklist, blacklists.get(blacklist))
            )

    ############################################################################

    def _get_blacklists(self, domain):
        """
        Connects to the mxtoolbox.com webpage and gets blacklisting data.
        Sends a POST request to the website with the domain to analyze as
        parameter. The result is some malformed JSON data which is parsed with
        regex. The method returns a dictionary with blacklist names and
        corresponding listing state for the given domain.
        """

        content_line = '{"inputText":"blacklist:' + domain + '","resultIndex":1}'

        # build headers
        request = '\r\n'.join([
            'POST /Public/Lookup.aspx/DoLookup2 HTTP/1.1 ',
            'Host: mxtoolbox.com',
            'Content-Type: application/json; charset=utf-8',
            'Content-Length: ' + str(len(content_line)),
            '',
            content_line
        ])

        self._log.debug('Request:\n\n' + request + '\n')

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((self._server_name, self._server_port))
        sock.send(request.encode('utf-8'))

        # Load Header to get the length of the content
        header = ''
        while '\r\n\r\n' not in header:
            header = header + sock.recv(1).decode('UTF-8')

        self._log.debug('Header:\n\n' + header + '\n')

        match = re.search(r'Content-Length: (\d+)', header)
        header_length = int(match.group(1))

        # load the content
        content = ''
        while header_length > 0:
            content = content + sock.recv(1000).decode("utf-8", 'replace')
            header_length -= 1000

        self._log.debug('Content:\n\n' + content + '\n')

        # parse the content
        content = content.replace('\\"', '"').replace('\\\\', "\\")

        blacklists = re.finditer(
            r'nbsp;(\w+)(\\u003c/td\\u003e\\u003ctd\\u003e\\u003cspan class=\\\"bld_name\\\"\\u003e)(\w+(\s?\w*)*)',
            content
        )

        return_list = collections.OrderedDict()

        for entry in blacklists:

            self._log.debug(entry.group(3) + ' ' + entry.group(1))

            return_list[entry.group(3)] = entry.group(1).lower()

        sock.close()

        return return_list
