# -*- coding: utf-8 -*-

"""
The Database connection.
"""

import threading

import pymysql

from additional import Config

################################################################################

class Database:
    """
    This class handles the connection to the database and executes queries.
    """

    def __init__(self):
        """
        Connects to Database with parameters from the configuration file.
        """

        self._lock = threading.Lock()
        self._connection = pymysql.connect(**Config.database_connection)

    ############################################################################

    def close_connection(self):
        """
        Method to close the database connection.
        """

        self._connection.close()

    ############################################################################

    def create_table(self, create_query):
        """
        Method to create a table in the database by the given query.

        @param create_query: the query to create the table
        """

        with self._lock:

            cursor = self._connection.cursor()
            cursor.execute(create_query)
            cursor.close()
            self._connection.commit()

    ############################################################################

    def insert_data(self, insert_query, insert_values=None):
        """
        Method to insert data into the database by the given query and values.

        @param insert_query:  the query to insert an entry
        @param insert_values: the values for the query

        @return: last row id
        """

        with self._lock:

            cursor = self._connection.cursor()

            if insert_values:
                cursor.execute(insert_query, insert_values)

            else:
                cursor.execute(insert_query)

            last_row_id = cursor.lastrowid

            cursor.close()
            self._connection.commit()

            return last_row_id

    ############################################################################

    def select_data(self, select_query, select_values=None):
        """
        Method to select data from the database by the given query.

        @param select_query:  the query to select entries
        @param select_values: the values for the query

        @return: the selected entries
        """

        with self._lock:

            cursor = self._connection.cursor()

            if select_values:
                cursor.execute(select_query, select_values)

            else:
                cursor.execute(select_query)

            result = []

            for line in cursor.fetchall():
                result.append(line)

            cursor.close()
            self._connection.commit()

            return result
