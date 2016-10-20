# -*- coding: utf-8 -*-

"""
Collects Information about open ports on the given Domain.
"""

import nmap

from modules import DatasourceBase

################################################################################

class Nmap(DatasourceBase):
    """
    Simple Version without parsing of the content.
    """

    # version of the module
    _version = 2015012401

    # dependencies of the module
    _dependencies = set()

    # database query strings of the module
    _queries = {
        'create' : '''
            CREATE TABLE IF NOT EXISTS module_Nmap (
                id INT AUTO_INCREMENT NOT NULL,
                request_id INT NOT NULL,
                ip_address VARCHAR(15) NOT NULL,
                port INT(5) NOT NULL,
                protocol VARCHAR(3) NOT NULL,
                name VARCHAR(255),
                state VARCHAR(255),
                reason VARCHAR(255),
                product VARCHAR(255),
                version VARCHAR(255),
                conf INT,
                cpe VARCHAR(255),
                extra_info VARCHAR(255),
                PRIMARY KEY (id),
                FOREIGN KEY (request_id) REFERENCES requests(id)
            )''',

        'insert' : '''
            INSERT INTO module_Nmap (
                request_id, ip_address, port, protocol, name, state, reason,
                product, version, conf, cpe, extra_info
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)''',

        'select' : '''
            SELECT *
            FROM module_Nmap
            WHERE request_id = %s'''
    }

    ############################################################################

    def __init__(self):
        super(Nmap, self).__init__()

    ############################################################################

    def _search(self, request_id, domain, counter):
        """
        Inherited method to start the search. The result will be entered in the
        database.
        """

        nm = nmap.PortScanner()
        nm.scan(domain, self._get_module_config('port_range'))

        for host in nm.all_hosts():

            for protocol in nm[host].all_protocols():

                if protocol not in ['tcp', 'udp']:
                    continue

                for port in nm[host][protocol].keys():

                    self._db.insert_data(
                        self._queries['insert'], (
                            request_id, host, port, protocol,
                            nm[host][protocol][port]['name'],
                            nm[host][protocol][port]['state'],
                            nm[host][protocol][port]['reason'],
                            nm[host][protocol][port]['product'],
                            nm[host][protocol][port]['version'],
                            int(nm[host][protocol][port]['conf']),
                            nm[host][protocol][port]['cpe'],
                            nm[host][protocol][port]['extrainfo']
                        )
                    )
