# -*- coding: utf-8 -*-

"""
Module for querying the google safe browsing API
"""

import requests

from modules import DatasourceBase

################################################################################

class GoogleSafeBrowsing(DatasourceBase):
    """
    The module uses the API provided by Google to lookup the domainname in the
    blacklists of google
    """

    # version of the module
    _version = 2015012401

    # dependencies of the module
    _dependencies = set()

    # server to connect to
    _server_name = ''
    _server_port = 443

    # database query strings of the module
    _queries = {
        'create' : '''
            CREATE TABLE IF NOT EXISTS module_GoogleSafeBrowsing (
                id INT AUTO_INCREMENT NOT NULL,
                request_id INT NOT NULL,
                state TEXT,
                PRIMARY KEY (id),
                FOREIGN KEY (request_id) REFERENCES requests(id)
            )''',

        'insert' : '''
            INSERT INTO module_GoogleSafeBrowsing (request_id, state)
            VALUES (%s, %s)''',

        'select' : '''
            SELECT *
            FROM module_GoogleSafeBrowsing
            WHERE request_id = %s'''
    }

    ############################################################################

    def __init__(self):
        super(GoogleSafeBrowsing, self).__init__()

    ############################################################################

    def _search(self, request_id, domain, counter):
        """
        Inherited method to start the search. The result will be entered in the
        database.
        """

        state = self._get_state(domain)

        self._db.insert_data(self._queries['insert'], (request_id, state))

    ############################################################################

    def _get_state(self, domain):
        """
        Connects to google API and get the state of the domain.

        @return: state of the domain as string:
                 “phishing” | “malware” | “phishing,malware”
        """

        url = 'https://sb-ssl.google.com/safebrowsing/api/lookup?client=api'

        payload = {
            'key': self._get_module_config('api_key'),
            'appver': '1.0',
            'pver': '3.0',
            'url': domain}

        response = requests.get(url, params=payload)

        self._log.debug('Status code: {}'.format(response.status_code))
        self._log.debug('Content: {}'.format(response.text))

        content = response.text

        if response.status_code is 200:
            return content # response is 200 - Ok

        elif response.status_code is 204:
            return 'ok' # response is 204 - No content
