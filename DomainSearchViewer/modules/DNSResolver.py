# -*- coding: utf-8 -*-

"""
Module for resolving DNS records.
"""

import dns.name
import dns.message
import dns.query
import dns.reversename
import dns.rdtypes.ANY.SOA
import dns.rdtypes.IN.A

from modules import DatasourceBase

################################################################################

class DNSResolver(DatasourceBase):
    """
    This module uses dnsPython to resolve the DNS records of the given domain.
    it also does a reverse lookup and writes the results into the database.
    """

    # version of the module
    _version = 2015012401

    # dependencies of the module
    _dependencies = set()

    # counter for lookup recursions
    _recursion = 0

    # set of found data by the lookups
    _complete_set = set()

    # database query strings of the module
    _queries = {
        'create' : '''
            CREATE TABLE IF NOT EXISTS module_DNSResolver (
                id INT AUTO_INCREMENT NOT NULL,
                request_id INT NOT NULL,
                name VARCHAR(255),
                ttl INT,
                class VARCHAR(5),
                type VARCHAR(5),
                rdata TEXT,
                PRIMARY KEY (id),
                FOREIGN KEY (request_id) REFERENCES requests(id)
            )''',

        'insert' : '''
            INSERT INTO module_DNSResolver (request_id, name, ttl, class, type, rdata)
            VALUES (%s, %s, %s, %s, %s, %s)''',

        'select' : '''
            SELECT *
            FROM module_DNSResolver
            WHERE request_id = %s
            ORDER BY name'''
    }

    ############################################################################

    def __init__(self):
        super(DNSResolver, self).__init__()

    ############################################################################

    def _search(self, request_id, domain, counter):
        """
        Inherited method to start the search. The result will be entered in the
        database.
        """

        # clear set and recursion
        self._complete_set = set()
        self._recursion = 0

        # search for SOA record with nameserver from configuration file
        soa_nameserver = self._find_nameserver(domain,
            self._get_module_config('nameserver'))

        # lookup for ANY on SOA Nameserver
        self._lookup(request_id, domain, soa_nameserver)

        # reverse lookup for all IPs on default nameserver
        self._reverse_lookup(request_id,
            self._get_module_config('nameserver'))

        sorted_set = list(self._complete_set)

        # sort a list of tuples by the second key
        sorted_set.sort(key = lambda item: item[1])

        for line in sorted_set:
            self._db.insert_data(self._queries['insert'], line)

    ############################################################################

    def _find_nameserver(self, domain, nameserver):
        """
        Searches for the first Authority nameserver
        """

        ans = self._resolve(domain.strip(), nameserver, 'SOA')

        if ans:

            for section in ans:

                for block in section:

                    if type(block[0]) is dns.rdtypes.ANY.SOA.SOA:

                        ns_name = str(block[0].mname)

                        # resolve ip adress for the nameserver
                        ans = self._resolve(ns_name, nameserver, 'A')

                        for block in ans[0]:

                            if type(block[0]) is dns.rdtypes.IN.A.A:

                                return block[0].address

    ############################################################################

    def _lookup(self, request_id, domain, nameserver):
        """
        Does a lookup for the given domain and writes the answer to the db.
        Does a DNS Lookup for recordtype ANY. If the answer contains no A or
        AAAA record, those recordtypes are requested separately.
        """

        self._recursion += 1
        ans = self._resolve(domain, nameserver, recordtype='ANY')

        result = self._insert_into_set(request_id, ans)

        if not result[0]:  # type A

            ans = self._resolve(domain, nameserver, recordtype='A')
            self._insert_into_set(request_id, ans)

        if not result[1]:  # type AAAA

            ans = self._resolve(domain, nameserver, recordtype='AAAA')
            self._insert_into_set(request_id, ans)

        if self._recursion < self._get_module_config('max_recursions'):

            for cname in result[2]:  # type CNAME

                ans = self._lookup(request_id, cname, nameserver)
                self._insert_into_set(request_id, ans)

    ############################################################################

    def _reverse_lookup(self, request_id, nameserver):
        """
        Does a reverse lookup for every IPv4 and IPv6 Adress.
        Queries the database for prviously resolved IP adresses and does a
        reverse lookup. Also stores the result in the database.
        """

        ip_list = []

        for line in self._complete_set:

            if line[4] == 'A' or line[4] == 'AAAA':
                ip_list.append(line[5])

        for rdata in ip_list:

            reverse_ans = self._resolve(
                dns.reversename.from_address(str(rdata)), nameserver)

            self._insert_into_set(request_id, reverse_ans)

    ############################################################################

    def _insert_into_set(self, request_id, answer):
        """
        Inserts the given answer into the set of found data
        the answer should be the answer section of the lookup result.
        """

        has_a = has_aaaa = False
        cnames = set()

        if answer:

            for section in answer:

                for block in section:

                    self._log.debug(block)

                    name = str(block.name)
                    ttl = block.ttl
                    rdclass = str(dns.rdataclass.to_text(block.rdclass))
                    rdtype = str(dns.rdatatype.to_text(block.rdtype))

                    for entry in block:

                        data = (request_id, name, ttl, rdclass, rdtype,
                            str(entry))

                        self._complete_set.add(data)

                        if rdtype is 'CNAME':
                            cnames.add(entry.target)

                    if rdtype is 'A':
                        has_a = True

                    if rdtype is 'AAAA' :
                        has_aaaa = True

        return (has_a, has_aaaa, cnames)

    ############################################################################

    def _resolve(self, domain, nameserver, recordtype='ANY'):
        """
        Resolves a given domain name.
        Returns the answer section of the DNS Response.
        """

        additional_rdclass = 65535

        self._log.debug(str(domain) + ' ' + recordtype)

        request = dns.message.make_query(domain, recordtype)
        request.flags |= dns.flags.AD
        request.find_rrset(
            request.additional,
            dns.name.root,
            additional_rdclass,
            dns.rdatatype.OPT,
            create = True,
            force_unique = True
        )

        self._log.debug('Request: \r\n\r\n{}\r\n\r\nNameserver: {}\r\n'
            .format(request, nameserver))

        try:

            response = dns.query.udp(request, nameserver, timeout=3)

            self._log.debug('Response: \r\n\r\n{}\r\n'.format(response))

            return response.answer, response.authority, response.additional

        except:
            self._log.debug('Response: No response')
