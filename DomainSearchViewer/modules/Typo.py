# -*- coding: utf-8 -*-

"""
Tests differens Typo domains for existence
"""

import queue
import socket
import threading

from modules import DatasourceBase

################################################################################

class Typo(DatasourceBase):
    """
    Tests differens Typo domains for existence.
    """

    # version of the module
    _version = 2015012401

    # dependencies of the module
    _dependencies = set()

    # database query strings of the module
    _queries = {
        'create' : '''
            CREATE TABLE IF NOT EXISTS module_Typo (
                id INT AUTO_INCREMENT NOT NULL,
                request_id INT NOT NULL,
                typo_name VARCHAR(255) NOT NULL,
                PRIMARY KEY (id),
                FOREIGN KEY (request_id) REFERENCES requests(id)
            )''',

        'insert' : '''
            INSERT INTO module_Typo (request_id, typo_name)
            VALUES (%s, %s)''',

        'select' : '''
            SELECT *
            FROM module_Typo
            WHERE request_id = %s'''
    }

    ############################################################################

    def __init__(self):
        super(Typo, self).__init__()

    ############################################################################

    def _search(self, request_id, domain, counter):
        """
        Inherited method to start the search. The result will be entered in the
        database.
        """

        answer = self._query(domain)

        for line in answer:

            self._db.insert_data(
                self._queries['insert'],
                (request_id, line)
            )

    ############################################################################

    def _generate_typos(self, domain):
        """
        Generates a bunch of typo domain names
        """

        tld_index = domain.rfind('.')
        tld = domain[tld_index:]
        domain = domain[:tld_index]

        typos = set()

        # without minus and dot
        typos.add(domain.replace('.', '') + tld)
        typos.add(domain.replace('-', '') + tld)

        # Double chars at every position
        # forgotten char at every position
        # Transposed characters
        for i in range(0, len(domain)):

            if domain[i].isalnum():

                typos.add(domain[:i + 1] + domain[i:] + tld)
                typos.add(domain[:i] + domain[i + 1:] + tld)

                if i < len(domain) - 1:

                    typos.add(
                        domain[:i] +
                        domain[i + 1] +
                        domain[i] +
                        domain[i + 2:] +
                        tld
                    )

        ########################################################################

        def permute(parts, char, prefix='', sep=''):
            """
            Varies combinations of parts
            """

            for i in range(1, len(parts)):

                typos.add(
                    prefix +
                    sep.join(parts[:i]) +
                    char +
                    sep.join(parts[i:]) +
                    tld
                )

                permute(parts[i:], char, prefix + sep.join(parts[:i]) + char)

        ########################################################################

        # combine - and . in varous patterns
        permute(domain.split('.'), '.')
        permute(domain.split('-'), '-')

        # add www without . in front of domainname
        typos.add('www' + domain + tld)

        # various combinations of common mistaktes
        for item in self._get_module_config('common_mistakes'):

            typos.add(domain.replace(item[0], item[1]) + tld)
            typos.add(domain.replace(item[1], item[0]) + tld)
            permute(domain.split(item[0]), item[1], sep=item[0])
            permute(domain.split(item[1]), item[0], sep=item[1])


        # append common TLDs to all found typos
        for typo in typos.copy():

            for tld in self._get_module_config('common_tlds'):
                typos.add(typo[:typo.rfind('.')] + tld)

        # discard domainname if it exist
        typos.discard(domain + tld)

        # discard unusable typos
        for typo in typos.copy():

            if typo.startswith('-') or typo.startswith('.'):
                typos.discard(typo)

        # and sort the result
        typos = list(typos)
        typos.sort()

        self._log.debug(str(len(typos)))

        return typos

    ############################################################################

    def _query(self, domain):
        """
        Generates different Typo names and digs them to see if they exist.
        Limits the number of threads (config)
        """

        typo_queue = queue.Queue()

        for line in self._generate_typos(domain):
            typo_queue.put(line)

        found_typos = set()

        domain_ip_addresses = self._get_ip_addresses(domain)

        lock = threading.Lock()

        ########################################################################

        def worker():
            """
            serach for every typo, but limit the number of threads
            """

            while not typo_queue.empty():

                typo = typo_queue.get()

                try:

                    typo_ip_addresses = self._get_ip_addresses(typo)

                    # adds typo to set if no common ip addresses exists
                    if not typo_ip_addresses & domain_ip_addresses:

                        with lock:
                            found_typos.add(typo)

                except socket.gaierror:
                    pass

                typo_queue.task_done()

        ########################################################################

        threads = []

        for _ in range(self._get_module_config('max_threads')):

            thread = threading.Thread(target=worker)
            threads.append(thread)
            thread.setDaemon(True)
            thread.start()

        for thread in threads:
            thread.join()

        self._log.debug(', '.join([line for line in found_typos]))

        list_of_typos = list(found_typos)
        list_of_typos.sort()

        return list_of_typos
