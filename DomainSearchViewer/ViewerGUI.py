#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
The DomainSearchViewerGUI is a Graphical user interface (GUI) as a supplement to
the Viewer.
"""

import sys
import os

from PyQt5.Qt import QMainWindow, QSqlDatabase, QMessageBox, QLabel, QPixmap, \
    QTabWidget, Qt, QWidget, QSqlRelationalTableModel, QSqlTableModel, \
    QTableView, QLineEdit, QComboBox, QGroupBox, QPushButton, QVBoxLayout, \
    QGridLayout, QDateTimeEdit, QDateTime, QSqlQuery, QApplication, pyqtSlot

from additional import Config

class DomeinSearchViewerGUI(QMainWindow):
    """
    This class represents the main window of the gui.
    """

    def __init__(self, *args):

        QMainWindow.__init__(self, *args)

        self._create_connection()
        self._create_components()
        self._create_layout()
        self._create_style_sheet()

        self.setWindowTitle('DomainSearch')
        self.resize(1024, 768)

    ############################################################################

    def _create_connection(self):
        """
        Method to create the database connection.
        """

        db = QSqlDatabase.addDatabase('QMYSQL')
        db.setDatabaseName(Config.database_connection['db'])
        db.setUserName(Config.database_connection['user'])
        db.setPassword(Config.database_connection['passwd'])

        if not db.open():
            QMessageBox.critical(None, 'Database Error', db.lastError().text())
            sys.exit(1)

    ############################################################################

    def _create_components(self):
        """
        Method to create the components.
        """

        # Logo

        self.logo = QLabel()
        self.logo.setPixmap(QPixmap(os.getcwd() + '/resources/DomainSearch.png'))
        self.logo.setAlignment(Qt.AlignCenter)

        self.tab_widget = QTabWidget()

        ########################################################################
        # Tab: 'Domains'
        ########################################################################

        self.domains_tab = QWidget()

        ########################################################################

        self.domains_tab.model = QSqlRelationalTableModel()
        self.domains_tab.model.setEditStrategy(QSqlTableModel.OnFieldChange)

        ########################################################################

        self.domains_tab.table_view = QTableView()
        self.domains_tab.table_view.setAlternatingRowColors(True)
        self.domains_tab.table_view.setModel(self.domains_tab.model)
        self.domains_tab.table_view.verticalHeader().setVisible(False)

        ########################################################################

        self.domains_tab.domain_id = QLineEdit()
        self.domains_tab.domain_id_label = QLabel('&Domain ID')
        self.domains_tab.domain_id_label.setBuddy(self.domains_tab.domain_id)

        self.domains_tab.name = QLineEdit()
        self.domains_tab.name_label = QLabel('&Name')
        self.domains_tab.name_label.setBuddy(self.domains_tab.name)

        self.domains_tab.state = QComboBox()
        self.domains_tab.state_label = QLabel('&State')
        self.domains_tab.state_label.setBuddy(self.domains_tab.state)

        self.domains_tab.comment = QLineEdit()
        self.domains_tab.comment_label = QLabel('&Comment')
        self.domains_tab.comment_label.setBuddy(self.domains_tab.comment)

        self.domains_tab.updated_from = QDateTimeEdit(QDateTime.currentDateTime().addDays(-1))
        self.domains_tab.updated_from.setCalendarPopup(True)
        self.domains_tab.updated_from.setMaximumDateTime(QDateTime.currentDateTime())
        self.domains_tab.updated_from_label = QLabel('&Updated from')
        self.domains_tab.updated_from_label.setBuddy(self.domains_tab.updated_from)

        self.domains_tab.updated_to = QDateTimeEdit(QDateTime.currentDateTime())
        self.domains_tab.updated_to.setCalendarPopup(True)
        self.domains_tab.updated_to.setMaximumDateTime(QDateTime.currentDateTime())
        self.domains_tab.updated_to_label = QLabel('&Updated to')
        self.domains_tab.updated_to_label.setBuddy(self.domains_tab.updated_to)

        self.domains_tab.submit_button = QPushButton('Submit Query')
        self.domains_tab.clear_button = QPushButton('Clear Input')

        ########################################################################

        self.domains_tab.search_box = QGroupBox('Search')
        self.domains_tab.search_box.setObjectName('search_box')

        ########################################################################

        self.domains_tab.results_box = QGroupBox('Results')
        self.domains_tab.results_box.setObjectName('results_box')

        ########################################################################

        self.domains_tab.state.addItem('---')
        self.domains_tab.state.addItem('permitted')
        self.domains_tab.state.addItem('denied')

        self.domains_tab.domain_id.returnPressed.connect(self._domains_tab_changed)
        self.domains_tab.name.returnPressed.connect(self._domains_tab_changed)
        self.domains_tab.state.activated['QString'].connect(self._domains_tab_changed)
        self.domains_tab.state.currentIndexChanged['QString'].connect(self._domains_tab_changed)
        self.domains_tab.comment.returnPressed.connect(self._domains_tab_changed)
        self.domains_tab.updated_from.dateChanged.connect(self._domains_tab_changed)
        self.domains_tab.updated_to.dateChanged.connect(self._domains_tab_changed)

        self.domains_tab.submit_button.clicked.connect(self._domains_tab_changed)
        self.domains_tab.clear_button.clicked.connect(self._domains_tab_cleared)

        ########################################################################

        self.tab_widget.addTab(self.domains_tab, 'Domains')

        ########################################################################
        # Tab: 'Requests'
        ########################################################################

        self.requests_tab = QWidget()

        ########################################################################

        self.requests_tab.model = QSqlRelationalTableModel()
        self.requests_tab.model.setEditStrategy(QSqlTableModel.OnFieldChange)

        ########################################################################

        self.requests_tab.table_view = QTableView()
        self.requests_tab.table_view.setAlternatingRowColors(True)
        self.requests_tab.table_view.setModel(self.requests_tab.model)
        self.requests_tab.table_view.verticalHeader().setVisible(False)

        ########################################################################

        self.requests_tab.request_id = QLineEdit()
        self.requests_tab.request_id_label = QLabel('&Request ID')
        self.requests_tab.request_id_label.setBuddy(self.requests_tab.request_id)

        self.requests_tab.domain_id = QLineEdit()
        self.requests_tab.domain_id_label = QLabel('&Domain ID')
        self.requests_tab.domain_id_label.setBuddy(self.requests_tab.domain_id)

        self.requests_tab.state = QComboBox()
        self.requests_tab.state_label = QLabel('&State')
        self.requests_tab.state_label.setBuddy(self.requests_tab.state)

        self.requests_tab.comment = QLineEdit()
        self.requests_tab.comment_label = QLabel('&Comment')
        self.requests_tab.comment_label.setBuddy(self.requests_tab.comment)

        self.requests_tab.created_from = QDateTimeEdit(QDateTime.currentDateTime().addDays(-1))
        self.requests_tab.created_from.setCalendarPopup(True)
        self.requests_tab.created_from.setMaximumDateTime(QDateTime.currentDateTime())
        self.requests_tab.created_from_label = QLabel('&Created from')
        self.requests_tab.created_from_label.setBuddy(self.requests_tab.created_from)

        self.requests_tab.created_to = QDateTimeEdit(QDateTime.currentDateTime())
        self.requests_tab.created_to.setCalendarPopup(True)
        self.requests_tab.created_to.setMaximumDateTime(QDateTime.currentDateTime())
        self.requests_tab.created_to_label = QLabel('&Created to')
        self.requests_tab.created_to_label.setBuddy(self.requests_tab.created_to)

        self.requests_tab.submit_button = QPushButton('Submit Query')
        self.requests_tab.clear_button = QPushButton('Clear Input')

        ########################################################################

        self.requests_tab.search_box = QGroupBox('Search')
        self.requests_tab.search_box.setObjectName('search_box')

        ########################################################################

        self.requests_tab.results_box = QGroupBox('Results')
        self.requests_tab.results_box.setObjectName('results_box')

        ########################################################################

        self.requests_tab.state.addItem('---')
        self.requests_tab.state.addItem('queued')
        self.requests_tab.state.addItem('scanned')
        self.requests_tab.state.addItem('permitted')
        self.requests_tab.state.addItem('denied')

        self.requests_tab.request_id.returnPressed.connect(self._requests_tab_changed)
        self.requests_tab.domain_id.returnPressed.connect(self._requests_tab_changed)
        self.requests_tab.state.activated['QString'].connect(self._requests_tab_changed)
        self.requests_tab.state.currentIndexChanged['QString'].connect(self._requests_tab_changed)
        self.requests_tab.comment.returnPressed.connect(self._requests_tab_changed)
        self.requests_tab.created_from.dateChanged.connect(self._requests_tab_changed)
        self.requests_tab.created_to.dateChanged.connect(self._requests_tab_changed)

        self.requests_tab.submit_button.clicked.connect(self._requests_tab_changed)
        self.requests_tab.clear_button.clicked.connect(self._requests_tab_cleared)

        ########################################################################

        self.tab_widget.addTab(self.requests_tab, 'Requests')

        ########################################################################
        # Tab: 'Modules'
        ########################################################################

        self.modules_tab = QWidget()

        ########################################################################

        self.modules_tab.model = QSqlRelationalTableModel()
        self.modules_tab.model.setEditStrategy(QSqlTableModel.OnFieldChange)

        ########################################################################

        self.modules_tab.table_view = QTableView()
        self.modules_tab.table_view.setAlternatingRowColors(True)
        self.modules_tab.table_view.setModel(self.modules_tab.model)
        self.modules_tab.table_view.verticalHeader().setVisible(False)

        ########################################################################

        self.modules_tab.module = QComboBox()
        self.modules_tab.module_label = QLabel('&Module')
        self.modules_tab.module_label.setBuddy(self.modules_tab.module)

        self.modules_tab.module_id = QLineEdit()
        self.modules_tab.module_id_label = QLabel('&Module ID')
        self.modules_tab.module_id_label.setBuddy(self.modules_tab.module_id)

        self.modules_tab.request_id = QLineEdit()
        self.modules_tab.request_id_label = QLabel('&Request ID')
        self.modules_tab.request_id_label.setBuddy(self.modules_tab.request_id)

        self.modules_tab.submit_button = QPushButton('Submit Query')
        self.modules_tab.clear_button = QPushButton('Clear Input')

        ########################################################################

        self.modules_tab.search_box = QGroupBox('Search')
        self.modules_tab.search_box.setObjectName('search_box')

        ########################################################################

        self.modules_tab.results_box = QGroupBox('Results')
        self.modules_tab.results_box.setObjectName('results_box')

        ########################################################################

        self.modules_tab.module.addItem('---')
        self.modules_tab.module.addItem('ASN')
        self.modules_tab.module.addItem('CertCheck')
        self.modules_tab.module.addItem('DNSResolver')
        self.modules_tab.module.addItem('DomainAge')
        self.modules_tab.module.addItem('GeoIP')
        self.modules_tab.module.addItem('GooglePageRank')
        self.modules_tab.module.addItem('GoogleSafeBrowsing')
        self.modules_tab.module.addItem('GoogleSearch')
        self.modules_tab.module.addItem('IPVoid')
        self.modules_tab.module.addItem('MXToolbox')
        self.modules_tab.module.addItem('Nmap')
        self.modules_tab.module.addItem('RobotsTxt')
        self.modules_tab.module.addItem('SpellChecker')
        self.modules_tab.module.addItem('Traceroute')
        self.modules_tab.module.addItem('Typo')
        self.modules_tab.module.addItem('VirusTotal')
        self.modules_tab.module.addItem('Whois')
        self.modules_tab.module.addItem('WOT')

        self.modules_tab.module.activated['QString'].connect(self._modules_tab_changed)
        self.modules_tab.module.currentIndexChanged['QString'].connect(self._modules_tab_changed)
        self.modules_tab.module_id.returnPressed.connect(self._modules_tab_changed)
        self.modules_tab.request_id.returnPressed.connect(self._modules_tab_changed)

        self.modules_tab.submit_button.clicked.connect(self._modules_tab_changed)
        self.modules_tab.clear_button.clicked.connect(self._modules_tab_cleared)

        ########################################################################

        self.tab_widget.addTab(self.modules_tab, 'Modules')

        ########################################################################
        # Tab: 'Versions'
        ########################################################################

        self.versions_tab = QWidget()

        ########################################################################

        self.versions_tab.model = QSqlRelationalTableModel()
        self.versions_tab.model.setEditStrategy(QSqlTableModel.OnFieldChange)

        ########################################################################

        self.versions_tab.table_view = QTableView()
        self.versions_tab.table_view.setAlternatingRowColors(True)
        self.versions_tab.table_view.setModel(self.versions_tab.model)
        self.versions_tab.table_view.verticalHeader().setVisible(False)

        ########################################################################

        self.versions_tab.refresh_button = QPushButton('Show/Refresh List')

        ########################################################################

        self.versions_tab.search_box = QGroupBox('Search')
        self.versions_tab.search_box.setObjectName('search_box')

        ########################################################################

        self.versions_tab.results_box = QGroupBox('Results')
        self.versions_tab.results_box.setObjectName('results_box')

        ########################################################################

        self.versions_tab.refresh_button.clicked.connect(self._versions_tab_changed)

        ########################################################################

        self.tab_widget.addTab(self.versions_tab, 'Versions')

        ########################################################################
        # Tab: 'Errors'
        ########################################################################

        self.errors_tab = QWidget()

        ########################################################################

        self.errors_tab.model = QSqlRelationalTableModel()
        self.errors_tab.model.setEditStrategy(QSqlTableModel.OnFieldChange)

        ########################################################################

        self.errors_tab.table_view = QTableView()
        self.errors_tab.table_view.setAlternatingRowColors(True)
        self.errors_tab.table_view.setModel(self.errors_tab.model)
        self.errors_tab.table_view.verticalHeader().setVisible(False)

        ########################################################################

        self.errors_tab.error_id = QLineEdit()
        self.errors_tab.error_id_label = QLabel('&Error ID')
        self.errors_tab.error_id_label.setBuddy(self.errors_tab.error_id)

        self.errors_tab.request_id = QLineEdit()
        self.errors_tab.request_id_label = QLabel('&Request ID')
        self.errors_tab.request_id_label.setBuddy(self.errors_tab.request_id)

        self.errors_tab.module = QComboBox()
        self.errors_tab.module_label = QLabel('&Module')
        self.errors_tab.module_label.setBuddy(self.errors_tab.module)

        self.errors_tab.comment = QLineEdit()
        self.errors_tab.comment_label = QLabel('&Comment')
        self.errors_tab.comment_label.setBuddy(self.errors_tab.comment)

        self.errors_tab.created_from = QDateTimeEdit(QDateTime.currentDateTime().addDays(-1))
        self.errors_tab.created_from.setCalendarPopup(True)
        self.errors_tab.created_from.setMaximumDateTime(QDateTime.currentDateTime())
        self.errors_tab.created_from_label = QLabel('&Created from')
        self.errors_tab.created_from_label.setBuddy(self.errors_tab.created_from)

        self.errors_tab.created_to = QDateTimeEdit(QDateTime.currentDateTime())
        self.errors_tab.created_to.setCalendarPopup(True)
        self.errors_tab.created_to.setMaximumDateTime(QDateTime.currentDateTime())
        self.errors_tab.created_to_label = QLabel('&Created to')
        self.errors_tab.created_to_label.setBuddy(self.errors_tab.created_to)

        self.errors_tab.submit_button = QPushButton('Submit Query')
        self.errors_tab.clear_button = QPushButton('Clear Input')

        ########################################################################

        self.errors_tab.search_box = QGroupBox('Search')
        self.errors_tab.search_box.setObjectName('search_box')

        ########################################################################

        self.errors_tab.results_box = QGroupBox('Results')
        self.errors_tab.results_box.setObjectName('results_box')

        ########################################################################

        self.errors_tab.module.addItem('---')
        self.errors_tab.module.addItem('ASN')
        self.errors_tab.module.addItem('CertCheck')
        self.errors_tab.module.addItem('DNSResolver')
        self.errors_tab.module.addItem('DomainAge')
        self.errors_tab.module.addItem('GeoIP')
        self.errors_tab.module.addItem('GooglePageRank')
        self.errors_tab.module.addItem('GoogleSafeBrowsing')
        self.errors_tab.module.addItem('GoogleSearch')
        self.errors_tab.module.addItem('IPVoid')
        self.errors_tab.module.addItem('MXToolbox')
        self.errors_tab.module.addItem('Nmap')
        self.errors_tab.module.addItem('RobotsTxt')
        self.errors_tab.module.addItem('SpellChecker')
        self.errors_tab.module.addItem('Traceroute')
        self.errors_tab.module.addItem('Typo')
        self.errors_tab.module.addItem('VirusTotal')
        self.errors_tab.module.addItem('Whois')
        self.errors_tab.module.addItem('WOT')

        self.errors_tab.error_id.returnPressed.connect(self._errors_tab_changed)
        self.errors_tab.request_id.returnPressed.connect(self._errors_tab_changed)
        self.errors_tab.module.activated['QString'].connect(self._errors_tab_changed)
        self.errors_tab.module.currentIndexChanged['QString'].connect(self._errors_tab_changed)
        self.errors_tab.comment.returnPressed.connect(self._errors_tab_changed)
        self.errors_tab.created_from.dateChanged.connect(self._errors_tab_changed)
        self.errors_tab.created_to.dateChanged.connect(self._errors_tab_changed)

        self.errors_tab.submit_button.clicked.connect(self._errors_tab_changed)
        self.errors_tab.clear_button.clicked.connect(self._errors_tab_cleared)

        ########################################################################

        self.tab_widget.addTab(self.errors_tab, 'Errors')

        ########################################################################
        # Tab: 'Database Search'
        ########################################################################

        self.search_tab = QWidget()

        ########################################################################

        self.search_tab.model = QSqlRelationalTableModel()
        self.search_tab.model.setEditStrategy(QSqlTableModel.OnFieldChange)

        ########################################################################

        self.search_tab.table_view = QTableView()
        self.search_tab.table_view.setAlternatingRowColors(True)
        self.search_tab.table_view.setModel(self.search_tab.model)
        self.search_tab.table_view.verticalHeader().setVisible(False)

        ########################################################################

        self.search_tab.selectLineEdit = QLineEdit()
        self.search_tab.selectLineEdit.setProperty('mandatoryField', True)
        self.search_tab.selectLabel = QLabel('&SELECT')
        self.search_tab.selectLabel.setBuddy(self.search_tab.selectLineEdit)

        self.search_tab.fromLineEdit = QLineEdit()
        self.search_tab.fromLineEdit.setProperty('mandatoryField', True)
        self.search_tab.fromLabel = QLabel('&FROM')
        self.search_tab.fromLabel.setBuddy(self.search_tab.fromLineEdit)

        self.search_tab.whereLineEdit = QLineEdit()
        self.search_tab.whereLabel = QLabel('&WHERE')
        self.search_tab.whereLabel.setBuddy(self.search_tab.whereLineEdit)

        self.search_tab.groupLineEdit = QLineEdit()
        self.search_tab.groupLabel = QLabel('&GROUP BY')
        self.search_tab.groupLabel.setBuddy(self.search_tab.groupLineEdit)

        self.search_tab.orderLineEdit = QLineEdit()
        self.search_tab.orderLabel = QLabel('&ORDER BY')
        self.search_tab.orderLabel.setBuddy(self.search_tab.orderLineEdit)

        self.search_tab.submit_button = QPushButton('Submit Query')
        self.search_tab.clear_button = QPushButton('Clear Input')
        self.search_tab.info_text = QLabel('(Input fields with orange background are required)')

        ########################################################################

        self.search_tab.search_box = QGroupBox('Search')
        self.search_tab.search_box.setObjectName('search_box')

        ########################################################################

        self.search_tab.results_box = QGroupBox('Results')
        self.search_tab.results_box.setObjectName('results_box')

        ########################################################################

        self.search_tab.selectLineEdit.setText('*')

        self.search_tab.selectLineEdit.returnPressed.connect(self._search_tab_changed)
        self.search_tab.whereLineEdit.returnPressed.connect(self._search_tab_changed)
        self.search_tab.fromLineEdit.returnPressed.connect(self._search_tab_changed)
        self.search_tab.groupLineEdit.returnPressed.connect(self._search_tab_changed)
        self.search_tab.orderLineEdit.returnPressed.connect(self._search_tab_changed)

        self.search_tab.submit_button.clicked.connect(self._search_tab_changed)
        self.search_tab.clear_button.clicked.connect(self._search_tab_cleared)

        ########################################################################

        self.tab_widget.addTab(self.search_tab, 'Database Search')

    ############################################################################

    def _create_layout(self):
        """
        Method to create the layout.
        """

        mainLayout = QVBoxLayout()
        mainLayout.addWidget(self.logo)
        mainLayout.addWidget(self.tab_widget)

        mainWidget = QWidget()
        mainWidget.setLayout(mainLayout)
        self.setCentralWidget(mainWidget)

        ########################################################################

        # domains_tab

        domains_tab_form_layout = QGridLayout()
        domains_tab_form_layout.addWidget(self.domains_tab.domain_id_label, 0, 0)
        domains_tab_form_layout.addWidget(self.domains_tab.domain_id, 0, 1, 1, 9)
        domains_tab_form_layout.addWidget(self.domains_tab.name_label, 1, 0)
        domains_tab_form_layout.addWidget(self.domains_tab.name, 1, 1, 1, 9)
        domains_tab_form_layout.addWidget(self.domains_tab.state_label, 2, 0)
        domains_tab_form_layout.addWidget(self.domains_tab.state, 2, 1, 1, 9)
        domains_tab_form_layout.addWidget(self.domains_tab.comment_label, 3, 0)
        domains_tab_form_layout.addWidget(self.domains_tab.comment, 3, 1, 1, 9)
        domains_tab_form_layout.addWidget(self.domains_tab.updated_from_label, 4, 0)
        domains_tab_form_layout.addWidget(self.domains_tab.updated_from, 4, 1, 1, 9)
        domains_tab_form_layout.addWidget(self.domains_tab.updated_to_label, 5, 0)
        domains_tab_form_layout.addWidget(self.domains_tab.updated_to, 5, 1, 1, 9)
        domains_tab_form_layout.addWidget(self.domains_tab.submit_button, 6, 1)
        domains_tab_form_layout.addWidget(self.domains_tab.clear_button, 6, 2)
        self.domains_tab.search_box.setLayout(domains_tab_form_layout)

        domains_tab_result_layout = QGridLayout()
        domains_tab_result_layout.addWidget(self.domains_tab.table_view, 0, 0)
        self.domains_tab.results_box.setLayout(domains_tab_result_layout)

        domains_tab_layout = QVBoxLayout()
        domains_tab_layout.addWidget(self.domains_tab.search_box)
        domains_tab_layout.addWidget(self.domains_tab.results_box)
        self.domains_tab.setLayout(domains_tab_layout)

        ########################################################################

        # requests_tab

        requests_tab_form_layout = QGridLayout()
        requests_tab_form_layout.addWidget(self.requests_tab.request_id_label, 0, 0)
        requests_tab_form_layout.addWidget(self.requests_tab.request_id, 0, 1, 1, 9)
        requests_tab_form_layout.addWidget(self.requests_tab.domain_id_label, 1, 0)
        requests_tab_form_layout.addWidget(self.requests_tab.domain_id, 1, 1, 1, 9)
        requests_tab_form_layout.addWidget(self.requests_tab.state_label, 2, 0)
        requests_tab_form_layout.addWidget(self.requests_tab.state, 2, 1, 1, 9)
        requests_tab_form_layout.addWidget(self.requests_tab.comment_label, 3, 0)
        requests_tab_form_layout.addWidget(self.requests_tab.comment, 3, 1, 1, 9)
        requests_tab_form_layout.addWidget(self.requests_tab.created_from_label, 4, 0)
        requests_tab_form_layout.addWidget(self.requests_tab.created_from, 4, 1, 1, 9)
        requests_tab_form_layout.addWidget(self.requests_tab.created_to_label, 5, 0)
        requests_tab_form_layout.addWidget(self.requests_tab.created_to, 5, 1, 1, 9)
        requests_tab_form_layout.addWidget(self.requests_tab.submit_button, 6, 1)
        requests_tab_form_layout.addWidget(self.requests_tab.clear_button, 6, 2)
        self.requests_tab.search_box.setLayout(requests_tab_form_layout)

        requests_tab_result_layout = QGridLayout()
        requests_tab_result_layout.addWidget(self.requests_tab.table_view, 0, 0)
        self.requests_tab.results_box.setLayout(requests_tab_result_layout)

        requests_tab_layout = QVBoxLayout()
        requests_tab_layout.addWidget(self.requests_tab.search_box)
        requests_tab_layout.addWidget(self.requests_tab.results_box)
        self.requests_tab.setLayout(requests_tab_layout)

        ########################################################################

        # modules_tab

        modules_tab_form_layout = QGridLayout()
        modules_tab_form_layout.addWidget(self.modules_tab.module_label, 0, 0)
        modules_tab_form_layout.addWidget(self.modules_tab.module, 0, 1, 1, 9)
        modules_tab_form_layout.addWidget(self.modules_tab.module_id_label, 1, 0)
        modules_tab_form_layout.addWidget(self.modules_tab.module_id, 1, 1, 1, 9)
        modules_tab_form_layout.addWidget(self.modules_tab.request_id_label, 2, 0)
        modules_tab_form_layout.addWidget(self.modules_tab.request_id, 2, 1, 1, 9)
        modules_tab_form_layout.addWidget(self.modules_tab.submit_button, 3, 1)
        modules_tab_form_layout.addWidget(self.modules_tab.clear_button, 3, 2)
        self.modules_tab.search_box.setLayout(modules_tab_form_layout)

        modules_tab_result_layout = QGridLayout()
        modules_tab_result_layout.addWidget(self.modules_tab.table_view, 0, 0)
        self.modules_tab.results_box.setLayout(modules_tab_result_layout)

        modules_tab_layout = QVBoxLayout()
        modules_tab_layout.addWidget(self.modules_tab.search_box)
        modules_tab_layout.addWidget(self.modules_tab.results_box)
        self.modules_tab.setLayout(modules_tab_layout)

        ########################################################################

        # versions_tab

        versions_tab_form_layout = QGridLayout()
        versions_tab_form_layout.addWidget(self.versions_tab.refresh_button, 0, 0)
        self.versions_tab.search_box.setLayout(versions_tab_form_layout)

        versions_tab_result_layout = QGridLayout()
        versions_tab_result_layout.addWidget(self.versions_tab.table_view, 0, 0)
        self.versions_tab.results_box.setLayout(versions_tab_result_layout)

        versions_tab_layout = QVBoxLayout()
        versions_tab_layout.addWidget(self.versions_tab.search_box)
        versions_tab_layout.addWidget(self.versions_tab.results_box)
        self.versions_tab.setLayout(versions_tab_layout)

        ########################################################################

        # errors_tab

        errors_tab_form_layout = QGridLayout()
        errors_tab_form_layout.addWidget(self.errors_tab.error_id_label, 0, 0)
        errors_tab_form_layout.addWidget(self.errors_tab.error_id, 0, 1, 1, 9)
        errors_tab_form_layout.addWidget(self.errors_tab.request_id_label, 1, 0)
        errors_tab_form_layout.addWidget(self.errors_tab.request_id, 1, 1, 1, 9)
        errors_tab_form_layout.addWidget(self.errors_tab.module_label, 2, 0)
        errors_tab_form_layout.addWidget(self.errors_tab.module, 2, 1, 1, 9)
        errors_tab_form_layout.addWidget(self.errors_tab.comment_label, 3, 0)
        errors_tab_form_layout.addWidget(self.errors_tab.comment, 3, 1, 1, 9)
        errors_tab_form_layout.addWidget(self.errors_tab.created_from_label, 4, 0)
        errors_tab_form_layout.addWidget(self.errors_tab.created_from, 4, 1, 1, 9)
        errors_tab_form_layout.addWidget(self.errors_tab.created_to_label, 5, 0)
        errors_tab_form_layout.addWidget(self.errors_tab.created_to, 5, 1, 1, 9)
        errors_tab_form_layout.addWidget(self.errors_tab.submit_button, 6, 1)
        errors_tab_form_layout.addWidget(self.errors_tab.clear_button, 6, 2)
        self.errors_tab.search_box.setLayout(errors_tab_form_layout)

        errors_tab_result_layout = QGridLayout()
        errors_tab_result_layout.addWidget(self.errors_tab.table_view, 0, 0)
        self.errors_tab.results_box.setLayout(errors_tab_result_layout)

        errors_tab_layout = QVBoxLayout()
        errors_tab_layout.addWidget(self.errors_tab.search_box)
        errors_tab_layout.addWidget(self.errors_tab.results_box)
        self.errors_tab.setLayout(errors_tab_layout)

        ########################################################################

        # search_tab

        search_tab_form_layout = QGridLayout()
        search_tab_form_layout.addWidget(self.search_tab.selectLabel, 0, 0)
        search_tab_form_layout.addWidget(self.search_tab.selectLineEdit, 0, 1, 1, 9)
        search_tab_form_layout.addWidget(self.search_tab.fromLabel, 1, 0)
        search_tab_form_layout.addWidget(self.search_tab.fromLineEdit, 1, 1, 1, 9)
        search_tab_form_layout.addWidget(self.search_tab.whereLabel, 2, 0)
        search_tab_form_layout.addWidget(self.search_tab.whereLineEdit, 2, 1, 1, 9)
        search_tab_form_layout.addWidget(self.search_tab.groupLabel, 3, 0)
        search_tab_form_layout.addWidget(self.search_tab.groupLineEdit, 3, 1, 1, 9)
        search_tab_form_layout.addWidget(self.search_tab.orderLabel, 4, 0)
        search_tab_form_layout.addWidget(self.search_tab.orderLineEdit, 4, 1, 1, 9)
        search_tab_form_layout.addWidget(self.search_tab.submit_button, 5, 1)
        search_tab_form_layout.addWidget(self.search_tab.clear_button, 5, 2)
        search_tab_form_layout.addWidget(self.search_tab.info_text, 5, 3)
        self.search_tab.search_box.setLayout(search_tab_form_layout)

        search_tab_result_layout = QGridLayout()
        search_tab_result_layout.addWidget(self.search_tab.table_view, 0, 0)
        self.search_tab.results_box.setLayout(search_tab_result_layout)

        search_tab_layout = QVBoxLayout()
        search_tab_layout.addWidget(self.search_tab.search_box)
        search_tab_layout.addWidget(self.search_tab.results_box)
        self.search_tab.setLayout(search_tab_layout)

    ############################################################################

    def _create_style_sheet(self):
        """
        Method to create the stylesheet.
        """

        self.setStyleSheet('''
            QGroupBox#search_box {
                margin: 20px 0 0 0;
                padding-top: 20px;
            }
            QGroupBox#results_box {
                margin: 20px 0 0 0;
                padding-top: 20px;
            }
            QGroupBox::title {
                background: #fff;
                border-top-left-radius: 3px;
                border-bottom-right-radius: 3px;
                border-left: 1px solid #dadada;
                border-top: 1px solid #dadada;
                subcontrol-origin: margin;
                padding: 2px 3px;
                margin-top: 20px;
            }
            QTableView {
                selection-background-color: #008BCA;
                alternate-background-color: rgb(217,238,247);
            }
            QLineEdit {
                border: 1px solid #9a9fa0;
                border-radius: 3px;
                padding: 0 3px;
            }
            QDateTimeEdit {
                border: 1px solid #9a9fa0;
                border-radius: 3px;
                padding: 0 4px;
            }
            QComboBox {
                border: 1px solid #9a9fa0;
                border-radius: 3px;
                padding: 0 5px;
            }
            QPushButton {
                background: #495257;
                border-radius: 3px;
                color: #fff;
                padding: 5px 7px;
                margin: 5px 0;
            }
            QPushButton:pressed {
                background: #9a9fa0;
            }
            QTabBar::tab {
                background: #fff;
                border-radius: 3px;
                padding: 5px 7px;
                margin: 0 5px;
                border: 1px solid #495257;
            }
            QTabBar::tab:selected {
                background: #008BCA;
                color: #fff;
            }
            *[mandatoryField="true"]  {
                background: #fed980;
            }''')

    ############################################################################

    @pyqtSlot()
    def _domains_tab_changed(self):
        """
        Method to update output in domains_tab.
        """

        domain_id = self.domains_tab.domain_id.text()
        name = self.domains_tab.name.text()
        state = self.domains_tab.state.currentText()
        comment = self.domains_tab.comment.text()
        updated_from = self.domains_tab.updated_from.dateTime()
        updated_to = self.domains_tab.updated_to.dateTime()

        expression = ['''
            SELECT
                id as "Domain ID",
                name as "Name",
                state as "State",
                comment as "Comment",
                updated as "Updated"
            FROM domains''']

        if domain_id:

            expression.append('WHERE' if len(expression) == 1 else 'AND')
            expression.append('id = "%s"' % domain_id)

        if name:

            expression.append('WHERE' if len(expression) == 1 else 'AND')
            expression.append('name like "%s"' % ('%' + name + '%',))

        if state:

            if state != '---':
                expression.append('WHERE' if len(expression) == 1 else 'AND')
                expression.append('state = "%s"' % state)

        if comment:

            expression.append('WHERE' if len(expression) == 1 else 'AND')
            expression.append('comment like "%s"' % ('%' + comment + '%',))


        expression.append('WHERE' if len(expression) == 1 else 'AND')
        expression.append('updated BETWEEN "%s" AND "%s"' % (
            updated_from.toPyDateTime(), updated_to.toPyDateTime()))

        query = QSqlQuery()
        query.exec_(' '.join(expression))
        self.domains_tab.model.setQuery(query)
        self.domains_tab.table_view.resizeColumnsToContents()
        self.domains_tab.table_view.horizontalHeader().setStretchLastSection(True)

    @pyqtSlot()
    def _requests_tab_changed(self):
        """
        Method to update output in requests_tab.
        """

        request_id = self.requests_tab.request_id.text()
        domain_id = self.requests_tab.domain_id.text()
        state = self.requests_tab.state.currentText()
        comment = self.requests_tab.comment.text()
        created_from = self.requests_tab.created_from.dateTime()
        created_to = self.requests_tab.created_to.dateTime()

        expression = ['''
            SELECT
                id as "Request ID",
                domain_id as "Domain ID",
                state as "State",
                comment as "Comment",
                created as "Created"
            FROM requests''']

        if request_id:

            expression.append('WHERE' if len(expression) == 1 else 'AND')
            expression.append('id = "%s"' % request_id)

        if domain_id:

            expression.append('WHERE' if len(expression) == 1 else 'AND')
            expression.append('domain_id = "%s"' % domain_id)

        if state:

            if state != '---':
                expression.append('WHERE' if len(expression) == 1 else 'AND')
                expression.append('state = "%s"' % state)

        if comment:

            expression.append('WHERE' if len(expression) == 1 else 'AND')
            expression.append('comment like "%s"' % ('%' + comment + '%',))


        expression.append('WHERE' if len(expression) == 1 else 'AND')
        expression.append('created BETWEEN "%s" AND "%s"' % (
            created_from.toPyDateTime(), created_to.toPyDateTime()))

        query = QSqlQuery()
        query.exec_(' '.join(expression))
        self.requests_tab.model.setQuery(query)
        self.requests_tab.table_view.resizeColumnsToContents()
        self.requests_tab.table_view.horizontalHeader().setStretchLastSection(True)

    @pyqtSlot()
    def _modules_tab_changed(self):
        """
        Method to update output in modules_tab.
        """

        module = self.modules_tab.module.currentText()
        module_id = self.modules_tab.module_id.text()
        request_id = self.modules_tab.request_id.text()

        expression = ['SELECT * FROM %s' % 'module_' + module]

        if module_id:

            expression.append('WHERE' if len(expression) == 1 else 'AND')
            expression.append('id = "%s"' % module_id)

        if request_id:

            expression.append('WHERE' if len(expression) == 1 else 'AND')
            expression.append('request_id = "%s"' % request_id)

        query = QSqlQuery()
        query.exec_(' '.join(expression))
        self.modules_tab.model.setQuery(query)
        self.modules_tab.table_view.resizeColumnsToContents()
        self.modules_tab.table_view.horizontalHeader().setStretchLastSection(True)

    @pyqtSlot()
    def _versions_tab_changed(self):
        """
        Method to update output in versions_tab.
        """

        expression = ['''
            SELECT
                module as "Module",
                version as "Version",
                updated as "Updated"
            FROM versions''']

        query = QSqlQuery()
        query.exec_(' '.join(expression))
        self.versions_tab.model.setQuery(query)
        self.versions_tab.table_view.resizeColumnsToContents()
        self.versions_tab.table_view.horizontalHeader().setStretchLastSection(True)

    @pyqtSlot()
    def _errors_tab_changed(self):
        """
        Method to update output in errors_tab.
        """

        error_id = self.errors_tab.error_id.text()
        request_id = self.errors_tab.request_id.text()
        module = self.errors_tab.module.currentText()
        comment = self.errors_tab.comment.text()
        created_from = self.errors_tab.created_from.dateTime()
        created_to = self.errors_tab.created_to.dateTime()

        expression = ['''
            SELECT
                id as "Error ID",
                request_id as "Request ID",
                module as "Module",
                comment as "Comment",
                created as "Created"
            FROM errors''']

        if error_id:

            expression.append('WHERE' if len(expression) == 1 else 'AND')
            expression.append('id = "%s"' % error_id)

        if request_id:

            expression.append('WHERE' if len(expression) == 1 else 'AND')
            expression.append('request_id = "%s"' % request_id)

        if module:

            if module != '---':
                expression.append('WHERE' if len(expression) == 1 else 'AND')
                expression.append('module = "%s"' % module)

        if comment:

            expression.append('WHERE' if len(expression) == 1 else 'AND')
            expression.append('comment like "%s"' % ('%' + comment + '%',))


        expression.append('WHERE' if len(expression) == 1 else 'AND')
        expression.append('created BETWEEN "%s" AND "%s"' % (
            created_from.toPyDateTime(), created_to.toPyDateTime()))

        query = QSqlQuery()
        query.exec_(' '.join(expression))
        self.errors_tab.model.setQuery(query)
        self.errors_tab.table_view.resizeColumnsToContents()
        self.errors_tab.table_view.horizontalHeader().setStretchLastSection(True)

    @pyqtSlot()
    def _search_tab_changed(self):
        """
        Method to update output in search_tab.
        """

        select_field = self.search_tab.selectLineEdit.text()
        from_field = self.search_tab.fromLineEdit.text()
        where_field = self.search_tab.whereLineEdit.text()
        group_field = self.search_tab.groupLineEdit.text()
        order_field = self.search_tab.orderLineEdit.text()

        expression = "SELECT %s FROM %s" % (select_field, from_field)

        if where_field:
            expression += " WHERE %s" % where_field

        if group_field:
            expression += " GROUP BY %s" % group_field

        if order_field:
            expression += " ORDER BY %s" % order_field

        query = QSqlQuery()
        query.exec_(expression)
        self.search_tab.model.setQuery(query)
        self.search_tab.table_view.resizeColumnsToContents()
        self.search_tab.table_view.horizontalHeader().setStretchLastSection(True)

    ############################################################################

    @pyqtSlot()
    def _domains_tab_cleared(self):
        """
        Method to clear output in domains_tab.
        """

        self.domains_tab.domain_id.clear()
        self.domains_tab.name.clear()
        self.domains_tab.state.setCurrentIndex(0)
        self.domains_tab.comment.clear()
        self.domains_tab.updated_from.setDateTime(QDateTime.currentDateTime().addDays(-1))
        self.domains_tab.updated_to.setDateTime(QDateTime.currentDateTime())
        self.domains_tab.submit_button.click()

    @pyqtSlot()
    def _requests_tab_cleared(self):
        """
        Method to clear output in requests_tab.
        """

        self.requests_tab.request_id.clear()
        self.requests_tab.domain_id.clear()
        self.requests_tab.state.setCurrentIndex(0)
        self.requests_tab.comment.clear()
        self.requests_tab.created_from.setDateTime(QDateTime.currentDateTime().addDays(-1))
        self.requests_tab.created_to.setDateTime(QDateTime.currentDateTime())
        self.requests_tab.submit_button.click()

    @pyqtSlot()
    def _modules_tab_cleared(self):
        """
        Method to clear output in modules_tab.
        """

        self.modules_tab.module.setCurrentIndex(0)
        self.modules_tab.module_id.clear()
        self.modules_tab.request_id.clear()
        self.modules_tab.submit_button.click()

    @pyqtSlot()
    def _errors_tab_cleared(self):
        """
        Method to clear output in errors_tab.
        """

        self.errors_tab.error_id.clear()
        self.errors_tab.request_id.clear()
        self.errors_tab.module.setCurrentIndex(0)
        self.errors_tab.comment.clear()
        self.errors_tab.created_from.setDateTime(QDateTime.currentDateTime().addDays(-1))
        self.errors_tab.created_to.setDateTime(QDateTime.currentDateTime())
        self.errors_tab.submit_button.click()

    @pyqtSlot()
    def _search_tab_cleared(self):
        """
        Method to clear output in search_tab.
        """

        self.search_tab.selectLineEdit.setText('*')
        self.search_tab.fromLineEdit.clear()
        self.search_tab.whereLineEdit.clear()
        self.search_tab.groupLineEdit.clear()
        self.search_tab.orderLineEdit.clear()
        self.search_tab.submit_button.click()

################################################################################

if __name__ == '__main__':

    app = QApplication(sys.argv)

    mainwindow = DomeinSearchViewerGUI()
    mainwindow.show()

    app.exec_()
