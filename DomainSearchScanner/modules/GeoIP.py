# -*- coding: utf-8 -*-

"""
Module for loading GeoIP data.
"""

import requests

from modules import DatasourceBase
from modules import ModuleError

################################################################################

class GeoIP(DatasourceBase):
    """
    The module uses the API provided by http://freegeoip.net.
    """

    # version of the module
    _version = 2015012401

    # dependencies of the module
    _dependencies = set()

    # database query strings of the module
    _queries = {
        'create' : '''
            CREATE TABLE IF NOT EXISTS module_GeoIP (
                id INT AUTO_INCREMENT NOT NULL,
                request_id INT NOT NULL,
                ip_address VARCHAR(15) NOT NULL,
                country_code VARCHAR(10),
                country_name VARCHAR(255),
                region_code VARCHAR(10),
                region_name VARCHAR(255),
                city VARCHAR(255),
                zip_code VARCHAR(10),
                latitude VARCHAR(15),
                longitude VARCHAR(15),
                metro_code VARCHAR(10),
                PRIMARY KEY (id),
                FOREIGN KEY (request_id) REFERENCES requests(id)
            )''',

        'insert' : '''
            INSERT INTO module_GeoIP (
                request_id, ip_address, country_code, country_name, region_code,
                region_name, city, zip_code, latitude, longitude, metro_code
            )
            VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)''',

        'select' : '''
            SELECT
                id,
                request_id,
                CONCAT('IP: ', ip_address),
                CONCAT('Country: ', country_code, ' ', country_name),
                CONCAT('Region: ', region_code, ' ', region_name),
                CONCAT('City: ', city, ' ', zip_code),
                CONCAT('Pos: ', latitude, ', ', longitude),
                CONCAT('MC: ', metro_code)
            FROM module_GeoIP
            WHERE request_id = %s'''
    }

    ############################################################################

    def __init__(self):
        super(GeoIP, self).__init__()

    ############################################################################

    def _search(self, request_id, domain, counter):
        """
        Inherited method to start the search. The result will be entered in the
        database.
        """

        # get locations for ip addresses and write the result to database
        for ip in self._get_ip_addresses(domain):

            url = "http://localhost:8080/json/{}".format(ip)

            try:
                response = requests.get(url)

            except requests.exceptions.ConnectionError:
                raise ModuleError(True)

            self._log.debug('Status code: {}'.format(response.status_code))

            response = response.json()

            self._log.debug(response)

            insert_values = (
                request_id, response.get('ip'), response.get('country_code'),
                response.get('country_name'), response.get('region_code'),
                response.get('region_name'), response.get('city'),
                response.get('zip_code'), response.get('latitude'),
                response.get('longitude'), response.get('metro_code')
            )

        self._db.insert_data(self._queries['insert'], insert_values)
