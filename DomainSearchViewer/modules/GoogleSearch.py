# -*- coding: utf-8 -*-

"""
Module for parsing data about Google Search results.
"""

import requests
from lxml import html

from modules import DatasourceBase

################################################################################

class GoogleSearch(DatasourceBase):
    """
    This Module queries google about the domain name and stores the number of
    results.
    """

    # version of the module
    _version = 2015012401

    # dependencies of the module
    _dependencies = set()

    # database query strings of the module
    _queries = {
        'create' : '''
            CREATE TABLE IF NOT EXISTS module_GoogleSearch (
                id INT AUTO_INCREMENT NOT NULL,
                request_id INT NOT NULL,
                addition VARCHAR(255) NOT NULL,
                result INT(32) NOT NULL,
                PRIMARY KEY (id),
                FOREIGN KEY (request_id) REFERENCES requests(id)
            )''',

        'insert' : '''
            INSERT INTO module_GoogleSearch (request_id, addition, result)
            VALUES (%s, %s, %s)''',

        'select' : '''
            SELECT *
            FROM module_GoogleSearch
            WHERE request_id = %s'''
    }

    ############################################################################

    def __init__(self):
        super(GoogleSearch, self).__init__()

    ############################################################################

    def _search(self, request_id, domain, counter):
        """
        Inherited method to start the search. The result will be entered in the
        database.
        """

        search_types = {'link:', 'site:', ''}

        for addition in search_types:

            results = self._get_google_results(domain, addition)

            if addition == '':
                addition = 'normal:'

            addition = addition[:-1]

            self._db.insert_data(
                self._queries['insert'], (request_id, addition, results)
            )

    ############################################################################

    def _get_google_results(self, domain, addition=''):
        """
        Connects to the google.com webpage and gets number of results.
        """

        url = 'https://www.google.de/search'
        payload = {'q': '{}+{}'.format(addition, domain)}

        response = requests.get(url, params=payload)

        self._log.debug('Status code: {}'.format(response.status_code))

        tree = html.fromstring(response.text)

        xpath = tree.xpath('//div[@id="resultStats"]/text()')

        count = xpath[0].split(' ')[1].replace('.', '')

        self._log.debug('PageRank: {}'.format(count))

        return count
