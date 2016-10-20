# -*- coding: utf-8 -*-

"""
Module for loadiing the robots.txt file
"""

import re
import socket
from http import client

from modules import DatasourceBase
from modules import ModuleError

################################################################################

class RobotsTxt(DatasourceBase):
    """
    The module loads the robots.txt if exists.
    """

    # version of the module
    _version = 2015012401

    # dependencies of the module
    _dependencies = set()

    # database query strings of the module
    _queries = {
        'create' : '''
            CREATE TABLE IF NOT EXISTS module_RobotsTxt (
                id INT AUTO_INCREMENT NOT NULL,
                request_id INT NOT NULL,
                file TEXT,
                PRIMARY KEY (id),
                FOREIGN KEY (request_id) REFERENCES requests(id)
            )''',

        'insert' : '''
            INSERT INTO module_RobotsTxt (request_id, file)
            VALUES (%s, %s)''',

        'select' : '''
            SELECT *
            FROM module_RobotsTxt
            WHERE request_id = %s'''
    }

    ############################################################################

    def __init__(self):
        super(RobotsTxt, self).__init__()

    ############################################################################

    def _search(self, request_id, domain, counter):
        """
        Inherited method to start the search. The result will be entered in the
        database.
        """

        try:

            content = self._get_robots(domain)

            self._db.insert_data(
                self._queries['insert'],
                (request_id, content)
            )

        except socket.gaierror:

            self._report_module_error(request_id, 'No webserver on this domain')

            raise ModuleError

        except Exception as error:

            self._report_module_error(request_id, error)

            raise ModuleError

    ############################################################################

    def _get_robots(self, domain):
        """
        Connects to to the domain and tries to get the robots.txt file.

        @return: content of robots.txt or nothing
        """

        request = '/robots.txt'
        do_again = True
        https = False
        counter = 0

        while do_again and counter < self._get_module_config('max_depth'):

            do_again = False
            counter += 1

            self._log.debug(domain + ' ' + request)

            # open connection

            if https:
                conn = client.HTTPSConnection(domain, 443)

            else:
                conn = client.HTTPConnection(domain, 80)

            conn.request('GET' , request)
            response = conn.getresponse()

            # read response
            code = response.code
            content = response.read().decode('utf-8', 'ignore')

            self._log.debug(code)
            self._log.debug(content)

            # look for location in header fields if code
            # redirects and look again
            if code >= 300 and code <= 303:

                for title, loc in response.getheaders():

                    self._log.debug(title + ' ' + loc)

                    if title.lower() == 'location':

                        match = re.search(r'http(s?)://(.*?)($|/.*)', loc)

                        if match:

                            if match.group(1) == 's':
                                https = True

                            new_request = match.group(3)
                            new_domain = match.group(2)

                            if domain == new_domain and request == new_request:
                                return None

                            if new_request:
                                request = new_request

                            domain = new_domain

                            break

                do_again = True
                conn.close()
                continue

            # return if robots.txt found
            if code is 200:
                return content
