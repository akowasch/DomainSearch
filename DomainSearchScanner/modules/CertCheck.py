#!/usr/bin/env python3

"""
Module to get informations from domain's certificate and ssl server.
"""

import requests

from modules import DatasourceBase
from modules import ModuleError

################################################################################

class CertCheck(DatasourceBase):
    """
    The module uses the API provided by https://api.dev.ssllabs.com.
    Structure is changing from day to day, so at the moment the entire json will
    be saved until a stable release.
    """

    # version of the module
    _version = 2015012401

    # dependencies of the module
    _dependencies = set()

    # database query strings of the module
    _queries = {
        'create' : '''
            CREATE TABLE IF NOT EXISTS module_CertCheck (
                id INT AUTO_INCREMENT NOT NULL,
                request_id INT NOT NULL,
                json TEXT NOT NULL,
                PRIMARY KEY (id),
                FOREIGN KEY (request_id) REFERENCES requests(id)
            )''',

        'insert' : '''
            INSERT INTO module_CertCheck (
                request_id, json
            )
            VALUES (%s, %s)''',

        'select' : '''
            SELECT *
            FROM module_CertCheck
            WHERE request_id = %s'''
    }

    ############################################################################

    def __init__(self):
        super(CertCheck, self).__init__()

    ############################################################################

    def _search(self, request_id, domain, counter):
        """
        Inherited method to start the search. The result will be entered in the
        database.
        """

        url = "https://api.dev.ssllabs.com/api/fa78d5a4/analyze"

        payload = {'host': domain, 'publish': 'off', 'fromCache': 'on',
            'all': 'done'}

        try:
            response = requests.get(url, params=payload)

        except requests.exceptions.ConnectionError:
            raise ModuleError(True)

        self._log.debug('Status code: {}'.format(response.status_code))

        json_response = response.json()

        self._log.debug(json_response)

        if json_response['status'] == 'READY':

            self._db.insert_data(self._queries['insert'],
                (request_id, response.text))
