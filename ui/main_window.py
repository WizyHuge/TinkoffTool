from collections import deque
from datetime import datetime, timezone
import json
import os
import sys
import configparser
import logging

from PyQt6.QtGui import QAction
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebChannel import QWebChannel
from PyQt6.QtCore import QObject
from PyQt6.QtCore import QThread, Qt, pyqtSignal, QTimer
from PyQt6.QtWidgets import (
    QComboBox, QDialog, QGridLayout, QHBoxLayout,
    QHeaderView, QLabel, QLineEdit, QListWidget, QMainWindow, QPushButton,
    QSplitter, QTableWidget, QTableWidgetItem, QTabWidget, QTextEdit,
    QVBoxLayout, QWidget, QSizePolicy, QGroupBox, QCheckBox, QSpinBox,
    QFileDialog, QSystemTrayIcon, QMenu, QApplication, QAbstractItemView
)

from workers.api_worker import ApiWorker
from workers.stream_worker import MarketStreamWorker
from workers.trade_worker import TradeWorker
from workers.sender import send_signal
import account
from ui import styles

BROKER_COMMISSION = 0.0005

def apply_broker_commission(price, direction='BUY'):
    if direction == 'BUY':
        return price * (1 + BROKER_COMMISSION)
    else:
        return price * (1 - BROKER_COMMISSION)

LOG_LEVELS = {
    'DEBUG': logging.DEBUG,
    'INFO': logging.INFO, 
    'WARNING': logging.WARNING,
    'ERROR': logging.ERROR
}

STRATEGY_PARAMS = {
    "Advanced Strategy": {"min_prices": 20},
}

CATEGORY_COLORS = {
    'Акции': '#FF6B6B', 'Облигации': '#4ECDC4', 'Валюта': '#FFE66D', 'Фонды': '#95E1D3',
    'Драгметаллы': '#F7B731', 'Фьючерсы': '#A29BFE', 'Опционы': '#FD79A8', 'Другое': '#D5D5D5'
}

class AccountDialog(QDialog):
    def __init__(self, parent=None, account_name="", token=""):
        super().__init__(parent)
        self.setWindowTitle("Account settings")
        self.setModal(True)
        self.build_ui(account_name, token)
        if parent and hasattr(parent, 'theme'):
            self.setStyleSheet(parent.theme["dialog"])

    def build_ui(self, account_name, token):
        layout = QVBoxLayout(self)
        self.nameEdit = QLineEdit()
        self.nameEdit.setPlaceholderText("Account name")
        self.nameEdit.setStyleSheet(styles.DARK_THEME["line_edit"])
        self.nameEdit.setText(account_name)
        self.errorLabel = QLabel()
        self.tokenEdit = QLineEdit()
        self.tokenEdit.setEchoMode(QLineEdit.EchoMode.Password)
        self.tokenEdit.setPlaceholderText("Токен Tinkoff API")
        self.tokenEdit.setStyleSheet(styles.DARK_THEME["line_edit"])
        self.tokenEdit.setText(token)
        layout.addWidget(self.nameEdit)
        layout.addWidget(self.tokenEdit)
        layout.addWidget(self.errorLabel)
        horizontal_layout = QHBoxLayout()
        self.okButton = QPushButton("Сохранить")
        self.okButton.setStyleSheet(styles.DARK_THEME["button_secondary"])
        self.okButton.clicked.connect(self.accept)
        self.cancelButton = QPushButton("Отмена")
        self.cancelButton.setStyleSheet(styles.DARK_THEME["button_secondary"])
        self.cancelButton.clicked.connect(self.reject)
        horizontal_layout.addWidget(self.okButton)
        horizontal_layout.addWidget(self.cancelButton)
        layout.addLayout(horizontal_layout)
        
    def accept(self):
        if ApiWorker().check_token(self.tokenEdit.text().strip()) is False:
            self.errorLabel.setText("Ошибка: некорректный токен API")
            return
        return super().accept()

    def get_data(self):
        return self.nameEdit.text().strip(), self.tokenEdit.text().strip()

class AccountManagerWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Account manager")
        self.setMinimumSize(400, 300)
        self.main_window = parent
        self.build_ui()

    def build_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        self.accountsList = QListWidget()
        self.accountsList.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.accountsList.setStyleSheet(styles.DARK_THEME["list"])
        self.addAccountBtn = QPushButton("Add account")
        self.addAccountBtn.setStyleSheet(styles.DARK_THEME["button_secondary"])
        self.editAccountBtn = QPushButton("Edit account")
        self.editAccountBtn.setStyleSheet(styles.DARK_THEME["button_secondary"])
        self.deleteAccountBtn = QPushButton("Delete account")
        self.deleteAccountBtn.setStyleSheet(styles.DARK_THEME["button_secondary"])
        buttons = QHBoxLayout()
        buttons.addWidget(self.addAccountBtn)
        buttons.addWidget(self.editAccountBtn)
        buttons.addWidget(self.deleteAccountBtn)
        layout.addWidget(self.accountsList)
        layout.addLayout(buttons)
        self.addAccountBtn.clicked.connect(self.add_account)
        self.editAccountBtn.clicked.connect(self.edit_account)
        self.deleteAccountBtn.clicked.connect(self.delete_account)
        self.accountsList.itemDoubleClicked.connect(self.edit_account)
        self.refresh_accounts_list()

    def refresh_accounts_list(self):
        self.accountsList.clear()
        accounts = account.load_accounts()
        for name in accounts.keys():
            self.accountsList.addItem(name)
        if self.main_window:
            self.main_window.refresh_accounts_list()

    def add_account(self):
        dialog = AccountDialog(self)
        if dialog.exec():
            name, token = dialog.get_data()
            if not name or not token:
                return
            accounts = account.load_accounts()
            if name in accounts:
                return
            accounts[name] = token
            account.save_accounts(accounts)
            self.refresh_accounts_list()

    def edit_account(self):
        current_item = self.accountsList.currentItem()
        if not current_item:
            return
        old_name = current_item.text()
        accounts = account.load_accounts()
        if old_name not in accounts:
            return
        dialog = AccountDialog(self, old_name, accounts[old_name])
        if dialog.exec():
            new_name, new_token = dialog.get_data()
            if not new_name or not new_token:
                return
            if new_name != old_name and new_name in accounts:
                return
            if new_name != old_name:
                del accounts[old_name]
            accounts[new_name] = new_token
            account.save_accounts(accounts)
            self.refresh_accounts_list()

    def delete_account(self):
        current_item = self.accountsList.currentItem()
        if not current_item:
            return
        name = current_item.text()
        accounts = account.load_accounts()
        if name in accounts:
            del accounts[name]
            account.save_accounts(accounts)
            self.refresh_accounts_list()

