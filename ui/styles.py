DARK_THEME = {
    "main_window": """
        QMainWindow {
            background: #0f0f0f;
            color: #e6edf3;
        }
    """,
    
    "widget": """
        QWidget {
            background: #1a1a1a;
            color: #e6edf3;
        }
    """,

    "dialog": """
        QDialog {
            background: #1a1a1a;
            color: #e6edf3;
        }
    """,
    
    "list": """
        QListWidget {
            background: #21262d;
            color: #e6edf3;
            border: 1px solid #30363d;
            border-radius: 6px;
            padding: 8px 8px;
            font-size: 14px;
            font-weight: 500;
            outline: none;
        }
        QListWidget::item {
            background: #21262d;
            color: #e6edf3;
            border: 1px solid #30363d;
            border-radius: 6px;
            padding: 8px 8px;
            margin: 2px 0px;
            font-size: 14px;
            font-weight: 500;
            outline: none;
        }
        QListWidget::item:selected {
            background: #1f6f3c;
            color: #e6edf3;
            border: 1px solid #2ea043;
            border-radius: 6px;
            outline: none;
        }
        QListWidget::item:selected:active {
            background: #238636;
            color: #e6edf3;
            border: 1px solid #2ea043;
            outline: none;
        }
        QListWidget::item:selected:focus {
            background: #1f6f3c;
            color: #e6edf3;
            border: 1px solid #2ea043;
            outline: none;
        }
        QListWidget::item:hover {
            background: #30363d;
            color: #e6edf3;
            border: 1px solid #238636;
            border-radius: 6px;
        }
        QListWidget:focus {
            outline: none;
            border: 1px solid #30363d;
        }
    """,
    
    "button_primary": """
        QPushButton {
            background: #238636;
            color: white;
            border: 1px solid #2ea043;
            border-radius: 6px;
            padding: 10px 16px;
            font-size: 14px;
            font-weight: 500;
        }
        QPushButton:hover {
            background: #2ea043;
        }
        QPushButton:pressed {
            background: #1f6f3c;
        }
        QPushButton:disabled {
            background: #484f58;
            color: #8b949e;
        }
    """,
    
    "button_secondary": """
        QPushButton {
            background: #21262d;
            color: #e6edf3;
            border: 1px solid;
            border-color: #30363d;
            border-radius: 6px;
            padding: 10px 16px;
            font-size: 13px;
            font-weight: 500;
            outline: none;
            min-width: 100px;
        }
        QPushButton:hover {
            background: #30363d;
            border-color: #238636;
        }
        QPushButton:pressed {
            background: #1c2128;
        }
        QPushButton:disabled {
            background: #484f58;
            color: #8b949e;
        }
    """,
    
    "line_edit": """
        QLineEdit {
            background: #0f0f0f;
            color: #e6edf3;
            border: 1px solid #30363d;
            border-radius: 6px;
            padding: 8px 12px;
            font-size: 14px;
        }
        QLineEdit:focus {
            border: 1px solid #2ea043;
            background: #0f0f0f;
        }
        QLineEdit:hover {
            border-color: #238636;
        }
        QLineEdit:disabled {
            background: #0f0f0f;
            color: #484f58;
        }
        QLineEdit::placeholder {
            color: #238636;
            font-style: italic;
            background: #0f0f0f
        }
        QTextEdit{
            background: #0f0f0f;
            border: none;
        }
    """,
    
    "combo_box": """
        QComboBox {
            background: #0f0f0f;
            color: #e6edf3;
            border: 1px solid #30363d;
            border-radius: 6px;
            padding: 8px;
            font-size: 14px;
            min-width: 120px;
        }
        QComboBox::drop-down {
            subcontrol-origin: padding;
            subcontrol-position: top right;
            border: none;
            width: 20px;
        }
        QComboBox QAbstractItemView {
            background: #0f0f0f;
            color: #e6edf3;
            border: 1px solid #30363d;
            background: #0f0f0f;
            selection-color: white;
            selection-background-color: #238636;
            font-size: 14px;
            outline: none;
        }
        
        QComboBox QAbstractItemView::item {
            padding: 4px;
            font-size: 14px;
            border-radius: 6px;
        }
        
        QComboBox QAbstractItemView::item:hover {
            background: #30363d;
            color: #e6edf3;
            border: 1px solid #238636;
            border-radius: 6px;
        }
        
        QComboBox:hover {
            border-color: #238636;
        }
        QComboBox:focus {
            border-color: #2ea043;
        }
        QComboBox:disabled {
            background: #1a1a1a;
            color: #555555;
        }
    """,
    
    "checkbox": """
        QCheckBox {
            color: #e6edf3;
            spacing: 10px;
            font-size: 14px;
            font-weight: 500;
            background: #0f0f0f;
        }
        QCheckBox::indicator {
            width: 12px;
            height: 12px;
            border-radius: 4px;
            border: 1px solid #333333;
            background: #0f0f0f;
        }
        QCheckBox::indicator:hover {
            border-color: #238636;
        }
        QCheckBox::indicator:checked {
            background: #238636;
            border: 1px solid #2ea043;
        }
        QCheckBox:disabled {
            color: #555555;
        }
        QCheckBox::indicator:disabled {
            background: #1a1a1a;
            border: 1px solid #262626;
        }
    """,
    
    "group_box": """
        QGroupBox {
            color: #e6edf3;
            border: 1px solid #30363d;
            border-radius: 8px;
            margin-top: 15px;
            padding-top: 15px;
            font-weight: 600;
            font-size: 14px;
            background: #0f0f0f;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 12px;
            padding: 4px 12px 4px 12px;
            background: #0f0f0f;
            color: #e6edf3;
            border: 1px solid #30363d;
            border-radius: 6px;
        }
    """,
    
    "text_edit": """
        QTextEdit {
            background: #0f0f0f;
            color: #e6edf3;
            border: 1px solid #30363d;
            border-radius: 6px;
            padding: 12px;
            font-family: 'Consolas', 'Monaco', monospace;
            font-size: 13px;
            selection-background-color: #1f6f3c;
        }
        QTextEdit:focus {
            border: 1px solid #2ea043;
        }
    """,
    
    "table_widget": """

        QTableWidget::viewport {
            background: #0f0f0f;
            color: #e6edf3;
            border: 1px solid #30363d;
            border-radius: 6px;
        }
        
        QTableWidget {
            background: #0f0f0f;
            color: #e6edf3;
            border: 1px solid #30363d;
            border-radius: 6px;
            gridline-color: #21262d;
        }
        
        
        QScrollBar::add-page {
            background: #0f0f0f;
            border: none;
            border-radius: 6px;
            width: 10px;
            
        }
        QScrollBar::sub-page {
            background: #0f0f0f;
            border: none;
            border-radius: 6px;
            width: 10px;
        }
        
        QScrollBar {
            background: #0f0f0f;
            border: 1px solid #30363d;
            border-radius: 6px;
        }
        
        QTableWidget::item {
            padding: 8px;
            border-bottom: 1px solid #21262d;
            border-right: 1px solid #21262d;
        }
        
        QTableWidget::item:first-child {
            border-left: none;
            border-top: none;
        }
        QTableWidget::item:last-child {
            border-right: none;
            border-bottom: none;
        }
        QTableWidget::item:selected {
            background: #1f6f3c;
            color: white;
        }
        
        QTableWidget::item:selected:active {
            background: #238636;
        }
        QTableWidget::item:selected:!active {
            background: #1f6f3c;
        }
        QTableWidget::item:hover {
            background: #161b22;
        }
        QHeaderView::section:horizontal {
            border-bottom: 1px solid #21262d;
            border-right: 1px solid #21262d;
        }
        QHeaderView::section:vertical {
            padding: 5px;
            border-bottom: 1px solid #21262d;
            border-right: 1px solid #21262d;
        }
        QHeaderView::section {
            background: #161b22;
            color: #e6edf3;
            padding: 10px;
            border: none;
            font-weight: 600;
        }
        QTableCornerButton::section {
            background: #161b22;
            color: #e6edf3;
            padding: 10px;
            border: none;
            font-weight: 600;
            border-right: 1px solid #21262d;
            border-bottom: 1px solid #21262d;
        }
        
        QTableWidget::focus {
            outline: none;
        }
    """,
    
    "tab_widget": """
        QTabWidget::pane {
            border: 1px solid #30363d;
            background: none;
            border-radius: 8px;
        }
        QTabBar::tab {
            background: #2d2d2d;
            color: #8b949e;
            border: 1px solid #30363d;
            border-bottom: none;
            border-top-left-radius: 6px;
            border-top-right-radius: 6px;
            padding: 5px 10px;
            margin-right: 2px;
            font-size: 14px;
            font-weight: 500;
        }
        QTabBar::tab:selected {
            background: #0f0f0f;
            color: #e6edf3;
            border-color: #30363d;
            border-bottom: 1px solid #0f0f0f;
        }
        QTabBar::tab:hover:!selected {
            background: #3d3d3d;
            color: #e6edf3;
        }
        QTabBar {
            background: #1a1a1a;
        }
    """,
    
    "spinbox": """
        QSpinBox {
            background: #0f0f0f;
            color: #e6edf3;
            border: 1px solid #30363d;
            border-radius: 6px;
            padding: 8px 10px;
            font-size: 14px;
        }
        QSpinBox:focus {
            border: 1px solid #2ea043;
        }
        QSpinBox::up-button, QSpinBox::down-button {
            width: 0px;
            height: 0px;
            border: none;
            background: transparent;
        }
    """,
    
    "label_primary": """
        QLabel {
            background-color: transparent;
            color: #e6edf3;
            font-size: 14px;
            font-weight: 500;
        }
    """,
    
    "label_secondary": """
        QLabel {
            background-color: transparent;
            color: #8b949e;
            font-size: 13px;
        }
    """,
    
    "label_title": """
        QLabel {
            background-color: transparent;
            color: #e6edf3;
            font-size: 18px;
            font-weight: 600;
            padding: 8px 0px;
        }
    """,
    
    "label_accent": """
        QLabel {
            background-color: transparent;
            color: #2ea043;
            font-size: 14px;
            font-weight: 600;
        }
    """,
    
    "splitter": """
        QSplitter::handle {
            background: #30363d;
            width: 4px;
            height: 4px;
            border-radius: 2px;
        }
        QSplitter::handle:hover {
            background: #484f58;
        }
        QSplitter::handle:horizontal {
            margin: 0 2px;
        }
        QSplitter::handle:vertical {
            margin: 2px 0;
        }
    """
}

