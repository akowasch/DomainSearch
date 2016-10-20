# -*- coding: utf-8 -*-

"""
Module for loading the Age of the Domain.
"""

import requests

from modules import DatasourceBase
from modules import ModuleError

################################################################################

class DomainAge(DatasourceBase):
    """
    The module uses the API provided by http://archive.org.
    The age is the timestamp of the first snapshot on archive.org.
    """

    # version of the module
    _version = 2015012401

    # dependencies of the module
    _dependencies = set()

    # database query strings of the module
    _queries = {
        'create' : '''
            CREATE TABLE IF NOT EXISTS module_DomainAge (
                id INT AUTO_INCREMENT NOT NULL,
                request_id INT NOT NULL,
                age DATETIME NOT NULL,
                PRIMARY KEY (id),
                FOREIGN KEY (request_id) REFERENCES requests(id)
            )''',

        'insert' : '''
            INSERT INTO module_DomainAge (request_id, age)
            VALUES (%s, %s)''',

        'select' : '''
            SELECT *
            FROM module_DomainAge
            WHERE request_id = %s'''
    }

    ############################################################################

    def __init__(self):
        super(DomainAge, self).__init__()

    ############################################################################

    def _search(self, request_id, domain, counter):
        """
        Connects to archive.org and get timestamp of first entry.
        Uses the API Provided by archive.org.
        @return: Age of the domain as string. (YYYYMMMMDDDDhhmmss)
        """

        url = 'http://archive.org/wayback/available'

        payload = {'url': domain, 'timestamp': ''}

        try:
            response = requests.get(url, params=payload)

        except requests.exceptions.ConnectionError:
            raise ModuleError(True)

        self._log.debug('Status code: {}'.format(response.status_code))

        response = response.json()

        self._log.debug(response)

        try:

            age = response['archived_snapshots']['closest']['timestamp']

            self._db.insert_data(self._queries['insert'], (request_id, age))

        except: # no age found
            self._log.debug('No entry found')
