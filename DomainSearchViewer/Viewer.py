#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
The Viewer component of the DomainSearch application.
"""

import sys
import argparse
from datetime import datetime

import pymysql

from additional import Config
from additional.DBReader import DBReader
from additional.Logging import Logging
from additional.Scheduler import SubClassError
from additional.Scheduler import VersionError

################################################################################

def parse_args():
    """
    Creates the help menu and the command line options.
    """

    parser = argparse.ArgumentParser(
        description = '''
            Tool to get informations about domains from the database.''')

    parser.add_argument('domain',
        help = 'the domain to search for')

    parser.add_argument('-f', '--from_date',
        help = 'returns only informations from requests since the given datetime')

    parser.add_argument('-t', '--to_date',
        help = 'returns only informations from requests until the given datetime')

    parser.add_argument('-l', '--limit',
        help = 'returns omly informations from the newest request',
        action = 'store_true')

    parser.add_argument('-s', '--state',
        choices=['queued, scanned, permitted, denied'],
        help = 'returns only informations from requests in the given state')

    parser.add_argument('-i', '--info',
        help = 'returns only the header information about the search',
        action = 'store_true')

    return parser.parse_args()

################################################################################

def dateformat(date):
    """
    Tries to parse a string into a datetime object.
    Raises a ValueError if the format doesn't fit.

    @param date: the date to parse

    @result: parsed date
    """

    formats = {
        '%Y-%m-%d',
        '%d-%m-%Y',
        '%Y-%m-%d %H:%M',
        '%d-%m-%Y %H:%M',
        '%Y-%m-%d %H:%M:%S',
        '%d-%m-%Y %H:%M:%S'
    }

    for entry in formats.copy():

        formats.add(entry.replace('-', '.'))
        formats.add(entry.replace('-', '/'))

    for entry in formats:

        try:
            return datetime.strptime(date, entry)

        except ValueError:
            pass

    raise ValueError("'{}' is not a valid date/time".format(date))

################################################################################

def format_result(result, info):
    """
    Formats the given resultset.

    @param result: the result to format.
    @param info:   return only the header information.
    """

    if info:

        return '\n'.join([
            'Domain: ' + str(result.domain),
            'Request ID: ' + str(result.request_id),
            'State: ' + str(result.state),
            'Comment: ' + str(result.comment),
            'Created: ' + str(result.created)])

    else:
        return str(result)

################################################################################

def search(domain, from_date=datetime.min, to_date=datetime.max,
    info=False, limit=False, state=None):
    """
    Performs a search in the database and returns the formatted result

    @param domain:    the domain to lookup
    @param from_date: returns only requests since the given datetime
    @param to_date:   returns only requests until the given datetime
    @param state:     returns only requests in the given state
    @param limit:     returns only the newest request
    @param info:      returns only the header information about the search
    """

    try:
        reader = DBReader()

    except (VersionError, SubClassError) as e:

        if Config.debug_mode:
            raise

        log.error(e)

        return

    infos = reader.get_informations(
        domain, from_date, to_date, limit, state)

    if not infos:
        return

    result = ', '.join([str(format_result(res, info)) for res in infos])

    return result

################################################################################

def validate_configuration():
    """
    Method to validate the configuration file.
    """

    for var in [value for key, value in \
        Config.__dict__.items() if not key.startswith('__')]:

        if not isinstance(var, (int, float, str, tuple, list, set, dict)):

            log.error('Configurtion error! Please check configuration file')
            sys.exit(1)

################################################################################
################################################################################

if __name__ == '__main__':

    print('''\
  ____                        _         ____                      _
 |  _ \\  ___  _ __ ___   __ _(_)_ __   / ___|  ___  __ _ _ __ ___| |__
 | | | |/ _ \\| '_ ` _ \\ / _` | | '_ \\  \\___ \\ / _ \\/ _` | '__/ __| '_ \\
 | |_| | (_) | | | | | | (_| | | | | |  ___) |  __/ (_| | | | (__| | | |
 |____/ \\___/|_| |_| |_|\\__,_|_|_| |_| |____/ \\___|\\__,_|_|  \\___|_| |_|
 __     ___                          _   _   ___
 \\ \\   / (_) _____      _____ _ __  / | / | / _ \\
  \\ \\ / /| |/ _ \\ \\ /\\ / / _ \\ '__| | | | || | | |
   \\ V / | |  __/\\ V  V /  __/ |    | |_| || |_| |
    \\_/  |_|\\___| \\_/\\_/ \\___|_|    |_(_)_(_)___/
''')

    ############################################################################

    log = Logging('DomainSearchViewer').get_logger()

    ############################################################################

    # validates the configuration file
    validate_configuration()

    ############################################################################

    args = parse_args()

    log.debug('Parsed arguments: {}'.format(args))

    ############################################################################

    try:

        if args.from_date:
            from_date = dateformat(args.from_date)

        else:
            from_date = datetime.min

        if args.to_date:
            to_date = dateformat(args.to_date)

        else:
            to_date = datetime.max

    except ValueError:

        log.error('Invalid date format\r\n' +  \
            ' You can use one of following:\r\n' + \
            ' Y-m-d'+ ' | d-m-Y' + ' | Y-m-d H:M' + ' | d-m-Y H:M' + \
            ' | Y-m-d H:M:S' + ' | d-m-Y H:M:S\r\n' + \
            ' Y.m.d'+ ' | d.m.Y' + ' | Y.m.d H:M' + ' | d.m.Y H:M' + \
            ' | Y.m.d H:M:S' + ' | d.m.Y H:M:S\r\n' + \
            ' Y/m/d'+ ' | d/m/Y' + ' | Y/m/d H:M' + ' | d/m/Y H:M' + \
            ' | Y/m/d H:M:S' + ' | d/m/Y H:M:S')

        sys.exit(1)

    ############################################################################

    try:

        results = search(args.domain, from_date, to_date, args.info, args.limit,
            args.state)

    except pymysql.err.DatabaseError as error:

        log.error('Database not initialised')
        log.debug(error)

        sys.exit(1)

    if not results:
        log.info('No informations available')

    else:
        print(results)
