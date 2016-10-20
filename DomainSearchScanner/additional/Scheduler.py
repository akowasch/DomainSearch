# -*- coding: utf-8 -*-

"""
The scheduler is responsible for the module handling.
"""

"""
################################################################################

Messages:

    Scanner -> TaskNotificationServer:

        "notification": {
            "scan": {
                "domain": "example.com",
                "request_id": 1
            }
        }

################################################################################

Queue structur:

    rerun_queue = (request_id, domain, counter, rerun_modules, date_time)

        request_id = int
        domain = str
        counter = int
        rerun_modules = [module, ...]

            module = str

        date_time = datetime

################################################################################
"""

import time
import json
import socket
import threading
from datetime import datetime
from importlib import import_module

import modules
from additional import Config
from additional.Logging import Logging

################################################################################

class Scheduler():
    """
    This class instantiates the modules, creates the module's database schema,
    takes care of the module's dependencies and versions and runs the modules.
    """

    # dictonary of instantiated modules
    _instantiated_modules = {}

    def __init__(self, db, rerun_queue):

        self._db = db

        self._lock = threading.Lock()
        self._rerun_queue = rerun_queue
        self._log = Logging(self.__class__.__name__).get_logger()

        ########################################################################

        self._instantiate_modules()
        self._create_module_tables()
        self._check_module_dependencies()
        self._check_module_versions()

    ############################################################################

    def _instantiate_modules(self):
        """
        Method to instantiate modules.
        All modules must contain a class with the exact same name as the module.
        This class must implement the abstract base class (abc) DatasourceBase.
        """

        # finds all modules to import
        for module_name in modules.__all__:

            # drops 'unwanted' modules
            if module_name in Config.norun:

                self._log.info('Module will not be executed: {}'
                    .format(module_name))

                continue

            # imports an instantiates the module by name
            module = import_module('modules.' + module_name)
            module = getattr(module, module_name)()

            # makes sure the module implements DatasourceBase
            if not isinstance(module, modules.DatasourceBase):

                raise SubClassError(
                    'Modul is not an instance of DatasourceBase: {}'
                    .format(module.__class__.__name__))

            # adds the module to the list of instantieated modules
            self._instantiated_modules[module.__class__.__name__] = module

    ############################################################################

    def is_module_instantiated(self, module):
        """
        Method to check if a given module is instantiated.

        @param module: the module to check

        @return: True if module is instantiated, False otherwise
        """

        return module in self._instantiated_modules

    ############################################################################

    def _create_module_tables(self):
        """
        Method to create the module's database schema.
        """

        for module in self._instantiated_modules.values():

            query = module.get_queries('create')

            errors = 0

            try:

                if isinstance(query, list):

                    for qry in query:
                        self._db.create_table(qry)

                else:
                    self._db.create_table(query)

            except DatabaseError:
                errors += 1

            if errors:
                raise DatabaseError('Creation of database tables failed')

    ############################################################################

    def _check_module_dependencies(self):
        """
        Method to check modules for circular dependencies.
        """

        for name, module in self._instantiated_modules.items():

            dependency_set = set(name)
            self._get_module_dependencies(module, dependency_set)

    def _get_module_dependencies(self, module, dependency_set):
        """
        Method to get module's dependencies.
        This method calls itself recursifely to find all dependencies.

        @param module:         the module to get the dependencies
        @param dependency_set: a set of already found dependencies
        """

        # gets module's dependencies
        for mod in module.get_dependencies():

            if mod not in self._instantiated_modules:

                if mod in Config.norun:

                    raise DependencyError(
                        'Excluded module dependency detected: {} -> {}'
                        .format(module.__class__.__name__, mod))

                else:

                    raise DependencyError(
                        'Unknown module dependency detected: {} -> {}'
                        .format(module.__class__.__name__, mod))

            if mod in dependency_set:
                raise DependencyError('Circular modul dependency detected')

            dependency_set.add(mod)

            self._get_module_dependencies(
                self._instantiated_modules[mod], dependency_set)

    ############################################################################

    def _check_module_versions(self):
        """
        Method to check module's versions.
        """

        for module_name, module in self._instantiated_modules.items():

            module_version = module.get_version()

            # searches module's version in the database
            result = self._db.select_data('''
                SELECT version
                FROM versions
                WHERE module = %s''', (module_name,))

            if not result:

                # appends the module with it's version to the database
                self._db.insert_data('''
                    INSERT INTO versions (module, version)
                    VALUES (%s, %s)''', (module_name, module_version))

            elif result[0][0] < module_version:

                # updates the request entry
                self.server.db.update_data('''
                    UPDATE versions
                    SET version = %s
                    WHERE module = %s''', (module_version, module_name,))

            elif result[0][0] > module_version:

                raise VersionError('Old module version detected!' +
                    'Module: {} - Expected: {} - Found: {}'
                    .format(module_name, result[0][0], module_version))

    ############################################################################

    def start_modules(self, request_id, domain, counter=0, rerun_modules=None):
        """
        Method to start modules in separate threads.
        If one module has a dependency to another module,
        the execution will be delayed until the needed module has finished.
        So the order of execution is given by the dependencies.

        @param request_id:    the request id of the current request
        @param domain:        the domain to scan
        @param counter:       count the number of runs for this request
        @param rerun_modules: a list of modules that should rerun
        """

        self._lock.acquire()

        start = time.time()

        self._log.info(
            'Search started    - Request ID: {} - Domain: {} - Counter: {}'
            .format(request_id, domain, counter))

        ########################################################################

        condition_variable = threading.Condition()
        threads = []

        # a set of completed modules
        modules_done = set()

        # a set of failed modules that should rerun
        modules_failed_rerun = set()

        # a set of failed modules to notify dependent modules
        modules_failed_notify = set()

        # a set of ignored modules, as of dependencies failed
        modules_dependency_failed = set()

        ########################################################################

        class Worker(threading.Thread):
            """
            Class for running modules in their own thread.
            """

            def __init__(self, module, counter):

                threading.Thread.__init__(self)
                self._module = module
                self._module_name = module.__class__.__name__
                self._counter = counter

            ####################################################################

            def run(self):
                """
                Method to do the search for the given module.
                """

                try:

                    self._module.run(request_id, domain, counter)

                    with condition_variable:

                        modules_done.add(self._module_name)
                        condition_variable.notify()

                except modules.ModuleError as error:

                    with condition_variable:

                        if error.rerun_flag:
                            modules_failed_rerun.add(self._module_name)

                        else:
                            modules_failed_notify.add(self._module_name)

                        condition_variable.notify()

                except Exception:

                    with condition_variable:

                        modules_failed_notify.add(self._module_name)
                        condition_variable.notify()

        ########################################################################

        # checks if the scheduler was invoked with a list of modules to rerun

        if rerun_modules:

            instantiated_modules = \
                [self._instantiated_modules[m] for m in rerun_modules]

        else:
            instantiated_modules = list(self._instantiated_modules.values())

        ########################################################################

        # as long as there are modules in instantiated_modules, start them if
        # their dependencies match the list with already finished modules

        with condition_variable:

            while instantiated_modules:

                for module in instantiated_modules:

                    # checks if the module's dependencies have already been
                    # executed
                    if module.get_dependencies().issubset(modules_done):

                        instantiated_modules.remove(module)
                        thread = Worker(module, counter)
                        thread.start()
                        threads.append(thread)

                    # checks if the module depends on failed modules;
                    # modules will not rerun
                    elif module.get_dependencies() & modules_failed_notify or \
                        module.get_dependencies() & modules_dependency_failed:

                        instantiated_modules.remove(module)
                        modules_dependency_failed.add(module.__class__.__name__)

                    # checks if the module depends on failed modules;
                    # modules will rerun
                    elif module.get_dependencies() & modules_failed_rerun:

                        instantiated_modules.remove(module)
                        modules_failed_rerun.add(module.__class__.__name__)

                condition_variable.wait()

        ########################################################################

        # waits until all started modules are finished

        for thread in threads:
            thread.join()

        ########################################################################

        # checks if modules in modules_failed_rerun are in the correct list

        has_changed = True

        while has_changed:

            has_changed = False

            for module in modules_failed_rerun:

                deps = self._instantiated_modules[module].get_dependencies()

                if deps & modules_failed_notify or \
                    deps & modules_dependency_failed:

                    modules_failed_rerun.remove(module)
                    modules_dependency_failed.add(module)

                    has_changed = True

        ########################################################################

        # checks if errors have occured during the process (ignored)

        if modules_dependency_failed:

            # writes modules depending on finally failed modules to error
            # table in database

            self._log.error('Modules depending on finally failed module: {}'
                .format(modules_dependency_failed))

            for module in modules_dependency_failed:

                self._report_module_error(request_id, module,
                    'Module depends on finally failed module')

        # checks if errors have occured during the process

        if modules_failed_rerun:

            # adds failed modules and modules depending on them to the rerun
            # queue

            self._log.info('Modules queued to rerun: {}'
                .format(modules_failed_rerun))

            now = datetime.now()

            self._rerun_queue.put(
                (request_id, domain, counter + 1, modules_failed_rerun, now))

            self._lock.release()

            return

        # notifies the task-notification server about the finished task

        task_notification_server = (
            Config.task_notification_server['host'],
            Config.task_notification_server['port'])

        with socket.create_connection(task_notification_server) as sock:

            sock.sendall(bytes(json.dumps({
                'notification': {
                    'scan': {
                        'domain': domain,
                        'request_id': request_id
                    }
                }
            }), 'UTF-8'))

        ####################################################################

        end = time.time()

        self._log.info(
            'Search finished   - ' + \
            'Request ID: {} - Domain: {} - Counter: {} - Time: {:.2f}s'
            .format(request_id, domain, counter, end - start))

        self._lock.release()

    ############################################################################

    def _report_module_error(self, request_id, module, msg):
        """
        Method to finaly report an error in database.

        @param request_id: the request id of the current request
        @param module:     the module that reports the error
        @param msg:        the message to report
        """

        query = """
            INSERT INTO errors (request_id, module, comment)
            VALUES(%s, %s, %s)
            """

        self._db.insert_data(query, (request_id, module, msg))

################################################################################

class DatabaseError(Exception):
    """
    Exception for database errors.
    """

class SubClassError(Exception):
    """
    Exception for module subclass errors.
    """

class DependencyError(Exception):
    """
    Exception for module dependencie errors.
    """

class VersionError(Exception):
    """
    Exception for module version errors.
    """
