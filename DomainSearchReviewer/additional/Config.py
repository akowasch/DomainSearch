# -*- coding: utf-8 -*-

"""
Configuration file.
"""

# enables the debug mode of the client
# True:  Exceptions will be raised
# False: Exceptions will be catched and logged
debug_mode = True

# parameter for database connection
database_connection = {
    'user': 'root',
    'passwd': 'Se!Ne#Ta45',
    'host': 'localhost',
    'db': 'domainSearch',
    'charset': 'utf8'
}

# server to get domains to review
scanned_domain_request_server = {
    'host': 'localhost',
    'port': 8040
}

# path to the running file
running_path = 'resources/running'

# path to the backup file
backup_path = 'resources/backup'