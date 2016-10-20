# -*- coding: utf-8 -*-

"""
Module for Lexical Analysis of the domain name.
"""

import enchant

from modules import DatasourceBase

################################################################################

class SpellChecker(DatasourceBase):
    """
    This Module uses PyEnchant to check if substrings of the domain name are in
    a Dictionary. It also calculates the percentage of numerical characters in
    the name.
    """

    # version of the module
    _version = 2015012401

    # dependencies of the module
    _dependencies = set()

    # database query strings of the module
    _queries = {
        'create' : ['''
            CREATE TABLE IF NOT EXISTS module_SpellChecker (
                id INT AUTO_INCREMENT NOT NULL,
                request_id INT NOT NULL,
                length INT(32) NOT NULL,
                nr_percentage INT(32) NOT NULL,
                PRIMARY KEY (id),
                FOREIGN KEY (request_id) REFERENCES requests(id)
            )''',
            '''
            CREATE TABLE IF NOT EXISTS module_SpellCheckerMatches (
                id INT AUTO_INCREMENT NOT NULL,
                lex_id INT NOT NULL,
                matching VARCHAR(255) NOT NULL,
                language VARCHAR(5) NOT NULL,
                PRIMARY KEY (id),
                FOREIGN KEY (lex_id) REFERENCES module_SpellChecker(id)
            )'''],

        'insert' : ['''
            INSERT INTO module_SpellChecker (
                request_id, length, nr_percentage
            )
            VALUES (%s, %s, %s)''',
            '''
            INSERT INTO module_SpellCheckerMatches (
                lex_id, matching, language
            )
            VALUES (%s, %s, %s)'''],

        'select' : '''
            SELECT
                id,
                request_id,
                domain,
                CONCAT_WS(' ', 'Len:', length),
                CONCAT_WS(' ', 'Num:', nr_percentage, '%%' ),
                (
                    SELECT
                        GROUP_CONCAT(
                            matching, ' ', language
                            ORDER BY language
                            SEPARATOR ', '
                        )
                    FROM module_SpellCheckerMatches
                    WHERE module_SpellChecker.id = module_SpellCheckerMatches.lex_id
                )
            FROM module_SpellChecker
            WHERE request_id = %s'''
    }

    ############################################################################

    def __init__(self):
        super(SpellChecker, self).__init__()

    ############################################################################

    def _search(self, request_id, domain, counter):
        """
        Inherited method to start the search. The result will be entered in the
        database.
        """

        numbers = self._calculate_numerical_chars(domain)
        words = self._check_dict(domain)

        last_row_id = self._db.insert_data(
            self._queries['insert'][0],
            (request_id, numbers[0], numbers[1])
        )

        for line in words:

            self._db.insert_data(
                self._queries['insert'][1],
                (last_row_id, line[0], line[1])
            )

    ############################################################################

    def _calculate_numerical_chars(self, domain):
        """
        Calculates the percentage of numerical characters in the domain name.
        """

        domain = domain.replace('.', '')
        length = len(domain)
        number_count = 0

        for char in domain:

            if char.isdigit():
                number_count += 1

        try:
            percentage = float('%.1f' % (number_count / length * 100))

        except ZeroDivisionError:
            percentage = 0.0

        self._log.debug(" ".join(
            [str(length), str(number_count), str(percentage)]))

        return (length, percentage)

    ############################################################################

    def _check_dict(self, domain):
        """
        Checks if substrings of the domnain name match a dictionary.
        """

        matches = set()
        domain = domain.replace('.', '')
        substrings = self._get_substrings(
            domain, self._get_module_config('word_length')
        )

        for sub in substrings[:]:
            substrings.append(sub[0].upper() + sub[1:])

        self._log.debug(substrings)

        # check every substring in every language
        for lang in self._get_module_config('dicts'):
            checker = enchant.Dict(lang)
            for word in substrings:
                if checker.check(word):
                    matches.add((word.lower(), lang))

        self._log.debug(matches)

        return matches

    ############################################################################

    def _get_substrings(self, string, length):
        """
        Separates the given string into all substrings with the given length.
        """

        substrings = []

        string_tuple = tuple(string)

        for size in range(length, len(string_tuple) + 1):

            for index in range(len(string_tuple) + 1 - size):
                substrings.append(string[index:index + size])

        return substrings
