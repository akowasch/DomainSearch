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

# address and port of the rating-request server
# use empty string as host to listen on all interfaces
rating_request_server = {
    'host': '',
    'port': 8010
}

# address and port of the queued-domain-request server
# use empty string as host to listen on all interfaces
queued_domain_request_server = {
    'host': '',
    'port': 8020
}

# address and port of the task-notification server
# use empty string as host to listen on all interfaces
task_notification_server = {
    'host': '',
    'port': 8030
}

# address and port of the scanned-domain-request server
# use empty string as host to listen on all interfaces
scanned_domain_request_server = {
    'host': '',
    'port': 8040
}

# time until a domain entry expires in the database
domain_expiration_time = 1 # day(s)

# time until a request entry expires in the database
request_expiration_time = 1 # day(s)

# timeout to get task from blocked queue
queued_domain_request_server_timeout = 1 # second(s)

# path to the queued-domain-requests backup
queued_domain_requests_backup_path = 'resources/queued_domain_requests_backup'

# timeout to get task from blocked queue
scanned_domain_request_server_timeout = 1 # second(s)

# path to the scanned-domain-requests backup
scanned_domain_requests_backup_path = 'resources/scanned_domain_requests_backup'

# path to the running file
running_path = 'resources/running'