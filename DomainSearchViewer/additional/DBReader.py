# -*- coding: utf-8 -*-

"""
The DBReader gets informations about previous search requests from the database.
"""

from datetime import datetime

from additional.Database import Database
from additional.Scheduler import Scheduler
import pymysql

################################################################################

class DSTable(list):
    """
    Represents one table in a DSRecord. Inherits list.
    """

    def __init__(self, name):

        super(DSTable, self).__init__()

        self.name = name

    ############################################################################

    def __str__(self):

        first_part = '\n'.join(['', '#' * 80, '# ' + self.name, '#' * 80, ''])
        second_part = '\n'.join([str(line) for line in self])

        return '\n'.join([first_part, second_part])

################################################################################

class DSRecord(list):
    """
    Represents one Domain Search Record.
    Inherits dict and contains all information about one specific search.
    """

    def __init__(self, domain, request_id, state, comment, created):

        super(DSRecord, self).__init__()

        self.domain = domain
        self.request_id = request_id
        self.state = state
        self.comment = comment
        self.created = created

    ############################################################################

    def __str__(self):

        first_part = '\n'.join([
            'Domain: ' + str(self.domain),
            'Request ID: ' + str(self.request_id),
            'State: ' + str(self.state),
            'Comment: ' + str(self.comment),
            'Created: ' + str(self.created)])

        second_part = '\n'.join([str(table) for table in self])

        return '\n'.join([first_part, second_part])

################################################################################

class DBReader():
    """
    This Class queries the Database about previous searche requests and returns
    a DSRecord or a list of records in most cases.
    """

    def __init__(self):

        self._db = Database()
        self._scheduler = Scheduler(self._db)

    ############################################################################

    def get_informations(self, domain, from_date=datetime.min,
        to_date=datetime.max, limit=False, state=None):
        """
        Gets all informations from the modules to the given domain.

        @param domain:    the domain to search for
        @param from_date: returns informations only from requests since the
                          given datetime
        @param to_date:   returns informations only from requests until the
                          given datetime
        @param state:     returns informations only from requests in the given
                          state
        @param limit:     returns informations only from the newest request

        @return: list of DSRecords
        """

        query = '''
            SELECT id
            FROM domains
            WHERE name = %s'''

        result = self._db.select_data(query, (domain,))

        ########################################################################

        if not result:
            return

        domain_id = result[0][0]

        query = 'SELECT * FROM requests' + \
            ' ' + 'WHERE domain_id = %s AND created >= %s AND created <= %s'

        parameters = (domain_id, from_date, to_date)

        if state:

            query += ' ' + 'AND state = %s'
            parameters = (domain_id, from_date, to_date, state)

        if limit:
            query += ' ' + 'ORDER BY id DESC LIMIT 1'

        result = self._db.select_data(query, parameters)

        ########################################################################

        records = []

        for line in result:

            request_id = line[0]
            record = DSRecord(domain, request_id, line[2], line[3], line[4])

            for module, query in \
                self._scheduler.get_module_select_queries().items():

                try:
                    results = self._db.select_data(query, (request_id,))

                except pymysql.err.DatabaseError:
                    continue

                table_entry = DSTable(module)

                for line in results:

                    data = ', '.join([str(item) for item in line[2:]])

                    table_entry.append(data)

                record.append(table_entry)

            records.append(record)

        return records
