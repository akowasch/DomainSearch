# -*- coding: utf-8 -*-

"""
The scheduler is responsible for the module handling.
"""

import modules
from importlib import import_module

from additional.Logging import Logging

################################################################################

class Scheduler():
    """
    This class instantiates the modules, takes care of the module's versions
    and gets the module's select queries.
    """

    # dictonary of instantiated modules
    _instantiated_modules = {}

    def __init__(self, db):

        self._db = db
        self._log = Logging(self.__class__.__name__).get_logger()

        ########################################################################

        self._instantiate_modules()
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

    def get_module_select_queries(self):
        """
        Returns the module's search queries.
        """

        queries = {}

        for module_name, module in self._instantiated_modules.items():
            queries[module_name] = module.get_queries('select')

        return queries

################################################################################

class SubClassError(Exception):
    """
    Exception for module subclass errors.
    """

class VersionError(Exception):
    """
    Exception for module version errors.
    """