LIGHT_THEME = {
    "main_window": """
        QMainWindow {
            background: #ffffff;
            color: #0f0f0f;
        }
    """,
    
    "widget": """
        QWidget {
            background: #f5f5f5;
            color: #0f0f0f;
        }
    """,

    "dialog": """
        QDialog {
            background: #ffffff;
            color: #0f0f0f;
        }
    """,
    
    "list": """
        QListWidget {
            background: #ffffff;
            color: #0f0f0f;
            border: 1px solid #d1d1d1;
            border-radius: 6px;
            padding: 8px 8px;
            font-size: 14px;
            font-weight: 500;
            outline: none;
        }
        QListWidget::item {
            background: #ffffff;
            color: #0f0f0f;
            border: 1px solid #d1d1d1;
            border-radius: 6px;
            padding: 8px 8px;
            margin: 2px 0px;
            font-size: 14px;
            font-weight: 500;
            outline: none;
        }
        QListWidget::item:selected {
            background: #238636;
            color: #ffffff;
            border: 1px solid #2ea043;
            border-radius: 6px;
            outline: none;
        }
        QListWidget::item:selected:active {
            background: #2ea043;
            color: #ffffff;
            border: 1px solid #2ea043;
            outline: none;
        }
        QListWidget::item:selected:focus {
            background: #238636;
            color: #ffffff;
            border: 1px solid #2ea043;
            outline: none;
        }
        QListWidget::item:hover {
            background: #f0f0f0;
            color: #0f0f0f;
            border: 1px solid #238636;
            border-radius: 6px;
        }
        QListWidget:focus {
            outline: none;
            border: 1px solid #d1d1d1;
        }
    """,
    
    "button_primary": """
        QPushButton {
            background: #238636;
            color: white;
            border: 1px solid #2ea043;
            border-radius: 6px;
            padding: 10px 16px;
            font-size: 14px;
            font-weight: 500;
        }
        QPushButton:hover {
            background: #2ea043;
        }
        QPushButton:pressed {
            background: #1f6f3c;
        }
        QPushButton:disabled {
            background: #b0b0b0;
            color: #8b8b8b;
        }
    """,
    
    "button_secondary": """
        QPushButton {
            background: #ffffff;
            color: #0f0f0f;
            border: 1px solid;
            border-color: #d1d1d1;
            border-radius: 6px;
            padding: 10px 16px;
            font-size: 13px;
            font-weight: 500;
            outline: none;
            min-width: 100px;
        }
        QPushButton:hover {
            background: #f0f0f0;
            border-color: #238636;
        }
        QPushButton:pressed {
            background: #e8e8e8;
        }
        QPushButton:disabled {
            background: #b0b0b0;
            color: #8b8b8b;
        }
    """,
    
    "line_edit": """
        QLineEdit {
            background: #ffffff;
            color: #0f0f0f;
            border: 1px solid #d1d1d1;
            border-radius: 6px;
            padding: 8px 12px;
            font-size: 14px;
        }
        QLineEdit:focus {
            border: 1px solid #2ea043;
            background: #ffffff;
        }
        QLineEdit:hover {
            border-color: #238636;
        }
        QLineEdit:disabled {
            background: #f5f5f5;
            color: #8b8b8b;
        }
        QLineEdit::placeholder {
            color: #666666;
            font-style: italic;
        }
        QTextEdit{
            background: #ffffff;
            border: none;
        }
    """,
    
    "combo_box": """
        QComboBox {
            background: #ffffff;
            color: #0f0f0f;
            border: 1px solid #d1d1d1;
            border-radius: 6px;
            padding: 8px;
            font-size: 14px;
            min-width: 120px;
        }
        QComboBox::drop-down {
            subcontrol-origin: padding;
            subcontrol-position: top right;
            border: none;
            width: 20px;
        }
        QComboBox QAbstractItemView {
            background: #ffffff;
            color: #0f0f0f;
            border: 1px solid #d1d1d1;
            background: #ffffff;
            selection-color: white;
            selection-background-color: #238636;
            font-size: 14px;
            outline: none;
        }
        
        QComboBox QAbstractItemView::item {
            padding: 4px;
            font-size: 14px;
            border-radius: 6px;
        }
        
        QComboBox QAbstractItemView::item:selected {
            color: #0f0f0f;
            outline: none;
        }
        
        QComboBox QAbstractItemView::item:selected:focus {
            color: #0f0f0f;
            outline: none;
        }
        
        QComboBox QAbstractItemView::item:hover {
            background: #f0f0f0;
            color: #0f0f0f;
            border: 1px solid #238636;
            border-radius: 6px;
        }
        
        QComboBox:hover {
            border-color: #238636;
        }
        QComboBox:focus {
            border-color: #2ea043;
        }
        QComboBox:disabled {
            background: #f5f5f5;
            color: #8b8b8b;
        }
    """,
    
    "checkbox": """
        QCheckBox {
            color: #0f0f0f;
            spacing: 10px;
            font-size: 14px;
            font-weight: 500;
            background: transparent;
        }
        QCheckBox::indicator {
            width: 12px;
            height: 12px;
            border-radius: 4px;
            border: 1px solid #b0b0b0;
            background: #ffffff;
        }
        QCheckBox::indicator:hover {
            border-color: #238636;
        }
        QCheckBox::indicator:checked {
            background: #238636;
            border: 1px solid #2ea043;
        }
        QCheckBox:disabled {
            color: #8b8b8b;
        }
        QCheckBox::indicator:disabled {
            background: #f5f5f5;
            border: 1px solid #d1d1d1;
        }
    """,
    
    "group_box": """
        QGroupBox {
            color: #0f0f0f;
            border: 1px solid #d1d1d1;
            border-radius: 8px;
            margin-top: 15px;
            padding-top: 15px;
            font-weight: 600;
            font-size: 14px;
            background: #ffffff;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 12px;
            padding: 4px 12px 4px 12px;
            background: #ffffff;
            color: #0f0f0f;
            border: 1px solid #d1d1d1;
            border-radius: 6px;
        }
    """,
    
    "text_edit": """
        QTextEdit {
            background: #ffffff;
            color: #0f0f0f;
            border: 1px solid #d1d1d1;
            border-radius: 6px;
            padding: 12px;
            font-family: 'Consolas', 'Monaco', monospace;
            font-size: 13px;
            selection-background-color: #238636;
        }
        QTextEdit:focus {
            border: 1px solid #2ea043;
        }
    """,
    
    "table_widget": """
        QTableWidget::viewport {
            background: #ffffff;
            color: #0f0f0f;
            border: 1px solid #d1d1d1;
            border-radius: 6px;
        }
        
        QTableWidget {
            background: #ffffff;
            color: #0f0f0f;
            border: 1px solid #d1d1d1;
            border-radius: 6px;
            gridline-color: #e8e8e8;
        }
        
        QScrollBar::add-page {
            background: #ffffff;
            border: none;
            border-radius: 6px;
            width: 10px;
        }
        QScrollBar::sub-page {
            background: #ffffff;
            border: none;
            border-radius: 6px;
            width: 10px;
        }
        
        QScrollBar {
            background: #ffffff;
            border: 1px solid #d1d1d1;
            border-radius: 6px;
        }
        
        QTableWidget::item {
            padding: 8px;
            border-bottom: 1px solid #e8e8e8;
            border-right: 1px solid #e8e8e8;
        }
        
        QTableWidget::item:first-child {
            border-left: none;
            border-top: none;
        }
        QTableWidget::item:last-child {
            border-right: none;
            border-bottom: none;
        }
        QTableWidget::item:selected {
            background: #238636;
            color: white;
        }
        
        QTableWidget::item:selected:active {
            background: #2ea043;
        }
        QTableWidget::item:selected:!active {
            background: #238636;
        }
        QTableWidget::item:hover {
            background: #f8f8f8;
        }
        QHeaderView::section:horizontal {
            border-bottom: 1px solid #e8e8e8;
            border-right: 1px solid #e8e8e8;
        }
        QHeaderView::section:vertical {
            padding: 5px;
            border-bottom: 1px solid #e8e8e8;
            border-right: 1px solid #e8e8e8;
        }
        QHeaderView::section {
            background: #f0f0f0;
            color: #0f0f0f;
            padding: 10px;
            border: none;
            font-weight: 600;
        }
        QTableCornerButton::section {
            background: #f0f0f0;
            color: #0f0f0f;
            padding: 10px;
            border: none;
            font-weight: 600;
            border-right: 1px solid #e8e8e8;
            border-bottom: 1px solid #e8e8e8;
        }
        
        QTableWidget::focus {
            outline: none;
        }
    """,
    
    "tab_widget": """
        QTabWidget::pane {
            border: 1px solid #d1d1d1;
            background: none;
            border-radius: 8px;
        }
        QTabBar::tab {
            background: #e8e8e8;
            color: #666666;
            border: 1px solid #d1d1d1;
            border-bottom: none;
            border-top-left-radius: 6px;
            border-top-right-radius: 6px;
            padding: 5px 10px;
            margin-right: 2px;
            font-size: 14px;
            font-weight: 500;
        }
        QTabBar::tab:selected {
            background: #ffffff;
            color: #0f0f0f;
            border-color: #d1d1d1;
            border-bottom: 1px solid #ffffff;
        }
        QTabBar::tab:hover:!selected {
            background: #f0f0f0;
            color: #0f0f0f;
        }
        QTabBar {
            background: #f5f5f5;
        }
    """,
    
    "spinbox": """
        QSpinBox {
            background: #ffffff;
            color: #0f0f0f;
            border: 1px solid #d1d1d1;
            border-radius: 6px;
            padding: 8px 10px;
            font-size: 14px;
        }
        QSpinBox:focus {
            border: 1px solid #2ea043;
        }
        QSpinBox::up-button, QSpinBox::down-button {
            width: 0px;
            height: 0px;
            border: none;
            background: transparent;
        }
    """,
    
    "label_primary": """
        QLabel {
            background-color: transparent;
            color: #0f0f0f;
            font-size: 14px;
            font-weight: 500;
        }
        QLabel::disabled {
            color: #666666;
        }
    """,
    
    "label_secondary": """
        QLabel {
            background-color: transparent;
            color: #666666;
            font-size: 13px;
        }
    """,
    
    "label_title": """
        QLabel {
            background-color: transparent;
            color: #0f0f0f;
            font-size: 18px;
            font-weight: 600;
            padding: 8px 0px;
        }
    """,
    
    "label_accent": """
        QLabel {
            background-color: transparent;
            color: #238636;
            font-size: 14px;
            font-weight: 600;
        }
    """,
    
    "splitter": """
        QSplitter::handle {
            background: #d1d1d1;
            width: 4px;
            height: 4px;
            border-radius: 2px;
        }
        QSplitter::handle:hover {
            background: #b0b0b0;
        }
        QSplitter::handle:horizontal {
            margin: 0 2px;
        }
        QSplitter::handle:vertical {
            margin: 2px 0;
        }
    """
}

STRATEGY_STYLES = {
    "status_label_active": """
        QLabel {
            background-color: #1e293b;
            color: #e2e8f0;
            border: 2px solid #334155;
            border-radius: 8px;
            padding: 12px;
            font-size: 14px;
            font-weight: bold;
            min-height: 25px;
        }
    """,
    
    "status_label_buy": """
        QLabel {
            background-color: #064e3b;
            color: #ecfdf5;
            border: 2px solid #10b981;
            border-radius: 8px;
            padding: 12px;
            font-size: 14px;
            font-weight: bold;
            min-height: 25px;
        }
    """,
    
    "status_label_sell": """
        QLabel {
            background-color: #7f1d1d;
            color: #fef2f2;
            border: 2px solid #ef4444;
            border-radius: 8px;
            padding: 12px;
            font-size: 14px;
            font-weight: bold;
            min-height: 25px;
        }
    """
}

THEMES = {
    "Dark": DARK_THEME,
    "Light": LIGHT_THEME
}

COMMON_STYLES = LIGHT_THEME
ACCOUNT_STYLES = LIGHT_THEME
PORTFOLIO_STYLES = LIGHT_THEME
CHART_STYLES = LIGHT_THEME
DIALOG_STYLES = LIGHT_THEME