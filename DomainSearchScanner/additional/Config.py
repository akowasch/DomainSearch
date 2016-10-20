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

# server to get domains to scan
queued_domain_request_server = {
    'host': 'localhost',
    'port': 8020
}

# server to send finished tasks
task_notification_server = {
    'host': 'localhost',
    'port': 8030
}

# path to the running file
running_path = 'resources/running'

# path to the rerun-queue backup file
rerun_queue_backup_path = 'resources/rerun_queue_backup'

# set of modules that won't run
norun = {
    'MXToolbox',
    'Traceroute',
    'Nmap'
}

# time until a domain entry expires in the database
domain_expiration_time = 1 # day(s)

# time until a request entry expires in the database
request_expiration_time = 1 # day(s)

# time between checks to rerun qeue
rerun_queue_check_delay = 10 # seconds

# maximal number of reruns
rerun_counter_max = 10

# times until a request should rerun selected by it's counter.
# if the counter is larger then the number of times, the last
# time will be used
rerun_thresholds = [1, 5, 10, 30, 60] # minutes

modules = {

    'DNSResolver': {
        'nameserver': '8.8.8.8',
        'max_recursions': 5,
    },

    'GoogleSafeBrowsing': {
        'api_key': 'AIzaSyAr83uIJt3dh_CkUfJhI8-nD7u_29Uv7NE',
    },

    'Nmap': {
        'port_range': '1-1023'
    },

    'RobotsTxt': {
        'max_depth': 6, # iterations
    },

    'SpellChecker': {
        'word_length': 4,
        'dicts': [
            'en_US',
            'de_DE'
        ]
    },

    'Traceroute': {
        'port': 33434,
        'max_hops': 30,
        'timeout': 2 # seconds
    },

    'Typo': {
        'max_threads': 5,
        'common_tlds': [
            '.de',
            '.com'
        ],
        'common_mistakes': [
            ('s', 'z'),
            ('e', '3'),
            ('d', 't'),
            ('k', 'c'),
            ('w', 'v'),
            ('ph', 'f')
        ]
    },

    'WOT': {
        'api_key': '1d5964024446897edf8625416a2b68b127009e4a'
    },

    'VirusTotal': {
        'api_key': '060fc524023ee96a6a26ddfa9d75b362e839bc771acad8518462e4c82dc74421'
    }
}