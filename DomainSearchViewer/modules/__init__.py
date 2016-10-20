# -*- coding: utf-8 -*-

"""
Abstract module class.
"""

import os
import abc
import glob
import time
import socket

################################################################################

# list of strings defining what symbols will be exported

MODULES = glob.glob(os.path.dirname(__file__) + "/*.py")
__all__ = [os.path.basename(f)[:-3] for f in MODULES]
__all__.remove('__init__')

################################################################################

class DatasourceBase(metaclass=abc.ABCMeta):
    """
    Abstract module class.
    """

    from additional import Config
    from additional.Logging import Logging
    from additional.Database import Database

    _version = None
    _dependencies = set()
    _queries = dict()

    ############################################################################

    @abc.abstractmethod
    def __init__(self):

        self._db = self.Database()
        self._log = self.Logging(self.__class__.__name__).get_logger()

    ############################################################################

    @abc.abstractmethod
    def _search(self, request_id, domain, counter):
        """
        Abstract method to collect module's informations and insert the result
        into database. Method will be executed when the module is loaded by the
        main program. All modules must implement this class.

        @param request_id: the request id of the current request
        @param domain:     the domain to scan
        @param counter:    count the number of runs for this request
        """

    ############################################################################

    def run(self, request_id, domain, counter):
        """
        Method called from the scheduler to run the actual module.

        @param request_id: the request id of the current request
        @param domain:     the domain to scan
        @param counter:    count the number of runs for this request
        """

        # validates parameter structure

        if not(
            isinstance(request_id, int) and \
            isinstance(domain, str) and \
            isinstance(counter, int)):

            self._log.error(
                'Bad Parameters - Request ID: {} - Domain: {} - Counter: {}'
                .format(request_id, domain, counter))

            raise ModuleError

        ########################################################################

        start = time.time()

        self._log.info(
            'Module started    - Request ID: {} - Domain: {}'
            .format(request_id, domain))

        ########################################################################

        try :

            # Collects modules information and inserts the result into database.
            self._search(request_id, domain, counter)

        except ModuleError as err:

            end = time.time()

            if err.rerun_flag:

                if counter > self.Config.rerun_counter_max:

                    # finally terminates the module despite the desire of rerun

                    self._log.error(
                        'Module expired    - Request ID: {} - Domain: {}'
                        .format(request_id, domain))

                    self._report_module_error(request_id, 'Module expired')

                    raise ModuleError

                self._log.info(
                    'Module unfinished - ' + \
                    'Request ID: {} - Domain: {} - Time: {:.2f}s'
                    .format(request_id, domain, end - start))

                raise

            self._log.error(
                'Module failed     - ' + \
                'Request ID: {} - Domain: {} - Time: {:.2f}s'
                .format(request_id, domain, end - start))

            raise

        except Exception as err:

            end = time.time()

            self._log.error(
                'Module failed     - ' + \
                'Request ID: {} - Domain: {} - Time: {:.2f}s'
                .format(request_id, domain, end - start))

            self._log.debug(err)

            raise

        ########################################################################

        end = time.time()

        self._log.info(
            'Module finished   - Request ID: {} - Domain: {} - Time: {:.2f}s'
            .format(request_id, domain, end - start))

    ############################################################################

    def _get_module_config(self, key, module=None):
        """
        Method to return module's configuration.

        @param key:    the information to extract from config file
        @param module: the name of the module to get the information
        """

        if module:
            return self.Config.modules[module][key]

        return self.Config.modules[self.__class__.__name__][key]

    ############################################################################

    def get_dependencies(self):
        """
        Method to return module's dependencies.

        @return: the module's dependencies
        """

        return self._dependencies

    ############################################################################

    def get_queries(self, query_type=None):
        """
        Method to return the requested query.

        @param query_type: (create, insert, select)
        """
        if query_type:
            return self._queries[query_type]

        return self._queries

    ############################################################################

    def get_version(self):
        """
        Method to return module's version.

        @return: the module's version
        """

        return self._version

    ############################################################################

    def _report_module_error(self, request_id, msg):
        """
        Method to finaly report an error in database.

        @param request_id: the request_id of the current request
        @param msg:        the message to report
        """

        query = """
            INSERT INTO errors (request_id, module, comment)
            VALUES(%s, %s, %s)
            """

        self._db.insert_data(query, (request_id, self.__class__.__name__, msg))

    ############################################################################

    def _get_ip_addresses(self, domain):
        """
        Method to get ip adresses to a given domain.

        @param domain: the domain to get the ips

        @return: the ips of the domain
        """

        ip_addresses = set()

        address_info = socket.getaddrinfo(domain, None, family=socket.AF_INET,
            proto=socket.IPPROTO_TCP)

        for entry in address_info:
            ip_addresses.add(entry[4][0])

        return ip_addresses

################################################################################

class ModuleError(Exception):
    """
    Exception for module errors. If module should rerun set attribute to True.
    """

    def __init__(self, rerun_flag=False):
        self.rerun_flag = rerun_flag
