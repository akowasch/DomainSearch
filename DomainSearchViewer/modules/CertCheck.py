#!/usr/bin/env python3

"""
Module to get informations from domain's certificate.
"""

from modules import DatasourceBase

################################################################################

class CertCheck(DatasourceBase):
    """
    """

    # version of the module
    _version = 2015012401

    # dependencies of the module
    _dependencies = set()

    # database query strings of the module
    _queries = {
        'create' : '''
            CREATE TABLE IF NOT EXISTS module_CertCheck (
                id INT AUTO_INCREMENT NOT NULL,
                request_id INT NOT NULL,
                PRIMARY KEY (id),
                FOREIGN KEY (request_id) REFERENCES requests(id)
            )''',

        'insert' : '''
            ''',

        'select' : '''
            SELECT *
            FROM module_CertCheck
            WHERE request_id = %s'''
    }

    ############################################################################

    def __init__(self):
        super(CertCheck, self).__init__()

    ############################################################################

    def _search(self, request_id, domain, counter):
        """
        Inherited method to start the search. The result will be entered in the
        database.
        """

        pass
