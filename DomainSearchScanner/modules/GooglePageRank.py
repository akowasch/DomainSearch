# -*- coding: utf-8 -*-

"""
Module for parsing data about Google Search results.
"""

import requests

from modules import DatasourceBase
from modules import ModuleError

################################################################################

class GooglePageRank(DatasourceBase):
    """
    This Module gets the google Page Rank from http://www.prapi.net/.
    """

    # version of the module
    _version = 2015012401

    # dependencies of the module
    _dependencies = set()

    # database query strings of the module
    _queries = {
        'create' : '''
            CREATE TABLE IF NOT EXISTS module_GooglePageRank (
                id INT AUTO_INCREMENT NOT NULL,
                request_id INT NOT NULL,
                pagerank TINYINT(1) NOT NULL,
                PRIMARY KEY (id),
                FOREIGN KEY (request_id) REFERENCES requests(id)
            )''',

        'insert' : '''
            INSERT INTO module_GooglePageRank (request_id, pagerank)
            VALUES (%s, %s)''',

        'select' : '''
            SELECT *
            FROM module_GooglePageRank
            WHERE request_id = %s'''
    }

    ############################################################################

    def __init__(self):
        super(GooglePageRank, self).__init__()

    ############################################################################

    def _search(self, request_id, domain, counter):
        """
        Inherited method to start the search. The result will be entered in the
        database.
        """

        url = 'http://www.prapi.net/pr.php'

        payload = {'url': domain, 'f': 'json'}

        try:
            response = requests.get(url, params=payload)

        except requests.exceptions.ConnectionError:
            raise ModuleError(True)

        self._log.debug('Status code: {}'.format(response.status_code))

        response = response.json()

        self._log.debug(response)

        page_rank = response['pagerank']

        self._db.insert_data(self._queries['insert'], (request_id, page_rank))
