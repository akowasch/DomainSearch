# -*- coding: utf-8 -*-

"""
Module to check blacklisted ip addresses on IPVoid.com.
"""

import requests
from lxml import html

from modules import DatasourceBase
from modules import ModuleError

################################################################################

class IPVoid(DatasourceBase):
    """
    This module connects to the IPVoid.com website and parses data about
    blacklisting of ip addresses. Must run after the DNSresolver module because
    IPVoid will need the domains IP addresses for searching.
    """

    # version of the module
    _version = 2015012401

    # dependencies of the module
    _dependencies = set()

    # database query strings of the module
    _queries = {
        'create' : '''
            CREATE TABLE IF NOT EXISTS module_IPVoid (
                id INT AUTO_INCREMENT NOT NULL,
                request_id INT NOT NULL,
                ip_address VARCHAR(15) NOT NULL,
                blacklist VARCHAR(255) NOT NULL,
                state BOOL NOT NULL,
                PRIMARY KEY (id),
                FOREIGN KEY (request_id) REFERENCES requests(id)
            )''',

        'insert' : '''
            INSERT INTO module_IPVoid (
                request_id, ip_address, blacklist, state
            )
            VALUES (%s, %s, %s, %s)''',

        'select' : '''
            SELECT *
            FROM module_IPVoid
            WHERE request_id = %s'''
    }

    ############################################################################

    def __init__(self):
        super(IPVoid, self).__init__()

    ############################################################################

    def _search(self, request_id, domain, counter):
        """
        Inherited method to start the search. The result will be entered in the
        database.
        """

        for ip_address in self._get_ip_addresses(domain):

            blacklists = self._get_blacklists(ip_address)

            for blacklist in blacklists:

                self._db.insert_data(self._queries['insert'],
                    (request_id, ip_address, blacklist[0], blacklist[1]))

    ############################################################################

    def _get_blacklists(self, ip_address):
        """
        Connects to the IPVoid.com webpage and gets blacklisting data.

        Sends a POST request to the website with the domain to analyze as
        parameter. The result is parsed with regex. The method returns a
        dictionary with blacklist names and corresponding listing state for
        the given domain.
        """

        blacklists = set()

        url = 'http://ipvoid.com'
        payload = {'ip': ip_address}
        headers = {'content-type': 'application/x-www-form-urlencoded'}

        try:
            response = requests.post(url, data=payload, headers=headers)

        except requests.exceptions.ConnectionError:
            raise ModuleError(True)

        self._log.debug('IP: {} - Status code: {}'
            .format(ip_address, response.status_code))

        url = 'http://ipvoid.com/scan/{}'.format(ip_address)

        try:
            response = requests.get(url)

        except requests.exceptions.ConnectionError:
            raise ModuleError(True)

        tree = html.fromstring(response.text)

        xpath = tree.xpath(
            '//h3[@id="ip-blacklist-report"]/following::tbody/tr')

        for tr in xpath:

            name = tr.xpath('td[1]/text()')[0].strip()
            state = tr.xpath('td[2]/img')[0].get('alt')

            state = 1 if state == 'Clean' else '0'

            blacklists.add((name, state))

        self._log.debug(blacklists)

        return blacklists