class MainWindow(QMainWindow):
    requestConnect = pyqtSignal()
    requestFetchPortfolio = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setup_variables()
        self.setup_ui()
        self.setup_workers()
        self.setup_tray_icon()
        
    def setup_variables(self):
        self.active_strategy = None
        self.worker = None
        self.streamWorker = None
        self.tradeWorker = None
        self.thread = None
        self.accounts_window = None
        self.tray_icon = None
        self.is_minimized_to_tray = False
        self.current_log_level = logging.INFO
        self.setStyleSheet(styles.DARK_THEME["main_window"])
        self.SETTINGS_FILE = "app_settings.ini"
        self.DEFAULT_SETTINGS = {
            'chart': {'theme': 'Темная', 'show_grid': 'false', 'show_volume': 'false', 'auto_refresh_portfolio': 'true', 'refresh_interval': '60'},
            'notifications': {'enable_telegram': 'false', 'telegram_token': '', 'telegram_chat_id': ''},
            'system': {'auto_start': 'false', 'minimize_to_tray': 'false', 'log_level': 'INFO'},
            'strategies': {'testing_mode': 'true', 'auto_start_strategy': 'false', 'allow_parallel_strategies': 'false', 'max_daily_trades': '50', 'min_trade_interval': '60'}
        }
        self.chart_data = deque(maxlen=10000)
        self.is_loading_history = False
        self.pending_stream_ticker = None
        self.pending_stream_token = None
        self.current_ticker = None
        self.current_token = None
        self.stream_auto_reconnect = False
        self.stream_reconnect_delay = 5
        self.candles = []
        self.current_candle = None
        self.last_candle_time = None
        self.portfolio_refresh_timer = QTimer()
        self.portfolio_refresh_timer.setSingleShot(False)

    def setup_ui(self):
        self.setWindowTitle("TinkoffAnalyzer — Trading Bot")
        self.setup_tabs()
        self.setup_central_widget()
        self.refresh_accounts_list()

    def setup_tabs(self):
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet(styles.DARK_THEME["tab_widget"])
        self.tab_account = QWidget()
        self.tab_portfolio = QWidget()
        self.tab_strategy = QWidget()
        self.tab_chart = QWidget()
        self.tab_settings = QWidget()
        for tab in [self.tab_account, self.tab_portfolio, self.tab_strategy, self.tab_chart, self.tab_settings]:
            tab.setStyleSheet(styles.DARK_THEME["widget"])
        self.tabs.addTab(self.tab_account, 'Account')
        self.portfolio_index = self.tabs.addTab(self.tab_portfolio, 'Portfolio')
        self.strategy_index = self.tabs.addTab(self.tab_strategy, 'Strategies')
        self.chart_index = self.tabs.addTab(self.tab_chart, 'Chart')
        self.tabs.addTab(self.tab_settings, 'Settings')
        self.tabs.setTabVisible(self.strategy_index, False)
        self.tabs.setTabVisible(self.portfolio_index, False)
        self.tabs.setTabVisible(self.chart_index, False)
        self.setup_account_tab()
        self.setup_portfolio_tab()
        self.setup_strategy_tab()
        self.setup_chart_tab()
        self.setup_settings_tab()

    def setup_central_widget(self):
        central = QWidget(self)
        layout = QGridLayout(central)
        layout.addWidget(self.tabs, 0, 0, 1, 1)
        self.setCentralWidget(central)

    def setup_account_tab(self):
        layout = QGridLayout(self.tab_account)
        self.tokenEdit = QLineEdit()
        self.tokenEdit.setEchoMode(QLineEdit.EchoMode.Password)
        self.tokenEdit.setPlaceholderText("Token Tinkoff Invest")
        self.tokenEdit.setStyleSheet(styles.DARK_THEME["line_edit"])
        self.connectBtn = QPushButton("Connect")
        self.connectBtn.setStyleSheet(styles.DARK_THEME["button_secondary"])
        self.statusLabel = QLabel()
        self.log = QTextEdit()
        self.log.setStyleSheet(styles.DARK_THEME["text_edit"])
        self.log.setReadOnly(True)
        self.accounts = QComboBox()
        self.accounts.setStyleSheet(styles.DARK_THEME["combo_box"])
        self.accounts.currentIndexChanged.connect(self.account_changed)
        header = QHBoxLayout()
        header.addWidget(self.tokenEdit)
        header.addWidget(self.connectBtn)
        layout.addLayout(header, 0, 0)
        layout.addWidget(self.accounts, 1, 0)
        layout.addWidget(self.statusLabel, 2, 0)
        layout.addWidget(self.log, 3, 0)
        self.connectBtn.clicked.connect(self.connect_clicked)

    def setup_portfolio_tab(self):
        layout = QVBoxLayout(self.tab_portfolio)
        metrics_layout = QHBoxLayout()
        self.totalAmountLabel = QLabel("Total cost: -")
        self.positionsCountLabel = QLabel("Positions: -")
        self.accountIdLabel = QLabel("Account: -")
        metrics_layout.addWidget(self.totalAmountLabel)
        metrics_layout.addWidget(self.positionsCountLabel)
        metrics_layout.addWidget(self.accountIdLabel)
        metrics_layout.addStretch()
        splitter = QSplitter(Qt.Orientation.Vertical)
        self.positionsTable = QTableWidget()
        self.positionsTable.setColumnCount(7)
        self.positionsTable.setHorizontalHeaderLabels(["Name", "Quantity", "Price", "Cost", "Currency", "Ticker", "UID"])
        self.positionsTable.horizontalHeader().setStretchLastSection(True)
        self.positionsTable.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.positionsTable.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.positionsTable.setStyleSheet(styles.DARK_THEME["table_widget"])
        self.positionsTable.setSortingEnabled(True)
        self.pieChart = QWebEngineView(self.tab_portfolio)
        self.pieChart.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        class ChartBridge(QObject):
            def __init__(self, main_window):
                super().__init__()
                self.main_window = main_window
        self.chart_bridge = ChartBridge(self)
        self.channel = QWebChannel()
        self.channel.registerObject("pyObject", self.chart_bridge)
        self.pieChart.page().setWebChannel(self.channel)
        self.pieChart.setHtml(self._get_pie_chart())
        splitter.addWidget(self.positionsTable)
        splitter.addWidget(self.pieChart)
        splitter.setSizes([400, 300])
        splitter.setChildrenCollapsible(False)
        layout.addLayout(metrics_layout)
        layout.addWidget(splitter)

    def setup_strategy_tab(self):
        main_layout = QVBoxLayout(self.tab_strategy)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(10, 10, 10, 10)
        strategy_container = QWidget()
        strategy_layout = QVBoxLayout(strategy_container)
        strategy_layout.setSpacing(10)
        strategy_layout.setContentsMargins(0, 0, 0, 0)
        self.setup_strategy_selection(strategy_layout)
        self.setup_strategy_status(strategy_layout)
        self.setup_strategy_log(strategy_layout)
        main_layout.addWidget(strategy_container, 1)

    def setup_strategy_selection(self, parent_layout):
        strategy_group = QGroupBox("Strategy selection")
        strategy_group.setStyleSheet(styles.DARK_THEME["group_box"])
        strategy_layout = QVBoxLayout(strategy_group)
        strategy_select_layout = QHBoxLayout()
        strategy_label = QLabel("Strategy:")
        strategy_label.setStyleSheet(styles.DARK_THEME["label_primary"])
        strategy_select_layout.addWidget(strategy_label)
        self.strategyCombo = QComboBox()
        self.strategyCombo.addItems(["Выберите стратегию", "Advanced Strategy"])
        self.strategyCombo.setStyleSheet(styles.DARK_THEME["combo_box"])
        self.strategyCombo.currentIndexChanged.connect(self.strategy_changed)
        strategy_select_layout.addWidget(self.strategyCombo)
        strategy_select_layout.addStretch()
        params_layout = QHBoxLayout()
        params_label = QLabel('Parameters:')
        params_label.setStyleSheet(styles.DARK_THEME["label_primary"])
        params_layout.addWidget(params_label)
        self.paramsLabel = QLabel("Not selected")
        self.paramsLabel.setStyleSheet(styles.DARK_THEME["label_secondary"])
        self.paramsLabel.setMinimumHeight(35)
        params_layout.addWidget(self.paramsLabel, 1)
        strategy_layout.addLayout(strategy_select_layout)
        strategy_layout.addLayout(params_layout)
        parent_layout.addWidget(strategy_group)

    def setup_strategy_status(self, parent_layout):
        status_group = QGroupBox("Strategy status")
        status_group.setStyleSheet(styles.DARK_THEME["group_box"])
        status_layout = QVBoxLayout(status_group)
        self.strategyStatusLabel = QLabel("Not selected")
        self.strategyStatusLabel.setStyleSheet(styles.DARK_THEME["label_primary"])
        self.strategyStatusLabel.setMinimumHeight(45)
        status_layout.addWidget(self.strategyStatusLabel)
        self.signalStatsLabel = QLabel("Stats: BUY: 0, SELL: 0, All: 0")
        self.signalStatsLabel.setStyleSheet(styles.DARK_THEME["label_secondary"])
        status_layout.addWidget(self.signalStatsLabel)
        parent_layout.addWidget(status_group)

    def setup_strategy_log(self, parent_layout):
        log_group = QGroupBox("Signals log")
        log_group.setStyleSheet(styles.DARK_THEME["group_box"])
        log_layout = QVBoxLayout(log_group)
        self.strategySignalsLog = QTextEdit()
        self.strategySignalsLog.setReadOnly(True)
        self.strategySignalsLog.setStyleSheet(styles.DARK_THEME["line_edit"])
        self.strategySignalsLog.setPlaceholderText("Strategy signals will be logged here")
        log_layout.addWidget(self.strategySignalsLog)
        log_buttons_layout = QHBoxLayout()
        clear_log_btn = QPushButton("Clear log")
        clear_log_btn.setStyleSheet(styles.DARK_THEME["button_secondary"])
        clear_log_btn.clicked.connect(self.strategySignalsLog.clear)
        export_log_btn = QPushButton("Export log")
        export_log_btn.setStyleSheet(styles.DARK_THEME["button_secondary"])
        export_log_btn.clicked.connect(self.export_strategy_log)
        log_buttons_layout.addWidget(clear_log_btn)
        log_buttons_layout.addWidget(export_log_btn)
        log_buttons_layout.addStretch()
        log_layout.addLayout(log_buttons_layout)
        parent_layout.addWidget(log_group, 1)

    def setup_chart_tab(self):
        main_layout = QVBoxLayout(self.tab_chart)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(5)
        self.tickerEdit = QLineEdit(self.tab_chart)
        self.tickerEdit.setPlaceholderText("Ticker / UID. e.g. TQBR / MOEX")
        self.tickerEdit.setStyleSheet(styles.DARK_THEME["line_edit"])
        self.setup_chart_controls(main_layout)
        self.setup_chart_widget(main_layout)

    def setup_chart_controls(self, parent_layout):
        mode_layout = QHBoxLayout()
        order_layout = QHBoxLayout()
        self.historicalLabel = QLabel("Period:", alignment=Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.historicalLabel.setStyleSheet("font-size: 14px; color: white")
        self.historicalComboBox = QComboBox()
        self.historicalComboBox.addItems(["1 день", "7 дней", "30 дней", "90 дней", "180 дней", "365 дней", "Всё время"])
        self.historicalComboBox.setCurrentIndex(-1)
        self.historicalComboBox.setStyleSheet(styles.DARK_THEME["combo_box"])
        self.realtimeBtn = QPushButton("Real time stream")
        self.realtimeBtn.setStyleSheet(styles.DARK_THEME["button_secondary"])
        self.stopBtn = QPushButton("Stop stream")
        self.stopBtn.setStyleSheet(styles.DARK_THEME["button_secondary"])
        self.stopBtn.setEnabled(False)
        self.current_price = QLabel("Current price: -", alignment=Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.current_price.setStyleSheet("font-size: 14px; color: white")
        self.buyBtn = QPushButton("BUY", self.tab_chart)
        self.buyBtn.setStyleSheet(styles.DARK_THEME["button_secondary"])
        self.sellBtn = QPushButton("SELL", self.tab_chart)
        self.sellBtn.setStyleSheet(styles.DARK_THEME["button_secondary"])
        self.changeMarketComboBox = QComboBox()
        self.changeMarketComboBox.addItems(['Market', 'Limit'])
        self.changeMarketComboBox.setStyleSheet(styles.DARK_THEME["combo_box"])
        self.quantitySpinBox = QSpinBox(self.tab_chart)
        self.quantitySpinBox.setStyleSheet(styles.DARK_THEME["spinbox"])
        self.quantitySpinBox.setMinimum(1)
        self.priceEdit = QLineEdit(self.tab_chart)
        self.priceEdit.setStyleSheet(styles.DARK_THEME["line_edit"])
        self.priceEdit.setPlaceholderText("Buy / Sell price")
        self.realtimeBtn.clicked.connect(self.start_stream)
        self.stopBtn.clicked.connect(self.stop_stream)
        self.historicalComboBox.currentIndexChanged.connect(lambda: self.load_historical_data(self.historicalComboBox.currentText().split()[0]))
        self.buyBtn.clicked.connect(lambda: self.send_order('BUY'))
        self.sellBtn.clicked.connect(lambda: self.send_order('SELL'))
        self.changeMarketComboBox.currentIndexChanged.connect(self.change_market_type)
        self.buyBtn.setEnabled(False)
        self.sellBtn.setEnabled(False)
        self.changeMarketComboBox.setEnabled(False)
        self.quantitySpinBox.setEnabled(False)
        self.priceEdit.setEnabled(False)
        order_layout.addWidget(self.buyBtn)
        order_layout.addWidget(self.sellBtn)
        order_layout.addWidget(self.quantitySpinBox)
        order_layout.addWidget(self.priceEdit)
        order_layout.addWidget(self.changeMarketComboBox)
        mode_layout.addWidget(self.current_price)
        mode_layout.addWidget(self.historicalLabel)
        mode_layout.addWidget(self.historicalComboBox)
        mode_layout.addWidget(self.realtimeBtn)
        mode_layout.addWidget(self.stopBtn)
        parent_layout.addWidget(self.tickerEdit)
        parent_layout.addLayout(mode_layout)
        parent_layout.addLayout(order_layout)

    def setup_chart_widget(self, parent_layout):
        self.plotWidget = QWebEngineView(self.tab_chart)
        self.plotWidget.setMinimumHeight(400)
        self.plotWidget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        class ChartBridge(QObject):
            def __init__(self, main_window):
                super().__init__()
                self.main_window = main_window
        self.chart_bridge = ChartBridge(self)
        self.channel = QWebChannel()
        self.channel.registerObject("pyObject", self.chart_bridge)
        self.plotWidget.page().setWebChannel(self.channel)
        self.plotWidget.setHtml(self._get_empty_chart_html())
        parent_layout.addWidget(self.plotWidget, 1)

    def setup_settings_tab(self):
        main_layout = QVBoxLayout(self.tab_settings)
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(25, 25, 25, 25)
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setStyleSheet(styles.DARK_THEME["splitter"])
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setSpacing(15)
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setSpacing(15)
        self.setup_accounts_settings(left_layout)
        self.setup_portfolio_settings(left_layout)
        self.setup_notification_settings(left_layout)
        self.setup_system_settings(right_layout)
        self.setup_strategy_settings(right_layout)
        self.setup_utility_buttons(right_layout)
        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)
        main_layout.addWidget(splitter)
        splitter.setSizes([400, 400])
        self.load_settings()

    def setup_accounts_settings(self, parent_layout):
        accounts_group = QGroupBox("Account management")
        accounts_group.setStyleSheet(styles.DARK_THEME["group_box"])
        accounts_layout = QVBoxLayout(accounts_group)
        accounts_btn_layout = QHBoxLayout()
        self.accounts_btn = QPushButton("Account settings")
        self.accounts_btn.setStyleSheet(styles.DARK_THEME["button_secondary"])
        self.accounts_btn.clicked.connect(self.open_accounts_window)
        self.export_accounts_btn = QPushButton("Account export")
        self.export_accounts_btn.setStyleSheet(styles.DARK_THEME["button_secondary"])
        self.export_accounts_btn.clicked.connect(self.export_accounts)
        accounts_btn_layout.addWidget(self.accounts_btn)
        accounts_btn_layout.addWidget(self.export_accounts_btn)
        accounts_layout.addLayout(accounts_btn_layout)
        current_account_layout = QHBoxLayout()
        current_account_label = QLabel("Current account:")
        current_account_label.setStyleSheet(styles.DARK_THEME["label_primary"])
        current_account_layout.addWidget(current_account_label)
        self.current_account_label = QLabel("Not connected")
        self.current_account_label.setStyleSheet(styles.DARK_THEME["label_accent"])
        current_account_layout.addWidget(self.current_account_label, 1)
        accounts_layout.addLayout(current_account_layout)
        parent_layout.addWidget(accounts_group)

    def setup_portfolio_settings(self, parent_layout):
        chart_group = QGroupBox("Graph settings")
        chart_group.setStyleSheet(styles.DARK_THEME["group_box"])
        chart_layout = QGridLayout(chart_group)
        chart_layout.setVerticalSpacing(10)
        chart_layout.setHorizontalSpacing(15)
        theme_label = QLabel("Theme:")
        theme_label.setStyleSheet(styles.DARK_THEME["label_primary"])
        chart_layout.addWidget(theme_label, 0, 0)
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Dark", "Light"])
        self.theme_combo.setStyleSheet(styles.DARK_THEME["combo_box"])
        self.theme_combo.currentTextChanged.connect(self.change_theme)
        chart_layout.addWidget(self.theme_combo, 0, 1)
        self.show_grid = QCheckBox("Show grid")
        self.show_grid.setStyleSheet(styles.DARK_THEME["checkbox"])
        self.show_grid.setChecked(False)
        self.show_grid.setEnabled(False)
        chart_layout.addWidget(self.show_grid, 2, 0, 1, 2)
        self.show_volume = QCheckBox("Show volume")
        self.show_volume.setStyleSheet(styles.DARK_THEME["checkbox"])
        self.show_volume.setChecked(False)
        self.show_volume.setEnabled(False)
        chart_layout.addWidget(self.show_volume, 3, 0, 1, 2)
        self.auto_refresh_portfolio = QCheckBox("Auto refresh portfolio")
        self.auto_refresh_portfolio.setStyleSheet(styles.DARK_THEME["checkbox"])
        self.auto_refresh_portfolio.setChecked(True)
        self.auto_refresh_portfolio.toggled.connect(self.on_auto_refresh_changed)
        chart_layout.addWidget(self.auto_refresh_portfolio, 4, 0, 1, 2)
        refresh_label = QLabel("Refresh interval:")
        refresh_label.setStyleSheet(styles.DARK_THEME["label_primary"])
        chart_layout.addWidget(refresh_label, 5, 0)
        self.refresh_interval = QSpinBox()
        self.refresh_interval.setStyleSheet(styles.DARK_THEME["spinbox"])
        self.refresh_interval.setRange(1, 9999)
        self.refresh_interval.setValue(60)
        self.refresh_interval.setSuffix(" сек")
        self.auto_refresh_portfolio.toggled.connect(self.refresh_interval.setEnabled)
        self.refresh_interval.valueChanged.connect(self.on_refresh_interval_changed)
        chart_layout.addWidget(self.refresh_interval, 5, 1)
        parent_layout.addWidget(chart_group)

    def setup_notification_settings(self, parent_layout):
        notifications_group = QGroupBox("Notifications")
        notifications_group.setStyleSheet(styles.DARK_THEME["group_box"])
        notifications_layout = QVBoxLayout(notifications_group)
        notifications_layout.setSpacing(10)
        telegram_layout = QHBoxLayout()
        self.enable_telegram_notifications = QCheckBox("Telegram notifications")
        self.enable_telegram_notifications.setStyleSheet(styles.DARK_THEME["checkbox"])
        self.enable_telegram_notifications.setChecked(False)
        telegram_layout.addWidget(self.enable_telegram_notifications)
        self.telegram_token_edit = QLineEdit()
        self.telegram_token_edit.setPlaceholderText("Bot token")
        self.telegram_token_edit.setStyleSheet(styles.DARK_THEME["line_edit"])
        self.telegram_token_edit.setEnabled(False)
        self.enable_telegram_notifications.toggled.connect(self.telegram_token_edit.setEnabled)
        self.telegram_chat_id = QLineEdit()
        self.telegram_chat_id.setPlaceholderText("Chat ID")
        self.telegram_chat_id.setStyleSheet(styles.DARK_THEME["line_edit"])
        self.telegram_chat_id.setEnabled(False)
        self.enable_telegram_notifications.toggled.connect(self.telegram_chat_id.setEnabled)
        telegram_layout.addWidget(self.telegram_token_edit)
        telegram_layout.addWidget(self.telegram_chat_id)
        notifications_layout.addLayout(telegram_layout)
        test_notifications_btn = QPushButton("Test notifications")
        test_notifications_btn.setStyleSheet(styles.DARK_THEME["button_secondary"])
        test_notifications_btn.clicked.connect(self.test_notifications)
        notifications_layout.addWidget(test_notifications_btn)
        parent_layout.addWidget(notifications_group)

    def setup_system_settings(self, parent_layout):
        system_group = QGroupBox("System settings")
        system_group.setStyleSheet(styles.DARK_THEME["group_box"])
        system_layout = QVBoxLayout(system_group)
        system_layout.setSpacing(10)
        self.auto_start = QCheckBox("Start on system start")
        self.auto_start.setStyleSheet(styles.DARK_THEME["checkbox"])
        self.auto_start.setChecked(False)
        system_layout.addWidget(self.auto_start)
        self.minimize_to_tray = QCheckBox("Minimize to tray")
        self.minimize_to_tray.setStyleSheet(styles.DARK_THEME["checkbox"])
        self.minimize_to_tray.setChecked(True)
        system_layout.addWidget(self.minimize_to_tray)
        log_level_layout = QHBoxLayout()
        log_level_label = QLabel("Log level:")
        log_level_label.setStyleSheet(styles.DARK_THEME["label_primary"])
        log_level_layout.addWidget(log_level_label)
        self.log_level_combo = QComboBox()
        self.log_level_combo.addItems(["DEBUG", "INFO", "WARNING", "ERROR"])
        self.log_level_combo.setStyleSheet(styles.DARK_THEME["combo_box"])
        self.log_level_combo.currentTextChanged.connect(self.set_log_level)
        log_level_layout.addWidget(self.log_level_combo)
        system_layout.addLayout(log_level_layout)
        parent_layout.addWidget(system_group)

    def setup_strategy_settings(self, parent_layout):
        strategies_config_group = QGroupBox("Strategies config")
        strategies_config_group.setStyleSheet(styles.DARK_THEME["group_box"])
        strategies_config_group.setEnabled(False)
        strategies_config_layout = QVBoxLayout(strategies_config_group)
        strategies_config_layout.setSpacing(10)
        self.testing_mode = QCheckBox("Testing mode")
        self.testing_mode.setStyleSheet(styles.DARK_THEME["checkbox"])
        self.testing_mode.setChecked(True)
        strategies_config_layout.addWidget(self.testing_mode)
        self.auto_start_strategy = QCheckBox("Auto start strategy")
        self.auto_start_strategy.setStyleSheet(styles.DARK_THEME["checkbox"])
        self.auto_start_strategy.setChecked(False)
        strategies_config_layout.addWidget(self.auto_start_strategy)
        self.allow_parallel_strategies = QCheckBox("Allow parallel strategies")
        self.allow_parallel_strategies.setStyleSheet(styles.DARK_THEME["checkbox"])
        self.allow_parallel_strategies.setChecked(False)
        strategies_config_layout.addWidget(self.allow_parallel_strategies)
        max_trades_layout = QHBoxLayout()
        max_trades_label = QLabel("Max daily trades:")
        max_trades_label.setStyleSheet(styles.DARK_THEME["label_primary"])
        max_trades_layout.addWidget(max_trades_label)
        self.max_daily_trades = QSpinBox()
        self.max_daily_trades.setStyleSheet(styles.DARK_THEME["spinbox"])
        self.max_daily_trades.setRange(1, 1000)
        self.max_daily_trades.setValue(50)
        max_trades_layout.addWidget(self.max_daily_trades)
        max_trades_layout.addStretch()
        strategies_config_layout.addLayout(max_trades_layout)
        trade_interval_layout = QHBoxLayout()
        trade_interval_label = QLabel("Min trade interval:")
        trade_interval_label.setStyleSheet(styles.DARK_THEME["label_primary"])
        trade_interval_layout.addWidget(trade_interval_label)
        self.min_trade_interval = QSpinBox()
        self.min_trade_interval.setStyleSheet(styles.DARK_THEME["spinbox"])
        self.min_trade_interval.setRange(1, 3600)
        self.min_trade_interval.setValue(60)
        self.min_trade_interval.setSuffix(" sec")
        trade_interval_layout.addWidget(self.min_trade_interval)
        trade_interval_layout.addStretch()
        strategies_config_layout.addLayout(trade_interval_layout)
        parent_layout.addWidget(strategies_config_group)

    def setup_utility_buttons(self, parent_layout):
        info_group = QGroupBox("Settings functions")
        info_group.setStyleSheet(styles.DARK_THEME["group_box"])
        info_layout = QVBoxLayout(info_group)
        info_layout.setSpacing(8)
        buttons_layout = QHBoxLayout()
        save_btn = QPushButton("Save settings")
        save_btn.setStyleSheet(styles.DARK_THEME["button_secondary"])
        save_btn.clicked.connect(self.save_settings)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setStyleSheet(styles.DARK_THEME["button_secondary"])
        cancel_btn.clicked.connect(self.cancel_changes)
        reset_btn = QPushButton("Reset")
        reset_btn.setStyleSheet(styles.DARK_THEME["button_secondary"])
        reset_btn.clicked.connect(self.reset_settings)
        buttons_layout.addWidget(save_btn)
        buttons_layout.addWidget(cancel_btn)
        buttons_layout.addWidget(reset_btn)
        info_layout.addLayout(buttons_layout)
        actions_layout = QHBoxLayout()
        backup_btn = QPushButton("Backup")
        backup_btn.setStyleSheet(styles.DARK_THEME["button_secondary"])
        backup_btn.clicked.connect(self.create_backup)
        export_logs_btn = QPushButton("Export logs")
        export_logs_btn.setStyleSheet(styles.DARK_THEME["button_secondary"])
        export_logs_btn.clicked.connect(self.export_logs)
        actions_layout.addWidget(backup_btn)
        actions_layout.addWidget(export_logs_btn)
        info_layout.addLayout(actions_layout)
        parent_layout.addWidget(info_group)

    def setup_workers(self):
        self.thread = QThread(self)
        self.worker = ApiWorker()
        self.worker.moveToThread(self.thread)
        self.worker.connected.connect(self.connected)
        self.worker.error.connect(self.on_api_error)
        self.worker.portfolioData.connect(self.update_portfolio_ui)
        self.worker.historicalPricesLoaded.connect(self.on_historical_prices_loaded)
        self.requestConnect.connect(self.worker.connect_api)
        self.requestFetchPortfolio.connect(self.worker.fetch_portfolio)
        self.thread.start()
        self.streamWorker = MarketStreamWorker()
        self.tradeWorker = TradeWorker()
        self.tradeWorker.moveToThread(self.thread)
        self.tradeWorker.order_placed.connect(self.on_order_placed)
        self.tradeWorker.order_error.connect(self.on_order_error)

    def setup_tray_icon(self):
        if not QSystemTrayIcon.isSystemTrayAvailable():
            return
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(self.style().standardIcon(self.style().StandardPixmap.SP_ComputerIcon))
        tray_menu = QMenu()
        show_action = QAction("Показать", self)
        show_action.triggered.connect(self.show_from_tray)
        tray_menu.addAction(show_action)
        tray_menu.addSeparator()
        exit_action = QAction("Выход", self)
        exit_action.triggered.connect(self.close_application)
        tray_menu.addAction(exit_action)
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self.tray_icon_activated)
        self.tray_icon.show()

    def get_token(self):
        manual_token = self.tokenEdit.text().strip()
        if manual_token:
            if self.worker.check_token(manual_token):
                return manual_token
        if self.accounts.currentText():
            account_token = account.get_account_token(self.accounts.currentText())
            if account_token and self.worker.check_token(account_token):
                return account_token
        return None

    def connect_clicked(self):
        token = self.tokenEdit.text().strip()
        if token:
            self.current_account_label.setText("Ручной ввод токена")
        self.worker.set_token(token)
        self.statusLabel.setText("Подключение...")
        self.requestConnect.emit()

    def account_changed(self, index):
        if hasattr(self, 'ignore_account_signal') and self.ignore_account_signal:
            return
        if not hasattr(self, 'worker') or self.worker is None:
            return
        if index == -1:
            self.current_account_label.setText("Не выбран") 
            return
        account_name = self.accounts.currentText()
        token = account.get_account_token(account_name)
        if not token:
            self.current_account_label.setText("Не выбран")
            return
        self.current_account_label.setText(account_name) 
        self.accounts.setEnabled(False)
        self.log.clear()
        self.worker.set_token(token)
        self.statusLabel.setText("Подключение...")
        self.requestConnect.emit()

    def refresh_accounts_list(self):
        self.ignore_account_signal = True
        self.accounts.clear()
        accounts = account.load_accounts()
        for name in accounts.keys():
            self.accounts.addItem(name)
        self.accounts.setCurrentIndex(-1)
        self.current_account_label.setText("Не выбран")
        self.ignore_account_signal = False

    def connected(self, message):
        self.statusLabel.setText("Подключено")
        self.append_log(message)
        self.tabs.setTabVisible(self.portfolio_index, True)
        self.tabs.setTabVisible(self.strategy_index, True)
        self.tabs.setTabVisible(self.chart_index, True)
        self.requestFetchPortfolio.emit()
        if self.accounts.currentText():
            self.current_account_label.setText(f"{self.accounts.currentText()} ✓")

    def on_api_error(self, message):
        if "Ошибка загрузки истории" in message or "Получено 0 свечей" in message or "Не удалось извлечь цены" in message or "Инструмент с тикером" in message:
            self.append_log(message)
        else:
            self.statusLabel.setText("Ошибка")
            self.append_log(message)
            self.tabs.setTabVisible(self.portfolio_index, False)
            self.tabs.setTabVisible(self.strategy_index, False)
            self.tabs.setTabVisible(self.chart_index, False)
            self.accounts.setEnabled(True)
            self.current_account_label.setText("Ошибка подключения")
            self.accounts.setCurrentIndex(-1)

    def update_portfolio_ui(self, data):
        self.totalAmountLabel.setText(f"Total cost: {data['total_amount']:,.2f} {data['currency']}")
        self.positionsCountLabel.setText(f"Positions: {data['total_positions_count']}")
        self.accountIdLabel.setText(f"Account ID: {data['account_id']}")
        positions = data['positions']
        self.update_positions_table(positions)
        if positions:
            self.update_pie_chart(positions)
        self.accounts.setEnabled(True)
        self.setup_portfolio_refresh_timer()

    def on_auto_refresh_changed(self, checked):
        if checked:
            self.setup_portfolio_refresh_timer()
        else:
            if hasattr(self, 'portfolio_refresh_timer'):
                self.portfolio_refresh_timer.stop()

    def on_refresh_interval_changed(self, value):
        self.setup_portfolio_refresh_timer()

    def setup_portfolio_refresh_timer(self):
        try:
            if hasattr(self, 'portfolio_refresh_timer'):
                self.portfolio_refresh_timer.stop()
                try:
                    self.portfolio_refresh_timer.timeout.disconnect()
                except:
                    pass
            if (hasattr(self, 'auto_refresh_portfolio') and 
                self.auto_refresh_portfolio.isChecked() and
                hasattr(self, 'refresh_interval')):
                interval = self.refresh_interval.value() * 1000
                if interval > 0:
                    self.portfolio_refresh_timer.timeout.connect(self.refresh_portfolio)
                    self.portfolio_refresh_timer.start(interval)
        except:
            pass
    
    def refresh_portfolio(self):
        if hasattr(self, 'worker') and self.worker and self.worker.token:
            self.requestFetchPortfolio.emit()
        else:
            if hasattr(self, 'portfolio_refresh_timer'):
                self.portfolio_refresh_timer.stop()
    
    def update_positions_table(self, positions):
        self.positionsTable.setSortingEnabled(False)
        self.positionsTable.setRowCount(len(positions))
        for row, pos in enumerate(positions):
            self.positionsTable.setItem(row, 0, QTableWidgetItem(pos['name']))
            quantity_item = QTableWidgetItem()
            quantity_item.setData(Qt.ItemDataRole.DisplayRole, float(pos['quantity']))
            self.positionsTable.setItem(row, 1, quantity_item)
            price_item = QTableWidgetItem()
            price_item.setData(Qt.ItemDataRole.DisplayRole, float(pos['price']))
            self.positionsTable.setItem(row, 2, price_item)
            cost_item = QTableWidgetItem()
            cost_item.setData(Qt.ItemDataRole.DisplayRole, float(pos['value']))
            self.positionsTable.setItem(row, 3, cost_item)
            self.positionsTable.setItem(row, 4, QTableWidgetItem(pos['currency']))
            self.positionsTable.setItem(row, 5, QTableWidgetItem(pos['ticker']))
            self.positionsTable.setItem(row, 6, QTableWidgetItem(pos['uid'][:20] if pos['uid'] else ''))
        self.positionsTable.setSortingEnabled(True)

    def update_pie_chart(self, positions):
        if not positions:
            return
        categories = {}
        for pos in positions:
            category = pos.get('category', 'Другое')
            if category not in categories:
                categories[category] = 0
            categories[category] += float(pos['value'])
        sorted_categories = sorted(categories.items(), key=lambda x: x[1], reverse=True)
        labels = [cat[0] for cat in sorted_categories]
        values = [cat[1] for cat in sorted_categories]
        colors = [CATEGORY_COLORS.get(cat, '#D5D5D5') for cat in labels]
        if hasattr(self, 'pieChart') and self.pieChart:
            try:
                js_code = f"""
                if (typeof window.updatePortfolioChart === 'function') {{
                    window.updatePortfolioChart(
                        {json.dumps(labels)},
                        {json.dumps(values)},
                        {json.dumps(colors)}
                    );
                }}
                """
                self.pieChart.page().runJavaScript(js_code)
            except:
                pass

    def convert_price_to_candles(self, price_data):
        if not price_data:
            return []
        
        candles = []
        
        for i in range(0, len(price_data), 4):
            if i + 3 >= len(price_data):
                break
                
            timestamp1, price1 = price_data[i]
            timestamp2, price2 = price_data[i + 1]
            timestamp3, price3 = price_data[i + 2]
            timestamp4, price4 = price_data[i + 3]
            
            candle = {
                'time': timestamp1,
                'open': price1,
                'high': max(price1, price2, price3, price4),
                'low': min(price1, price2, price3, price4),
                'close': price4
            }
            candles.append(candle)
        
        return candles

    def load_historical_data(self, days=30):
        self.streamWorker.stop_stream()
        if days == 'Всё':
            days = 365
        else:
            days = int(days)
        
        if days <= 7:
            interval = '1hour'
        elif days <= 30:
            interval = '4hour'
        elif days <= 90:
            interval = '1day'
        else:
            interval = '1day'
        
        if hasattr(self, 'worker') and self.worker:
            token = self.worker.token
        else:
            if ApiWorker.check_token(self.tokenEdit.text().strip()):
                token = self.tokenEdit.text().strip()
            elif ApiWorker.check_token(account.get_account_token(self.accounts.currentText())):
                token = account.get_account_token(self.accounts.currentText())
            else:
                return
    
        ticker = self.tickerEdit.text().strip()
        
        if not ticker or not token:
            return

        self.current_ticker = ticker
        self.current_token = token
        self.is_loading_history = True
        self.stream_auto_reconnect = False
        
        if hasattr(self, 'worker') and self.worker:
            self.worker.set_token(token)
            self.worker.fetch_historical_prices(ticker, days=days, interval=interval)

    def start_stream(self):
        token = self.get_token()
        ticker = self.tickerEdit.text().strip()
        
        if not ticker or not token:
            return

        self.current_ticker = ticker
        self.current_token = token
        self.candles = []
        self.current_candle = None
        self.last_candle_time = None
        self.is_loading_history = True
        self.stream_auto_reconnect = True
        
        if hasattr(self, 'worker') and self.worker:
            self.worker.set_token(token)
            self.pending_stream_ticker = ticker
            self.pending_stream_token = token
            self.worker.fetch_historical_prices(ticker, hours=6, interval='30sec')

    def stop_stream(self):
        self.stream_auto_reconnect = False
        if hasattr(self, 'streamWorker'):
            self.streamWorker.stop_stream()
        self.toggle_stream_ui(False)
        
        if self.active_strategy:
            self.active_strategy.reset()
            self.strategyStatusLabel.setText("Strategy stopped")
        
        self.candles.clear()
        self.current_candle = None
        self.last_candle_time = None
        self.chart_data.clear()
        
        if hasattr(self, 'plotWidget') and self.plotWidget:
            self.plotWidget.setHtml(self._get_empty_chart_html())
        
        self.append_log("Stream stopped - data cleared")

    def toggle_stream_ui(self, running):
        if hasattr(self, 'realtimeBtn'):
            self.realtimeBtn.setEnabled(not running)
        if hasattr(self, 'stopBtn'):
            self.stopBtn.setEnabled(running)

    def on_historical_prices_loaded(self, price_data):
        if not price_data:
            if self.pending_stream_ticker:
                self._delayed_stream_start()
            return
        
        is_ohlc = len(price_data[0]) == 5
        
        if self.pending_stream_ticker:
            self._process_stream_history(price_data, is_ohlc)
        elif self.is_loading_history:
            self._process_regular_history(price_data, is_ohlc)

    def _process_regular_history(self, price_data, is_ohlc):
        try:
            if is_ohlc:
                candles = []
                for ts, o, h, l, c in price_data:
                    candles.append({
                        'time': ts,
                        'open': o,
                        'high': h,
                        'low': l,
                        'close': c
                    })
                self.candles = candles
            else:
                candles = self.convert_price_to_candles(price_data)
                self.candles = candles
            
            if candles:
                self._update_candlestick_chart()
            
            self.is_loading_history = False
            
        except:
            self.is_loading_history = False

    def _process_stream_history(self, price_data, is_ohlc):
        try:
            if not price_data:
                return
            
            if is_ohlc:
                candles = self.convert_5sec_to_1min(price_data)
                self.candles = candles
            else:
                candles = self.convert_history_to_candles(price_data)
                self.candles = candles
            
            if candles:
                self._update_candlestick_chart()
            
            self._delayed_stream_start()
            
        except:
            pass

    def _delayed_stream_start(self):
        try:
            if not self.pending_stream_ticker or not self.pending_stream_token:
                return
            
            self.start_stream_internal(self.pending_stream_ticker, self.pending_stream_token)
            self.pending_stream_ticker = None
            self.pending_stream_token = None
            
        except:
            pass

    def start_stream_internal(self, ticker, token):
        if not self.worker.check_token(token):
            self.toggle_stream_ui(False)
            return
        
        self.disconnect_stream_signals()
        
        self.streamWorker.set_token(token)
        self.streamWorker.candle.connect(self.candle)
        self.streamWorker.error.connect(self.append_log)
        self.streamWorker.started.connect(self.on_stream_started)
        self.streamWorker.stopped.connect(self.on_stream_stopped)

        self.current_ticker = ticker
        self.current_token = token
        self.stream_auto_reconnect = True
        
        self.streamWorker.start_stream(ticker, 'Now')

    def disconnect_stream_signals(self):
        signals = ['candle', 'error', 'started', 'stopped']
        for signal in signals:
            try:
                getattr(self.streamWorker, signal).disconnect()
            except:
                pass

    def on_stream_started(self):
        self.toggle_stream_ui(True)
        self.update_order_layout('ON')

    def on_stream_stopped(self):
        self.toggle_stream_ui(False)
        if self.stream_auto_reconnect and self.current_ticker and self.current_token:
            QTimer.singleShot(self.stream_reconnect_delay * 1000, self._reconnect_stream)
        self.update_order_layout('OFF')

    def _reconnect_stream(self):
        if self.stream_auto_reconnect and self.current_ticker and self.current_token:
            self.start_stream_internal(self.current_ticker, self.current_token)

    def candle(self, price):
        if price <= 0:
            return

        current_time = datetime.now(timezone.utc)
        current_minute = current_time.replace(second=0, microsecond=0)
        current_timestamp = int(current_minute.timestamp())
        
        if self.last_candle_time != current_timestamp:
            if self.current_candle:
                self.candles.append(self.current_candle)
                if len(self.candles) > 500:
                    self.candles.pop(0)
                self._update_candlestick_chart()
            
            self.current_candle = {
                'time': current_timestamp,
                'open': price,
                'high': price,
                'low': price,
                'close': price
            }
            self.last_candle_time = current_timestamp
        else:
            if self.current_candle:
                self.current_candle['high'] = max(self.current_candle['high'], price)
                self.current_candle['low'] = min(self.current_candle['low'], price)
                self.current_candle['close'] = price
                self._update_candlestick_chart()
        
        if self.active_strategy:
            self.active_strategy.add_price(price)
            self.process_strategy_signal(price)
        
        self.current_price.setText(f"Текущая цена: {price:.2f}")

    def _update_candlestick_chart(self):
        display_candles = self.candles.copy() if self.candles else []
        
        if hasattr(self, 'current_candle') and self.current_candle:
            display_candles.append(self.current_candle)
        
        if not display_candles:
            return
        
        if hasattr(self, 'plotWidget') and self.plotWidget:
            try:
                chart_data = []
                for candle in display_candles:
                    chart_data.append([
                        int(candle['time']) * 1000,
                        float(candle['open']),
                        float(candle['close']), 
                        float(candle['low']),
                        float(candle['high'])
                    ])
                
                js_code = f"""
                if (typeof window.updateCandlestickChart === 'function') {{
                    window.updateCandlestickChart({json.dumps(chart_data)});
                }}
                """
                self.plotWidget.page().runJavaScript(js_code)
            except:
                pass

    def convert_history_to_candles(self, price_data):
        if not price_data:
            return []
        
        candles = []
        current_candle = None
        
        sorted_data = sorted(price_data, key=lambda x: x[0])
        
        for timestamp, price in sorted_data:
            candle_time = datetime.fromtimestamp(timestamp, timezone.utc).replace(second=0, microsecond=0)
            candle_timestamp = int(candle_time.timestamp())
            
            if current_candle is None or current_candle['time'] != candle_timestamp:
                if current_candle is not None:
                    candles.append(current_candle)
                
                current_candle = {
                    'time': candle_timestamp,
                    'open': price,
                    'high': price,
                    'low': price,
                    'close': price
                }
            else:
                current_candle['high'] = max(current_candle['high'], price)
                current_candle['low'] = min(current_candle['low'], price)
                current_candle['close'] = price
        
        if current_candle is not None:
            candles.append(current_candle)
        
        return candles

    def convert_5sec_to_1min(self, five_sec_data):
        if not five_sec_data:
            return []
        
        candles_1min = []
        current_minute_data = []
        current_minute_timestamp = None
        
        sorted_data = sorted(five_sec_data, key=lambda x: x[0])
        
        for ts, o, h, l, c in sorted_data:
            candle_time = datetime.fromtimestamp(ts, timezone.utc).replace(second=0, microsecond=0)
            minute_timestamp = int(candle_time.timestamp())
            
            if current_minute_timestamp is None:
                current_minute_timestamp = minute_timestamp
            
            if minute_timestamp != current_minute_timestamp:
                if current_minute_data:
                    minute_candle = self._create_minute_candle(current_minute_data, current_minute_timestamp)
                    candles_1min.append(minute_candle)
                
                current_minute_data = []
                current_minute_timestamp = minute_timestamp
            
            current_minute_data.append({
                'timestamp': ts,
                'open': o,
                'high': h, 
                'low': l,
                'close': c
            })
        
        if current_minute_data:
            minute_candle = self._create_minute_candle(current_minute_data, current_minute_timestamp)
            candles_1min.append(minute_candle)
        
        return candles_1min

    def _create_minute_candle(self, five_sec_candles, minute_timestamp):
        if not five_sec_candles:
            return None
        
        open_price = five_sec_candles[0]['open']
        high_price = max(candle['high'] for candle in five_sec_candles)
        low_price = min(candle['low'] for candle in five_sec_candles)
        close_price = five_sec_candles[-1]['close']
        
        return {
            'time': minute_timestamp,
            'open': open_price,
            'high': high_price,
            'low': low_price,
            'close': close_price
        }

    def send_order(self, order):
        self.tradeWorker.set_token(self.get_token())
        ticker = self.tickerEdit.text().strip()
        quantity = self.quantitySpinBox.value()
        if self.changeMarketComboBox.currentText() == 'Limit':
            try:
                price = int(self.priceEdit.text())
            except ValueError:
                return
            if order == 'BUY':
                self.tradeWorker.place_limit_order(ticker, 'BUY', quantity, price)
            if order == 'SELL':
                self.tradeWorker.place_limit_order(ticker, 'SELL', quantity, price)
        else:
            if order == 'BUY':
                self.tradeWorker.place_market_order(ticker, 'BUY', quantity)
            if order == 'SELL':
                self.tradeWorker.place_market_order(ticker, 'SELL', quantity)

    def change_market_type(self):
        if self.changeMarketComboBox.currentText() == 'Market':
            self.priceEdit.setEnabled(False)
        else:
            self.priceEdit.setEnabled(True)

    def update_order_layout(self, status):
        if status == 'ON':
            self.sellBtn.setEnabled(True)
            self.buyBtn.setEnabled(True)
            self.quantitySpinBox.setEnabled(True)
            self.changeMarketComboBox.setEnabled(True)
            if self.changeMarketComboBox.currentText() == 'Market':
                self.priceEdit.setEnabled(False)
            else:
                self.priceEdit.setEnabled(True)
        else:
            self.sellBtn.setEnabled(False)
            self.buyBtn.setEnabled(False)
            self.quantitySpinBox.setEnabled(False)
            self.priceEdit.setEnabled(False)
            self.changeMarketComboBox.setEnabled(False)

    def strategy_changed(self):
        from strategies.advanced_strategy import CostAwareSmartStrategy

        strategy_name = self.strategyCombo.currentText()
        if strategy_name == " Выберите стратегию ":
            self.reset_strategy()
            return

        elif strategy_name == "Advanced Strategy":
            self.active_strategy = CostAwareSmartStrategy()
            self.paramsLabel.setText("Advanced Strategy")

        self.sync_strategy_with_chart_data(strategy_name)

    def reset_strategy(self):
        self.active_strategy = None
        self.paramsLabel.setText("Не выбрано")
        self.strategyStatusLabel.setText("Стратегия не выбрана")
        self.strategySignalsLog.clear()

    def sync_strategy_with_chart_data(self, strategy_name):
        if self.active_strategy and len(self.candles) > 0:
            for candle in self.candles:
                self.active_strategy.add_price(candle['close'])
            
            price_count = len(self.candles)
            min_required = STRATEGY_PARAMS.get(strategy_name, {}).get("min_prices", 0)
            
            if price_count < min_required:
                self.strategyStatusLabel.setText(f"Стратегия '{strategy_name}' загружена | Данных: {price_count}/{min_required} | Запустите стрим")
            else:
                self.strategyStatusLabel.setText(f"Стратегия '{strategy_name}' загружена | Данных: {price_count} | Готова к анализу")
        else:
            min_required = STRATEGY_PARAMS.get(strategy_name, {}).get("min_prices", 0)
            self.strategyStatusLabel.setText(f"Стратегия '{strategy_name}' загружена | Нужно данных: {min_required} | Запустите стрим")
        
        self.strategySignalsLog.clear()
        self.strategySignalsLog.append(f"Активирована стратегия: {strategy_name}")
        self.strategySignalsLog.append("Стратегия готова анализировать цены из стрима")

    def process_strategy_signal(self, price):
        signal = self.active_strategy.analyze(price)
        indicators = self.active_strategy.get_indicator_values()
        price_count = len(self.active_strategy.price_history)

        if signal:
            real_price = apply_broker_commission(price, signal)
            signal_text = f"Сигнал {signal} | Бирж. цена: {price:.2f} | С комиссией: {real_price:.2f}"
            self.strategySignalsLog.append(signal_text)
            self.update_strategy_status_with_signal(signal, indicators, price_count)
            self.update_signal_statistics(signal)
            self.show_signal_recommendation(signal, price)
        else:
            self.update_strategy_status_no_signal(indicators, price_count)

    def update_signal_statistics(self, signal):
        if not hasattr(self, 'signal_stats'):
            self.signal_stats = {'BUY': 0, 'SELL': 0, 'total': 0}
        
        self.signal_stats[signal] = self.signal_stats.get(signal, 0) + 1
        self.signal_stats['total'] = self.signal_stats.get('total', 0) + 1
        
        if hasattr(self, 'signalStatsLabel'):
            buy_count = self.signal_stats.get('BUY', 0)
            sell_count = self.signal_stats.get('SELL', 0)
            total_count = self.signal_stats.get('total', 0)
            self.signalStatsLabel.setText(f"Статистика: BUY: {buy_count}, SELL: {sell_count}, Всего: {total_count}")

    def show_signal_recommendation(self, signal, price):
        recommendation = ""
        if signal == "BUY":
            real_price = apply_broker_commission(price, 'BUY')
            commission = real_price - price
            recommendation = f"   🟢 Рассмотрите возможность покупки.\n   Биржевая цена: {price:.2f}\n   Цена с комиссией ({BROKER_COMMISSION*100:.3f}%): {real_price:.2f} (+{commission:.2f})"
        elif signal == "SELL":
            real_price = apply_broker_commission(price, 'SELL')
            commission = price - real_price
            recommendation = f"   🔴 Рассмотрите возможность продажи.\n   Биржевая цена: {price:.2f}\n   Цена с комиссией ({BROKER_COMMISSION*100:.3f}%): {real_price:.2f} (-{commission:.2f})"
        
        if recommendation:
            self.strategySignalsLog.append(f"\n{recommendation}\n")
            if self.enable_telegram_notifications.isChecked():
                send_signal(recommendation, self.telegram_token_edit.text(), self.telegram_chat_id.text())

    def update_strategy_status_with_signal(self, signal, indicators, price_count):
        if indicators:
            key_indicators = []
            if 'RSI' in indicators: key_indicators.append(f"RSI:{indicators['RSI']:.0f}")
            if 'EMA Fast' in indicators: key_indicators.append(f"EMA:{indicators['EMA Fast']:.1f}")
            if 'MACD' in indicators: key_indicators.append(f"MACD:{indicators['MACD']:.2f}")
            if 'Regime' in indicators: key_indicators.append(indicators['Regime'][:3])
            
            ind_str = " ".join(key_indicators[:3])
            
            if signal == "BUY":
                self.strategyStatusLabel.setStyleSheet(styles.STRATEGY_STYLES["status_label_buy"])
                status_text = f"🟢 BUY | {price_count} prices | {ind_str}"
            else:
                self.strategyStatusLabel.setStyleSheet(styles.STRATEGY_STYLES["status_label_sell"])
                status_text = f"🔴 SELL | {price_count} prices | {ind_str}"
            
            self.strategyStatusLabel.setText(status_text)

    def update_strategy_status_no_signal(self, indicators, price_count):
        strategy_name = self.active_strategy.name if self.active_strategy else ""
        min_required = STRATEGY_PARAMS.get(strategy_name, {}).get("min_prices", 0)

        if indicators:
            key_indicators = []
            if 'RSI' in indicators: key_indicators.append(f"RSI:{indicators['RSI']:.0f}")
            if 'EMA Fast' in indicators: key_indicators.append(f"EMA:{indicators['EMA Fast']:.1f}")
            if 'Regime' in indicators: key_indicators.append(indicators['Regime'][:3])
            
            ind_str = " ".join(key_indicators[:2])
            
            self.strategyStatusLabel.setStyleSheet(styles.STRATEGY_STYLES["status_label_active"])
            
            if price_count < min_required:
                status_text = f"⏳ Collecting: {price_count}/{min_required} | {ind_str}"
            else:
                status_text = f"📊 Active: {price_count} prices | {ind_str}"
            
            self.strategyStatusLabel.setText(status_text)

    def save_settings(self):
        try:
            config = configparser.ConfigParser()
            config['chart'] = {
                'theme': self.theme_combo.currentText(),
                'show_grid': str(self.show_grid.isChecked()).lower(),
                'show_volume': str(self.show_volume.isChecked()).lower(),
                'auto_refresh_portfolio': str(self.auto_refresh_portfolio.isChecked()).lower(),
                'refresh_interval': str(self.refresh_interval.value())
            }
            config['notifications'] = {
                'enable_telegram': str(self.enable_telegram_notifications.isChecked()).lower(),
                'telegram_token': self.telegram_token_edit.text(),
                'telegram_chat_id': self.telegram_chat_id.text(),
            }
            config['system'] = {
                'auto_start': str(self.auto_start.isChecked()).lower(),
                'minimize_to_tray': str(self.minimize_to_tray.isChecked()).lower(),
                'log_level': self.log_level_combo.currentText(),
            }
            config['strategies'] = {
                'testing_mode': str(self.testing_mode.isChecked()).lower(),
                'auto_start_strategy': str(self.auto_start_strategy.isChecked()).lower(),
                'allow_parallel_strategies': str(self.allow_parallel_strategies.isChecked()).lower(),
                'max_daily_trades': str(self.max_daily_trades.value()),
                'min_trade_interval': str(self.min_trade_interval.value())
            }
            with open(self.SETTINGS_FILE, 'w', encoding='utf-8') as f:
                config.write(f)
            self.apply_settings()
            self.append_log("Настройки успешно сохранены")
        except:
            pass

    def load_settings(self):
        try:
            config = configparser.ConfigParser()
            if not os.path.exists(self.SETTINGS_FILE):
                self.create_default_settings()
                config.read(self.SETTINGS_FILE)
            else:
                config.read(self.SETTINGS_FILE)
            if config.has_section('chart'):
                theme = config.get('chart', 'theme', fallback='Темная')
                index = self.theme_combo.findText(theme)
                if index >= 0:
                    self.theme_combo.setCurrentIndex(index)
                self.show_grid.setChecked(config.getboolean('chart', 'show_grid', fallback=True))
                self.show_volume.setChecked(config.getboolean('chart', 'show_volume', fallback=True))
                self.auto_refresh_portfolio.setChecked(config.getboolean('chart', 'auto_refresh_portfolio', fallback=True))
                self.refresh_interval.setValue(config.getint('chart', 'refresh_interval', fallback=5))
            if config.has_section('notifications'):
                self.enable_telegram_notifications.setChecked(config.getboolean('notifications', 'enable_telegram', fallback=False))
                self.telegram_token_edit.setText(config.get('notifications', 'telegram_token', fallback=''))
                self.telegram_chat_id.setText(config.get('notifications', 'telegram_chat_id', fallback=''))
            if config.has_section('system'):
                self.auto_start.setChecked(config.getboolean('system', 'auto_start', fallback=False))
                self.minimize_to_tray.setChecked(config.getboolean('system', 'minimize_to_tray', fallback=True))
                log_level = config.get('system', 'log_level', fallback='INFO')
                index = self.log_level_combo.findText(log_level)
                if index >= 0:
                    self.log_level_combo.setCurrentIndex(index)
            if config.has_section('strategies'):
                self.testing_mode.setChecked(config.getboolean('strategies', 'testing_mode', fallback=True))
                self.auto_start_strategy.setChecked(config.getboolean('strategies', 'auto_start_strategy', fallback=False))
                self.allow_parallel_strategies.setChecked(config.getboolean('strategies', 'allow_parallel_strategies', fallback=False))
                self.max_daily_trades.setValue(config.getint('strategies', 'max_daily_trades', fallback=50))
                self.min_trade_interval.setValue(config.getint('strategies', 'min_trade_interval', fallback=60))
        except:
            pass

    def create_default_settings(self):
        try:
            config = configparser.ConfigParser()
            for section, settings in self.DEFAULT_SETTINGS.items():
                config[section] = settings
            with open(self.SETTINGS_FILE, 'w', encoding='utf-8') as f:
                config.write(f)
        except:
            pass

    def apply_settings(self):
        try:
            self.change_theme(self.theme_combo.currentText())
            self.setup_portfolio_refresh_timer()
            if self.auto_start.isChecked():
                self.setup_autostart()
            else:
                self.remove_autostart()
        except:
            pass

    def cancel_changes(self):
        self.load_settings()

    def reset_settings(self):
        try:
            if os.path.exists(self.SETTINGS_FILE):
                os.remove(self.SETTINGS_FILE)
            self.create_default_settings()
            self.load_settings()
        except:
            pass

    def setup_autostart(self):
        try:
            if os.name == 'nt':
                import winreg
                key = winreg.HKEY_CURRENT_USER
                subkey = r"Software\Microsoft\Windows\CurrentVersion\Run"
                with winreg.OpenKey(key, subkey, 0, winreg.KEY_SET_VALUE) as reg_key:
                    app_path = os.path.abspath(sys.argv[0])
                    winreg.SetValueEx(reg_key, "TinkoffAnalyzer", 0, winreg.REG_SZ, app_path)
        except:
            pass

    def remove_autostart(self):
        try:
            if os.name == 'nt':
                import winreg
                key = winreg.HKEY_CURRENT_USER
                subkey = r"Software\Microsoft\Windows\CurrentVersion\Run"
                with winreg.OpenKey(key, subkey, 0, winreg.KEY_SET_VALUE) as reg_key:
                    try:
                        winreg.DeleteValue(reg_key, "TinkoffAnalyzer")
                    except:
                        pass
        except:
            pass

    def change_theme(self, theme_name):
        try:
            from ui import styles
            if theme_name == "Light":
                self.theme = styles.LIGHT_THEME
            else:
                self.theme = styles.DARK_THEME
            self.apply_theme_to_widget(self, self.theme)
            styles.COMMON_STYLES = self.theme
            styles.ACCOUNT_STYLES = self.theme
            styles.PORTFOLIO_STYLES = self.theme
            styles.CHART_STYLES = self.theme
            styles.DIALOG_STYLES = self.theme
            self.setStyleSheet(self.theme["main_window"])
            self.tabs.setStyleSheet(self.theme["tab_widget"])
            for tab in [self.tab_account, self.tab_portfolio, self.tab_strategy, self.tab_chart, self.tab_settings]:
                tab.setStyleSheet(self.theme["widget"])
            self.update_widget_styles(self.theme)
        except:
            pass

    def apply_theme_to_widget(self, widget, theme):
        try:
            if hasattr(widget, 'setStyleSheet'):
                widget_type = type(widget).__name__
                if widget_type == 'QLineEdit':
                    widget.setStyleSheet(theme["line_edit"])
                elif widget_type == 'QPushButton':
                    if not hasattr(widget, 'border_animation'):
                        widget.setStyleSheet(theme["button_secondary"])
                elif widget_type == 'QComboBox':
                    if not hasattr(widget, 'border_animation'):
                        widget.setStyleSheet(theme["combo_box"])
                elif widget_type == 'QMainWindow':
                    widget.setStyleSheet(theme["main_window"])
                elif widget_type == 'QTextEdit':
                    widget.setStyleSheet(theme["text_edit"])
                elif widget_type == 'QListWidget':
                    widget.setStyleSheet(theme["list"])
                elif widget_type == 'QTableWidget':
                    widget.setStyleSheet(theme["table_widget"])
                elif widget_type == 'QGroupBox':
                    widget.setStyleSheet(theme["group_box"])
                elif widget_type == 'QCheckBox':
                    widget.setStyleSheet(theme["checkbox"])
                elif widget_type == 'QSpinBox':
                    widget.setStyleSheet(theme["spinbox"])
                elif widget_type == 'QLabel':
                    widget.setStyleSheet(theme["label_secondary"])
            for child in widget.children():
                if isinstance(child, QWidget):
                    self.apply_theme_to_widget(child, theme)
        except:
            pass

    def update_widget_styles(self, theme):
        try:
            if hasattr(self, 'log'):
                self.log.setStyleSheet(theme["text_edit"])
            if hasattr(self, 'strategySignalsLog'):
                self.strategySignalsLog.setStyleSheet(theme["text_edit"])
            if hasattr(self, 'positionsTable'):
                self.positionsTable.setStyleSheet(theme["table_widget"])
            if hasattr(self, 'accountsList'):
                self.accountsList.setStyleSheet(theme["list"])
            if hasattr(self, 'strategyStatusLabel'):
                current_style = self.strategyStatusLabel.styleSheet()
                if "background-color: #1e293b" in current_style:
                    self.strategyStatusLabel.setStyleSheet(styles.STRATEGY_STYLES["status_label_active"])
                elif "background-color: #064e3b" in current_style:
                    self.strategyStatusLabel.setStyleSheet(styles.STRATEGY_STYLES["status_label_buy"])
                elif "background-color: #7f1d1d" in current_style:
                    self.strategyStatusLabel.setStyleSheet(styles.STRATEGY_STYLES["status_label_sell"])
        except:
            pass

    def test_notifications(self):
        send_signal('Тестовое уведомление', self.telegram_token_edit.text(), self.telegram_chat_id.text())

    def export_accounts(self):
        try:
            accounts = account.load_accounts()
            if not accounts:
                return
            filename, _ = QFileDialog.getSaveFileName(
                self,
                "Экспорт аккаунтов",
                f"tinkoff_accounts_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                "JSON Files (*.json);;All Files (*)"
            )
            if not filename:
                return
            if not filename.endswith('.json'):
                filename += '.json'
            export_data = {
                "version": "1.0",
                "export_date": datetime.now().isoformat(),
                "accounts_count": len(accounts),
                "accounts": accounts
            }
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)
        except:
            pass

    def export_strategy_log(self):
        from datetime import datetime
        if not self.strategySignalsLog.toPlainText():
            return
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"strategy_log_{timestamp}.txt"
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(f"Лог стратегии - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write("=" * 50 + "\n\n")
                f.write(self.strategySignalsLog.toPlainText())
        except:
            pass

    def create_backup(self):
        try:
            from datetime import datetime
            import shutil
            backup_dir = "backups"
            os.makedirs(backup_dir, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"backup_{timestamp}"
            backup_path = os.path.join(backup_dir, backup_name)
            files_to_backup = [
                "accounts.json",
                "app_settings.ini",
                "instrument_cache.json",
                "name_cache.json"
            ]
            os.makedirs(backup_path, exist_ok=True)
            for file in files_to_backup:
                if os.path.exists(file):
                    shutil.copy2(file, os.path.join(backup_path, file))
            shutil.make_archive(backup_path, 'zip', backup_path)
            shutil.rmtree(backup_path)
        except:
            pass

    def export_logs(self):
        try:
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"app_logs_{timestamp}.txt"
            logs = []
            logs.append("=== ОСНОВНОЙ ЛОГ ===\n")
            logs.append(self.log.toPlainText())
            logs.append("\n\n=== ЛОГ СТРАТЕГИЙ ===\n")
            logs.append(self.strategySignalsLog.toPlainText())
            with open(filename, 'w', encoding='utf-8') as f:
                f.write("\n".join(logs))
        except:
            pass

    def tray_icon_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.show_from_tray()

    def show_from_tray(self):
        self.show()
        self.setWindowState(self.windowState() & ~Qt.WindowState.WindowMinimized | Qt.WindowState.WindowActive)
        self.activateWindow()
        self.is_minimized_to_tray = False

    def close_application(self):
        if hasattr(self, 'streamWorker'):
            self.streamWorker.stop_stream()
        if hasattr(self, 'thread') and self.thread.isRunning():
            self.thread.quit()
            self.thread.wait(2000)
        QApplication.quit()

    def closeEvent(self, event):
        if self.minimize_to_tray.isChecked() and not self.is_minimized_to_tray:
            event.ignore()
            self.hide()
            self.is_minimized_to_tray = True
            if self.tray_icon:
                self.tray_icon.showMessage(
                    "TinkoffAnalyzer",
                    "Приложение свернуто в трей",
                    QSystemTrayIcon.MessageIcon.Information,
                    2000
                )
        else:
            if hasattr(self, 'streamWorker'):
                self.streamWorker.stop_stream()
            if hasattr(self, 'thread') and self.thread.isRunning():
                self.thread.quit()
                self.thread.wait(2000)
            if self.tray_icon:
                self.tray_icon.hide()
            event.accept()

    def force_close(self):
        self.is_minimized_to_tray = False
        self.minimize_to_tray.setChecked(False)
        self.close()

    def append_log(self, text, level=logging.INFO):
        if level < self.current_log_level:
            return  
        timestamp = datetime.now().strftime("%H:%M:%S")
        if level == logging.DEBUG:
            formatted_text = f"[{timestamp}] {text}"
        elif level == logging.INFO:
            formatted_text = f"[{timestamp}] {text}"
        elif level == logging.WARNING:
            formatted_text = f"[{timestamp}] {text}"
        elif level == logging.ERROR:
            formatted_text = f"[{timestamp}] {text}"
        else:
            formatted_text = f"[{timestamp}] {text}"
        self.log.append(formatted_text)
        cursor = self.log.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        self.log.setTextCursor(cursor)

    def set_log_level(self, level_name):
        level = LOG_LEVELS.get(level_name, logging.INFO)
        self.current_log_level = level
        self.log.clear()
        self.append_log(f"Уровень логов изменен на: {level_name}")

    def _get_empty_chart_html(self, theme_name="Dark"):
        is_dark = theme_name == "Dark"
        bg_color = "#0f172a" if is_dark else "#ffffff"
        text_color = "#e2e8f0" if is_dark else "#0f0f0f"
        grid_color = "#334155" if is_dark else "#d1d1d1"
        up_color = "#10b981" if is_dark else "#238636" 
        down_color = "#ef4444" if is_dark else "#dc2626" 
        return f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Tinkoff Candlestick Chart</title>
            <script src="https://cdn.jsdelivr.net/npm/echarts@5.4.3/dist/echarts.min.js"></script>
            <style>
                body {{ 
                    margin: 0; 
                    padding: 0; 
                    font-family: Arial, sans-serif; 
                    background: {bg_color}; 
                    color: {text_color}; 
                    height: 100vh;
                    overflow: hidden;
                }}
                #chart {{ 
                    width: 100%; 
                    height: 100vh; 
                    background: {bg_color}; 
                }}
            </style>
        </head>
        <body>
            <div id="chart"></div>
            <script>
                var chart = null;
                var allCandles = [];
                var currentZoom = {{ start: 0, end: 100 }};
                var isChartInitialized = false;
                window.updateCandlestickChart = function(newCandles) {{
                    if (!newCandles || newCandles.length === 0) {{
                        return;
                    }}
                    allCandles = newCandles;
                    if (!isChartInitialized || !chart) {{
                        if (initChart()) {{
                            renderCandlestickChart(false);
                        }}
                    }} else {{
                        try {{
                            var option = chart.getOption();
                            if (option && option.dataZoom && option.dataZoom[0]) {{
                                currentZoom.start = option.dataZoom[0].start;
                                currentZoom.end = option.dataZoom[0].end;
                            }}
                        }} catch (error) {{
                        }}
                        renderCandlestickChart(true);
                    }}
                }};
                function renderCandlestickChart(preserveZoom) {{
                    if (!chart) {{
                        return;
                    }}
                    var zoomStart = 0;
                    var zoomEnd = 100;
                    if (preserveZoom && currentZoom) {{
                        zoomStart = currentZoom.start;
                        zoomEnd = currentZoom.end;
                    }}
                    var option = {{
                        backgroundColor: '{bg_color}',
                        animation: false,
                        tooltip: {{
                            trigger: 'axis',
                            axisPointer: {{ 
                                type: 'cross'
                            }},
                            formatter: function(params) {{
                                var data = params[0].data;
                                if (!data) return '';
                                var date = new Date(data[0]);
                                var isUp = data[1] <= data[2];
                                var color = isUp ? '{up_color}' : '{down_color}';
                                return '<div style="font-weight: bold; margin-bottom: 5px; color: {text_color}">' + 
                                    date.toLocaleString('ru-RU') + '</div>' +
                                    '<div style="color: ' + color + ';">📈 Открытие: ' + data[1].toFixed(2) + '</div>' +
                                    '<div style="color: ' + color + ';">📉 Закрытие: ' + data[2].toFixed(2) + '</div>' +
                                    '<div style="color: {text_color};">📉 Минимум: ' + data[3].toFixed(2) + '</div>' +
                                    '<div style="color: {text_color};">📈 Максимум: ' + data[4].toFixed(2) + '</div>';
                            }},
                            backgroundColor: '{bg_color}',
                            borderColor: '{grid_color}',
                            textStyle: {{
                                color: '{text_color}'
                            }}
                        }},
                        xAxis: {{
                            type: 'time',
                            boundaryGap: false,
                            axisLine: {{ 
                                lineStyle: {{ 
                                    color: '{grid_color}' 
                                }} 
                            }},
                            axisLabel: {{
                                color: '{text_color}',
                                formatter: function(value) {{
                                    var date = new Date(value);
                                    return date.toLocaleTimeString('ru-RU', {{ 
                                        hour: '2-digit', 
                                        minute: '2-digit' 
                                    }});
                                }}
                            }},
                            splitLine: {{ 
                                show: true,
                                lineStyle: {{
                                    color: '{grid_color}',
                                    type: 'dashed',
                                    opacity: 0.3
                                }}
                            }}
                        }},
                        yAxis: {{
                            type: 'value',
                            scale: true,
                            axisLine: {{ 
                                lineStyle: {{ 
                                    color: '{grid_color}' 
                                }} 
                            }},
                            axisLabel: {{ 
                                color: '{text_color}'
                            }},
                            splitLine: {{ 
                                lineStyle: {{ 
                                    color: '{grid_color}', 
                                    type: 'dashed',
                                    opacity: 0.3
                                }} 
                            }}
                        }},
                        dataZoom: [
                            {{
                                type: 'inside',
                                start: zoomStart,
                                end: zoomEnd,
                                zoomOnMouseWheel: true,
                                moveOnMouseMove: true
                            }},
                            {{
                                type: 'slider',
                                show: true,
                                start: zoomStart,
                                end: zoomEnd,
                                height: 20,
                                bottom: 10,
                                textStyle: {{ 
                                    color: '{text_color}' 
                                }},
                                handleStyle: {{ 
                                    color: '{up_color}' 
                                }},
                                dataBackground: {{
                                    lineStyle: {{
                                        color: '{grid_color}'
                                    }},
                                    areaStyle: {{
                                        color: '{grid_color}',
                                        opacity: 0.1
                                    }}
                                }}
                            }}
                        ],
                        series: [{{
                            name: 'Свечи',
                            type: 'candlestick',
                            data: allCandles,
                            itemStyle: {{
                                color: '{up_color}',
                                color0: '{down_color}',
                                borderColor: '{up_color}',
                                borderColor0: '{down_color}',
                                borderWidth: 1
                            }},
                            emphasis: {{
                                itemStyle: {{
                                    borderWidth: 2
                                }}
                            }}
                        }}],
                        grid: {{ 
                            left: '3%', 
                            right: '3%', 
                            bottom: '15%', 
                            top: '3%' 
                        }}
                    }};
                    try {{
                        chart.setOption(option, true);
                        isChartInitialized = true;
                    }} catch (error) {{
                    }}
                }}
                function initChart() {{
                    var chartDom = document.getElementById('chart');
                    if (!chartDom) {{
                        return false;
                    }}
                    try {{
                        chart = echarts.init(chartDom);
                        chart.on('dataZoom', function(params) {{
                            if (params.batch) {{
                                currentZoom.start = params.batch[0].start;
                                currentZoom.end = params.batch[0].end;
                            }} else {{
                                currentZoom.start = params.start;
                                currentZoom.end = params.end;
                            }}
                        }});
                        window.addEventListener('resize', function() {{
                            if (chart) {{
                                chart.resize();
                            }}
                        }});
                        isChartInitialized = true;
                        return true;
                    }} catch (error) {{
                        return false;
                    }}
                }}
                document.addEventListener('DOMContentLoaded', function() {{
                    initChart();
                }});
                if (document.readyState === 'complete') {{
                    setTimeout(initChart, 100);
                }}
            </script>
        </body>
        </html>
        """
    
    def _get_pie_chart(self):
        return """
        <!DOCTYPE html>
        <html lang="ru">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
            <style>
                body { 
                    margin: 0; 
                    padding: 2vh; 
                    font-family: Arial, sans-serif; 
                    background: #0f0f0f; 
                    color: #0f0f0f; 
                }
                .chart-container {
                    position: relative;
                    height: 93vh;
                    width: 100%;
                }
            </style>
        </head>
        <body>
            <div class="chart-container">
                <canvas id="portfolioChart"></canvas>
            </div>
            <script>
                let portfolioChart;
                function initPortfolioChart() {
                    const ctx = document.getElementById('portfolioChart').getContext('2d');
                    const initialData = {
                        labels: ['Загрузка...'],
                        datasets: [{
                            data: [100],
                            backgroundColor: ['#94a3b8'],
                            borderColor: ['#475569'],
                            borderWidth: 2
                        }]
                    };
                    portfolioChart = new Chart(ctx, {
                        type: 'pie',
                        data: initialData,
                        options: {
                            responsive: true,
                            maintainAspectRatio: false,
                            plugins: {
                                legend: {
                                    position: 'top',
                                    labels: {
                                        color: '#f8fafc',
                                        font: {
                                            size: 12
                                        },
                                        padding: 20
                                    }
                                },
                                tooltip: {
                                    callbacks: {
                                        label: function(context) {
                                            const label = context.label || '';
                                            const value = context.parsed;
                                            const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                            const percentage = Math.round((value / total) * 100);
                                            return `${label}: ${value.toLocaleString('ru-RU')} руб. (${percentage}%)`;
                                        }
                                    }
                                }
                            }
                        }
                    });
                }
                function updatePortfolioChart(labels, data, colors) {
                    if (!portfolioChart) return;
                    portfolioChart.data.labels = labels;
                    portfolioChart.data.datasets[0].data = data;
                    portfolioChart.data.datasets[0].backgroundColor = colors;
                    portfolioChart.data.datasets[0].borderColor = colors.map(color => color.replace('0.2', '1'));
                    portfolioChart.update();
                }
                document.addEventListener('DOMContentLoaded', function() {
                    initPortfolioChart();
                });
                window.updatePortfolioChart = updatePortfolioChart;
            </script>
        </body>
        </html>
        """

    def open_accounts_window(self):
        if isinstance(self.accounts_window, AccountManagerWindow):
            self.accounts_window.close()
        self.accounts_window = AccountManagerWindow(self)
        if hasattr(self, 'theme'):
            self.accounts_window.setStyleSheet(self.theme["main_window"])
            self.apply_theme_to_widget(self.accounts_window, self.theme)
        self.accounts_window.show()

    def on_order_placed(self, order_id, message):
        self.append_log(f"{message}")
        self.append_log(f"ID ордера: {order_id}")

    def on_order_error(self, error_message):
        self.append_log(f"Ошибка размещения ордера: {error_message}")

    def error(self, message):
        self.append_log(f"Ошибка: {message}")