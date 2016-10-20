# -*- coding: utf-8 -*-

"""
Module to get informations about the Autonomous System Number (ASN).
Every valid domain has at least one ip address. An ip address belongs to a
subnet. The subnet was assigned to someone by an ASN.
"""

"""
ASN Databases:

data-raw-table: http://thyme.apnic.net/current/data-raw-table
data-used-autnums: http://thyme.apnic.net/current/data-used-autnums
"""

import ipaddress

from modules import DatasourceBase
from modules import ModuleError

################################################################################

class ASN(DatasourceBase):
    """
    """

    # version of the module
    _version = 2015012401

    # dependencies of the module
    _dependencies = set()

    # database query strings of the module
    _queries = {
        'create' : '''
            CREATE TABLE IF NOT EXISTS module_ASN (
                id INT AUTO_INCREMENT NOT NULL,
                request_id INT NOT NULL,
                ip_address VARCHAR(15) NOT NULL,
                asn INT NOT NULL,
                name VARCHAR(255),
                PRIMARY KEY (id),
                FOREIGN KEY (request_id) REFERENCES requests(id)
            )''',

        'insert' : '''
            INSERT INTO module_ASN (request_id, ip_address, asn, name)
            VALUES(%s, %s, %s, %s)''',

        'select' : '''
            SELECT *
            FROM module_ASN
            WHERE request_id = %s'''
    }

    ############################################################################

    def __init__(self):

        super(ASN, self).__init__()
        self._data_raw_table = []
        self._data_used_autnums = []

        try:
            self._init_database()

        except:
            pass

    ############################################################################

    def _init_database(self):

        with open('resources/data-raw-table', 'r', encoding='utf-8') as file:

            for line in file:

                line = line.strip().split('\t')
                self._data_raw_table.append(line)

            self._data_raw_table.reverse()

        with open('resources/data-used-autnums', 'r', encoding='utf-8') as file:

            for line in file:

                line = line.strip().split(' ', maxsplit=1)
                self._data_used_autnums.append(line)

    ############################################################################

    def _search(self, request_id, domain, counter):
        """
        Inherited method to start the search. The result will be entered in the
        database.
        """

        if not(self._data_raw_table and self._data_used_autnums):

            self._report_module_error(request_id, 'ASN Database not found')

            raise ModuleError

        asn_counter = 0

        for ip in self._get_ip_addresses(domain):

            asn = None
            name = None

            for entry in self._data_raw_table:

                # Description: _data_raw_table: [[subnet, asn], ...]

                # checks if ip address is part of the subnet
                if ip.split('.')[0] == entry[0].split('.')[0] and \
                    ipaddress.ip_address(ip) in ipaddress.ip_network(entry[0]):

                    asn = entry[1]
                    break

            if not asn:
                continue

            for line in self._data_used_autnums:

                if line[0] == asn:

                    name = line[1]
                    break

            if not name:
                continue

            self._log.debug(
                'Request ID: {} - Domain: {} - IP: {} - ASN: {} - Name: {}'
                .format(request_id, domain, ip, asn, name))

            self._db.insert_data(self._queries['insert'],
                (request_id, ip, asn, name))

            asn_counter += 1

        if asn_counter == 0:

            self._report_module_error(request_id, 'ASN not found')

            raise ModuleError
