# -*- coding: utf-8 -*-

"""
Collects Whois Information about the given Domain.
"""

import os
from datetime import datetime

import pythonwhois

from modules import DatasourceBase

################################################################################

class Whois(DatasourceBase):
    """
    Simple Version without parsing of the content.
    """

    # version of the module
    _version = 2015012401

    # dependencies of the module
    _dependencies = set()

    # database query strings of the module
    _queries = {
        'create' : ['''
            CREATE TABLE IF NOT EXISTS module_Whois (
                id INT AUTO_INCREMENT NOT NULL,
                request_id INT NOT NULL,
                domain_id INT,
                status TEXT,
                creation_date DATETIME,
                expiration_date DATETIME,
                updated_date DATETIME,
                registrar TEXT,
                whois_server TEXT,
                nameservers TEXT,
                emails TEXT,
                PRIMARY KEY (id),
                FOREIGN KEY (request_id) REFERENCES requests(id)
            )''',
            '''
            CREATE TABLE IF NOT EXISTS module_WhoisContacts (
                id INT AUTO_INCREMENT NOT NULL,
                whois_id INT NOT NULL,
                type VARCHAR(10),
                handle VARCHAR(255),
                name VARCHAR(255),
                organisation VARCHAR(255),
                street VARCHAR(255),
                postalcode VARCHAR(255),
                city VARCHAR(255),
                state VARCHAR(255),
                country VARCHAR(255),
                email VARCHAR(255),
                phone VARCHAR(255),
                fax VARCHAR(255),
                PRIMARY KEY (id),
                FOREIGN KEY (whois_id) REFERENCES module_Whois(id)
            )'''],

        'insert' : ['''
            INSERT INTO module_Whois (
                request_id, domain_id, status, creation_date, expiration_date,
                updated_date, registrar, whois_server, nameservers, emails
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)''',
            '''
            INSERT INTO module_WhoisContacts (
                whois_id, type, handle, name, organisation, street, postalcode,
                city, state, country, email, phone, fax
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)'''
            ],

        'select' : '''
            SELECT *
            FROM module_Whois
            WHERE request_id = %s'''
    }

    ############################################################################

    def __init__(self):
        super(Whois, self).__init__()

    ############################################################################

    def _search(self, request_id, domain, counter):
        """
        Inherited method to start the search. The result will be entered in the
        database.
        """

        domain_parts = domain.split('.')

        if len(domain_parts) >= 3 and domain_parts[0] == 'www':
            domain_parts = domain_parts[1:]

        ########################################################################

        try:
            whois = pythonwhois.get_whois('.'.join(domain_parts))

        except pythonwhois.shared.WhoisException:

            self._log.error('No root server for the TLD could be found')

            return

        self._log.debug(whois)

        ########################################################################

        for arg in whois:

            if isinstance(whois[arg], list):

                for i, e in enumerate(whois[arg]):

                    if isinstance(e, datetime):
                        whois[arg][i] = e.strftime("%Y-%m-%d %H:%M:%S")

                whois[arg] = os.linesep.join(whois[arg])

        ########################################################################

        whois_id = self._db.insert_data(
            self._queries['insert'][0], (
                request_id,
                whois['id'] if 'id' in whois else '',
                whois['status'] if 'status' in whois else '',
                whois['creation_date'] if 'creation_date' in whois else '',
                whois['expiration_date'] if 'expiration_date' in whois else '',
                whois['updated_date'] if 'updated_date' in whois else '',
                whois['registrar'] if 'registrar' in whois else '',
                whois['whois_server'] if 'whois_server' in whois else '',
                whois['nameservers'] if 'nameservers' in whois else '',
                whois['emails'] if 'emails' in whois else ''))

        ########################################################################

        if 'contacts' in whois:

            for key, value in whois['contacts'].items():

                if not value:
                    continue

                self._db.insert_data(
                    self._queries['insert'][1], (
                        whois_id,
                        key,
                        value['handle'] if 'handle' in value else '',
                        value['name'] if 'name' in value else '',
                        value['organisation'] if 'organisation' in value else '',
                        value['street'] if 'street' in value else '',
                        value['postalcode'] if 'postalcode' in value else '',
                        value['city'] if 'city' in value else '',
                        value['state'] if 'state' in value else '',
                        value['country'] if 'country' in value else '',
                        value['email'] if 'email' in value else '',
                        value['phone'] if 'phone' in value else '',
                        value['fax'] if 'fax' in value else ''))
