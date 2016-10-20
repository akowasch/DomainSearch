# -*- coding: utf-8 -*-

"""
Module to check domain for viruses.
"""

"""
################################################################################

Quota:

    Request rate   4 requests/minute
    Daily quota    5760 requests/day
    Monthly quota  178560 requests/month

################################################################################
"""

import requests

from modules import DatasourceBase
from modules import ModuleError

################################################################################

class VirusTotal(DatasourceBase):
    """
    This module uses the API from VirusTotal.com.
    """

    # version of the module
    _version = 2015012401

    # dependencies of the module
    _dependencies = set()

    # database query strings of the module
    _queries = {
        'create' : '''
            CREATE TABLE IF NOT EXISTS module_VirusTotal (
                id INT AUTO_INCREMENT NOT NULL,
                request_id INT NOT NULL,
                service VARCHAR(50) NOT NULL,
                detected INT NOT NULL,
                PRIMARY KEY (id),
                FOREIGN KEY (request_id) REFERENCES requests(id)
            )''',

        'insert' : '''
            INSERT INTO module_VirusTotal (request_id, service, detected)
            VALUES (%s, %s, %s)''',

        'select' : '''
            SELECT *
            FROM module_VirusTotal
            WHERE request_id = %s'''
    }

    def __init__(self):
        super(VirusTotal, self).__init__()

    ############################################################################

    def _search(self, request_id, domain, counter):
        """
        Inherited method to start the search. The result will be entered in the
        database.
        """

        url = 'http://www.virustotal.com/vtapi/v2/url/report'

        payload = {
            'resource': domain,
            'scan': '1',
            'apikey': self._get_module_config('api_key')}

        try:
            response = requests.post(url, params=payload)

        except requests.exceptions.ConnectionError:
            raise ModuleError(True)

        self._log.debug('Status code: {}'.format(response.status_code))

        ########################################################################

        # checks if the request rate limit is exceeded
        if response.status_code == 204 or not response:
            raise ModuleError(True)

        ########################################################################

        # converts to json output
        response = response.json()

        self._log.debug(response)

        ########################################################################

        if 'positives' in response:

            for key, value in response['scans'].items():

                self._db.insert_data(
                    self._queries['insert'],
                    (request_id, key, 1 if value['detected'] else 0))

        else: # requested item is still queued for analysis
            raise ModuleError(True)
