# -*- coding: utf-8 -*-

"""
Module to check Web of Trust rating.
"""

"""
################################################################################
# Components
################################################################################

0               Trustworthiness     “How much do you trust this site?”
4               Child safety        “How suitable is this site for children?”

################################################################################
# Reputation values
################################################################################

≥ 80            Excellent
≥ 60            Good
≥ 40            Unsatisfactory
≥ 20            Poor
≥ 0             Very poor

################################################################################
# Categories
################################################################################

Negative        101    Malware or viruses
                102    Poor customer experience
                103    Phishing
                104    Scam
                105    Potentially illegal
Questionable    201    Misleading claims or unethical
                202    Privacy risks
                203    Suspicious
                204    Hate, discrimination
                205    Spam
                206    Potentially unwanted programs
                207    Ads / pop-ups
Neutral         301    Online tracking
                302    Alternative or controversial medicine
                303    Opinions, religion, politics
                304    Other
Positive        501    Good site

################################################################################
# Child safety Categories
################################################################################

Negative        401    Adult content
Questionable    402    Incidental nudity
                403    Gruesome or shocking
Positive        404    Site for kids

################################################################################
# Blacklists
################################################################################

malware         Site is blacklisted for hosting malware
phishing        Site is blacklisted for hosting a phishing page
scam            Site is blacklisted for hosting a scam (e.g. a rogue pharmacy)
spam            Site is blacklisted for sending spam or being advertised in spam
"""

import requests

from modules import DatasourceBase
from modules import ModuleError

################################################################################

class WOT(DatasourceBase):
    """
    """

    # version of the module
    _version = 2015012401

    # dependencies of the module
    _dependencies = set()

    # database query strings of the module.
    _queries = {
        'create' : '''
            CREATE TABLE IF NOT EXISTS module_WOT (
                id INT AUTO_INCREMENT NOT NULL,
                request_id INT NOT NULL,
                trustworthiness VARCHAR(9),
                child_safety VARCHAR(9),
                categories VARCHAR(255),
                blacklists VARCHAR(255),
                PRIMARY KEY (id),
                FOREIGN KEY (request_id) REFERENCES requests(id)
            )''',

        'insert' : '''
            INSERT INTO module_WOT (
                request_id, trustworthiness, child_safety, categories, blacklists
            )
            VALUES (%s, %s, %s, %s, %s)''',

        'select' : '''
            SELECT *
            FROM module_WOT
            WHERE request_id = %s'''
    }

    ############################################################################

    def __init__(self):
        super(WOT, self).__init__()

    ############################################################################

    def _search(self, request_id, domain, counter):
        """
        Inherited method to start the search. The result will be entered in the
        database.
        """

        url = "http://api.mywot.com/0.4/public_link_json2"

        payload = {
            'hosts': domain + '/',
            'key': self._get_module_config('api_key')}

        try:
            response = requests.get(url, params=payload)

        except requests.exceptions.ConnectionError:
            raise ModuleError(True)

        self._log.debug('Status code: {}'.format(response.status_code))

        response = response.json()[domain]

        self._log.debug(response)

        self._db.insert_data(
            self._queries['insert'], (
                request_id,
                str(response['0']) if '0' in response else '',
                str(response['4']) if '4' in response else '',
                str(response['categories']) if \
                    'categories' in response else '',
                str(response['blacklists']) if \
                    'blacklists' in response else ''))
