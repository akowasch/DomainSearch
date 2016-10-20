# -*- coding: utf-8 -*-

"""
Module for querying the google safe browsing API
"""

import requests

from modules import DatasourceBase
from modules import ModuleError

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
        url = 'https://sb-ssl.google.com/safebrowsing/api/lookup?client=api'

        payload = {
            'key': self._get_module_config('api_key'),
            'appver': '1.0',
            'pver': '3.0',
            'url': domain}

        try:
            response = requests.get(url, params=payload)

        except requests.exceptions.ConnectionError:
            raise ModuleError(True)

        self._log.debug('Status code: {}'.format(response.status_code))
        self._log.debug('Content: {}'.format(response.text))

        content = response.text

        if response.status_code is 200: # Ok
            self._db.insert_data(self._queries['insert'], (request_id, content))

        elif response.status_code is 204: # No content
            self._db.insert_data(self._queries['insert'], (request_id, 'ok'))
