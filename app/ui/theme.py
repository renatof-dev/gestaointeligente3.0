APP_STYLESHEET = """
QMainWindow, QWidget {
    background: #f4f6fb;
    color: #0f172a;
    font-family: 'Segoe UI';
}

QLabel {
    background: transparent;
}

#Sidebar {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 #0b2239, stop:1 #1b496f);
    border-radius: 0;
    border-right: 1px solid rgba(255,255,255,0.09);
}

QFrame#SidebarUserCard {
    background: rgba(255,255,255,0.08);
    border: 1px solid rgba(255,255,255,0.12);
    border-radius: 12px;
}

QFrame#SidebarBrand {
    background: rgba(255,255,255,0.06);
    border: 1px solid rgba(255,255,255,0.14);
    border-radius: 14px;
}

QListWidget#SidebarMenu {
    background: transparent;
    border: none;
    outline: none;
}

QListWidget#SidebarMenu::item {
    color: #e8f0ff;
    padding: 10px 12px;
    margin: 3px 0;
    border-radius: 10px;
    border-left: 3px solid transparent;
    font-weight: 700;
    font-size: 13px;
}

QListWidget#SidebarMenu::item:hover {
    background: rgba(255,255,255,0.08);
}

QListWidget#SidebarMenu::item:selected {
    background: rgba(255,255,255,0.16);
    border-left: 3px solid #38bdf8;
}

QPushButton#MenuButton {
    text-align: left;
    border: none;
    border-radius: 10px;
    color: #e8f0ff;
    padding: 12px;
    font-weight: 600;
}

QPushButton#MenuButton:hover {
    background: rgba(255,255,255,0.13);
}

QPushButton#MenuButton:checked {
    background: rgba(255,255,255,0.24);
}

QFrame#Card {
    background: #ffffff;
    border: 1px solid #e3eaf3;
    border-radius: 14px;
}

QFrame#Card[pdvPane="catalog"] {
    border: 1px solid #c7d8ef;
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 #ffffff, stop:1 #f4f9ff);
}

QFrame#Card[pdvPane="checkout"] {
    border: 1px solid #d3dbe6;
    background: #f7f9fc;
}

QFrame[class="FilterBar"] {
    background: #ffffff;
    border: 1px solid #e3eaf3;
    border-radius: 14px;
}

QLineEdit, QComboBox, QDoubleSpinBox, QSpinBox, QTextEdit, QDateEdit {
    background: white;
    border: 1px solid #d6deea;
    border-radius: 10px;
    padding: 8px;
    selection-background-color: #635bff;
}

QDateEdit#ModernDateEdit {
    background: #f8faff;
    color: #334155;
    border: none;
    border-radius: 10px;
    padding: 7px 10px;
    min-width: 108px;
    font-weight: 700;
}

QDateEdit#ModernDateEdit::drop-down {
    width: 0px;
    border: none;
    background: transparent;
}

QDateEdit#ModernDateEdit::down-arrow {
    background: transparent;
    width: 0px;
    height: 0px;
}

QFrame#DateFieldWrap {
    background: #f8faff;
    border: 1px solid #d9e2ef;
    border-radius: 10px;
}

QToolButton#CalendarHintButton {
    background: #eef2ff;
    color: #5b6b85;
    border: none;
    border-left: 1px solid #d9e2ef;
    border-top-right-radius: 9px;
    border-bottom-right-radius: 9px;
    border-top-left-radius: 0px;
    border-bottom-left-radius: 0px;
    padding: 4px;
    min-width: 28px;
    max-width: 28px;
    min-height: 26px;
    max-height: 26px;
}

QToolButton#CalendarHintButton:hover {
    background: #e0e7ff;
    border-left: 1px solid #c7d2fe;
}

QCalendarWidget {
    background: #ffffff;
    border: 1px solid #dbe4f2;
    border-radius: 10px;
}

QCalendarWidget QWidget#qt_calendar_navigationbar {
    background: #f5f7ff;
    border-bottom: 1px solid #e3e9f6;
}

QCalendarWidget QToolButton {
    background: transparent;
    color: #334155;
    border: none;
    border-radius: 6px;
    padding: 4px 8px;
    font-weight: 700;
}

QCalendarWidget QToolButton:hover {
    background: #ecefff;
    color: #4338ca;
}

QCalendarWidget QSpinBox {
    background: transparent;
    border: none;
    color: #334155;
    font-weight: 700;
}

QCalendarWidget QAbstractItemView:enabled {
    selection-background-color: #635bff;
    selection-color: #ffffff;
    background: #ffffff;
    color: #334155;
    gridline-color: #edf2fb;
}

QCalendarWidget QAbstractItemView:disabled {
    color: #c2c9d6;
}

QLineEdit:focus, QComboBox:focus, QDoubleSpinBox:focus, QSpinBox:focus, QTextEdit:focus, QDateEdit:focus {
    border: 1px solid #635bff;
}

QLineEdit#PdvSearchInput {
    min-height: 36px;
    border-radius: 12px;
    border: 1px solid #cfe0f5;
    background: #ffffff;
    padding: 9px 12px;
}

QLineEdit#PdvSearchInput:focus {
    border: 1px solid #2c7be5;
    background: #fbfdff;
}

QLabel#PdvCounter {
    color: #45556f;
    font-size: 12px;
    font-weight: 800;
}

QLabel#PdvHintBadge {
    font-weight: 800;
    padding: 6px 10px;
    border-radius: 10px;
}

QLabel#PdvHintBadge[severity="ok"] {
    background: #ecfdf5;
    color: #166534;
    border: 1px solid #bbf7d0;
}

QLabel#PdvHintBadge[severity="warn"] {
    background: #fff7ed;
    color: #b45309;
    border: 1px solid #fed7aa;
}

QScrollArea#PdvProductScroll {
    border: none;
    background: transparent;
}

QScrollArea#PdvProductScroll > QWidget > QWidget {
    background: transparent;
}

QPushButton {
    background: #635bff;
    color: white;
    border: 1px solid #564df1;
    border-radius: 10px;
    font-weight: 700;
    padding: 9px 14px;
    min-height: 18px;
}

QPushButton:hover {
    background: #5a53eb;
}

QPushButton:pressed {
    background: #4f48d4;
}

QPushButton:disabled {
    background: #cbd5e1;
    color: #94a3b8;
    border: 1px solid #cbd5e1;
}

QPushButton#SecondaryButton {
    background: #f8fafc;
    color: #334155;
    border: 1px solid #cbd5e1;
}

QPushButton#GhostButton {
    background: #f2f5fb;
    color: #5b6b85;
    border: 1px solid #dee6f1;
    border-radius: 9px;
    padding: 6px 10px;
    min-height: 16px;
    font-weight: 700;
}

QPushButton#GhostButton:hover {
    background: #e9eef8;
    color: #334155;
}

QPushButton#PayShortcutButton {
    background: #e4eeff;
    color: #1f3b6d;
    border: 1px solid #bfd3f4;
    border-radius: 10px;
    font-weight: 800;
    padding: 7px 10px;
    min-height: 18px;
}

QPushButton#PayShortcutButton:hover {
    background: #d4e3ff;
    border: 1px solid #9bbbe7;
    color: #102f5f;
}

QPushButton#PayShortcutButton:pressed {
    background: #d0e1ff;
}

QPushButton#ProductTileButton {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 #ffffff, stop:1 #eef6ff);
    color: #10243f;
    border: 1px solid #bfd2ea;
    border-radius: 14px;
    text-align: left;
    padding: 11px 12px;
    font-weight: 700;
    line-height: 1.25;
    min-height: 88px;
}

QPushButton#ProductTileButton:hover {
    background: #deecff;
    border: 1px solid #6f9fdb;
}

QPushButton#ProductTileButton:pressed {
    background: #cfe1ff;
}

QPushButton#SecondaryButton:hover {
    background: #eef2f7;
}

QPushButton#DangerButton {
    background: #ef4444;
    border: 1px solid #b91c1c;
}

QPushButton#DangerButton:hover {
    background: #e23333;
}

QPushButton#SuccessButton {
    background: #22c55e;
    border: 1px solid #15803d;
}

QPushButton#SuccessButton:hover {
    background: #1fb255;
}

QTableWidget, QTableView {
    background: white;
    alternate-background-color: #fbfcff;
    border: 1px solid #e0e7f1;
    border-radius: 12px;
    gridline-color: transparent;
    selection-background-color: #ece9ff;
    selection-color: #211f54;
}

QTableWidget#RecentSalesTable {
    background: #ffffff;
    alternate-background-color: #f8fbff;
    border: 1px solid #e3eaf5;
    border-radius: 12px;
    gridline-color: transparent;
    selection-background-color: #eaf0ff;
    selection-color: #1e3a8a;
}

QTableWidget#RecentSalesTable::item {
    padding: 8px 10px;
    border-bottom: 1px solid #edf2f8;
}

QTableWidget#RecentSalesTable::item:selected:active,
QTableWidget#RecentSalesTable::item:selected:!active {
    background: #eaf0ff;
    color: #1e3a8a;
    outline: 0;
}

QTableWidget#RecentSalesTable QHeaderView::section {
    background: #f5f8ff;
    color: #64748b;
    border: none;
    border-bottom: 1px solid #e6edf8;
    padding: 10px 8px;
    font-weight: 800;
}

QTableWidget#PdvCartTable {
    background: #ffffff;
    alternate-background-color: #f3f8ff;
    border: 1px solid #c7d8ee;
    border-radius: 12px;
    selection-background-color: #cfe2ff;
    selection-color: #0f2f65;
}

QTableWidget#PdvCartTable::item {
    padding: 9px 8px;
    border-bottom: 1px solid #dfebf8;
}

QTableWidget#PdvCartTable QHeaderView::section {
    background: #e2ecfb;
    color: #324760;
    border: none;
    border-bottom: 1px solid #ccdcef;
    padding: 10px 8px;
    font-weight: 800;
}

QComboBox#PdvClientInput {
    min-height: 36px;
    border-radius: 10px;
    border: 1px solid #d5dde7;
    background: #ffffff;
    padding: 0 10px;
}

QComboBox#PdvClientInput:focus {
    border: 1px solid #9aa7ba;
}

QComboBox#PdvClientInput::drop-down {
    width: 0px;
    border: none;
    background: transparent;
}

QComboBox#PdvClientInput::down-arrow {
    width: 0px;
    height: 0px;
}

QComboBox#PdvDensityCombo {
    min-height: 24px;
    min-width: 106px;
    border-radius: 8px;
    border: 1px solid #d5dde7;
    background: #ffffff;
    font-size: 11px;
    padding: 0 6px;
}

QFrame#PdvSectionCard {
    background: #f7f9fc;
    border: 1px solid #d9e1ea;
    border-radius: 12px;
}

QFrame#PdvPaymentSection {
    background: #f7f9fc;
    border: 1px solid #d9e1ea;
    border-radius: 12px;
}

QFrame#PdvPaymentSection QLabel {
    font-size: 11px;
    color: #334155;
}

QLabel#PdvSmallSectionTitle {
    color: #7a8698;
    font-size: 11px;
    font-weight: 800;
    letter-spacing: 1px;
}

QScrollArea#PdvCartItemsScroll {
    border: 1px solid #d5dde8;
    border-radius: 12px;
    background: #ffffff;
    min-height: 210px;
}

QScrollArea#PdvCartItemsScroll > QWidget > QWidget {
    background: #ffffff;
}

QFrame#PdvCartRow {
    background: #ffffff;
    border: none;
    border-bottom: 1px solid #edf1f6;
    border-radius: 0px;
}

QFrame#PdvCartRow[selected="true"] {
    background: #f3f7ff;
    border-bottom: 1px solid #d8e3f5;
}

QLabel#PdvCartItemName {
    color: #0f172a;
    font-size: 13px;
    font-weight: 800;
}

QLabel#PdvCartItemPrice {
    color: #5b5ce2;
    font-size: 12px;
    font-weight: 700;
}

QLabel#PdvCartThumb {
    background: #f8fafd;
    border: 1px solid #e3e9f1;
    border-radius: 8px;
}

QPushButton#PayMethodButton {
    background: #ffffff;
    color: #53657f;
    border: 1px solid #d7deea;
    border-radius: 9px;
    font-weight: 700;
    padding: 6px 10px;
    font-size: 12px;
    min-height: 28px;
}

QPushButton#PayMethodButton:hover {
    background: #f2f6fd;
}

QPushButton#PayMethodButton[active="true"] {
    background: #e7fbff;
    color: #0f766e;
    border: 1px solid #06b6d4;
}

QPushButton#PdvSecondaryToggle {
    background: #f6f8fb;
    color: #5e6f87;
    border: 1px solid #d5dde7;
    border-radius: 8px;
    font-size: 11px;
    font-weight: 700;
    padding: 5px 9px;
    min-height: 20px;
}

QPushButton#PdvSecondaryToggle:checked {
    background: #eef4ff;
    color: #2b4c7e;
    border: 1px solid #b8cae6;
}

QToolButton#PdvPixQrButton {
    background: #f8fbff;
    color: #0f766e;
    border: 1px solid #b8e5dc;
    border-radius: 8px;
    font-size: 11px;
    font-weight: 800;
    padding: 4px 8px;
    min-width: 26px;
    min-height: 20px;
}

QToolButton#PdvPixQrButton:hover {
    background: #e7fbff;
    border: 1px solid #7adac8;
}

QFrame#PdvSecondaryWrap {
    background: #ffffff;
    border: 1px solid #d9e1ea;
    border-radius: 9px;
}

QFrame#PdvSecondaryWrap QLabel {
    font-size: 11px;
    color: #4b5d77;
    font-weight: 600;
}

QComboBox#PdvSecondaryMethod,
QDoubleSpinBox#PdvSecondaryAmount {
    background: #ffffff;
    border: 1px solid #d5dde7;
    border-radius: 8px;
    min-height: 26px;
    font-size: 11px;
}

QLabel#PdvPrimarySplitLabel {
    color: #3b4f6a;
    font-size: 11px;
    font-weight: 700;
    background: #f8fbff;
    border: 1px solid #d9e2ef;
    border-radius: 8px;
    padding: 5px 8px;
}

QPushButton#PdvSecondaryFillRest {
    background: #f3f6fb;
    color: #4c5e79;
    border: 1px solid #d1dae7;
    border-radius: 8px;
    font-size: 11px;
    font-weight: 700;
    padding: 5px 8px;
    min-height: 26px;
}

QPushButton#PdvSecondaryFillRest:hover {
    background: #e9eff8;
}

QLabel#PdvSplitHint {
    color: #5b6b85;
    font-size: 10px;
    font-weight: 600;
    padding: 2px 2px 0px 2px;
}

QLabel#PdvCartQty {
    color: #0f1f36;
    font-size: 13px;
    font-weight: 800;
}

QPushButton#PdvMiniButton {
    background: #f2f4f7;
    color: #1f2937;
    border: 1px solid #d7dee8;
    border-radius: 8px;
    font-size: 12px;
    font-weight: 900;
    padding: 0px;
    min-height: 20px;
}

QPushButton#PdvMiniButton:hover {
    background: #e9eef5;
}

QPushButton#PdvMiniDanger {
    background: #fff1f2;
    color: #ef4444;
    border: 1px solid #fecdd3;
    border-radius: 8px;
    font-size: 12px;
    font-weight: 900;
    padding: 0px;
    min-height: 20px;
}

QPushButton#PdvMiniDanger:hover {
    background: #ffe4e6;
}

QDoubleSpinBox#DiscountInputSpin {
    background: #ffffff;
    border: 1px solid #d5dde7;
    border-radius: 10px;
    min-height: 28px;
    font-size: 11px;
}

QComboBox#DiscountModeCombo {
    background: #ffffff;
    border: 1px solid #d5dde7;
    border-radius: 10px;
    min-height: 28px;
    min-width: 58px;
    padding: 0 8px;
    font-size: 11px;
}

QDoubleSpinBox#DiscountAmountSpin,
QDoubleSpinBox#CashReceivedSpin {
    background: #ffffff;
    border: 1px solid #d5dde7;
    border-radius: 10px;
    min-height: 28px;
    font-size: 11px;
}

QFrame#PdvSummaryCard {
    background: #ffffff;
    border: 1px solid #d9e1ec;
    border-radius: 10px;
}

QLabel#PdvSummaryLabel {
    color: #7a889a;
    font-size: 10px;
    font-weight: 500;
}

QLabel#PdvSummaryValue {
    color: #465772;
    font-size: 13px;
    font-weight: 700;
}

QLabel#PdvTotalLabel {
    color: #0f172a;
    font-size: 13px;
    font-weight: 900;
}

QLabel#PdvTotalValue {
    color: #6159e8;
    font-size: 16px;
    font-weight: 900;
}

QLabel#PdvChangeValue {
    color: #5b6b85;
    font-size: 11px;
    font-weight: 800;
}

QLabel#PdvChangeValue[state="ok"] {
    color: #0f766e;
}

QFrame#PdvBottomActions {
    background: transparent;
    border: none;
}

QPushButton#PdvFinishButton {
    background: #635bdf;
    color: #ffffff;
    border: 1px solid #564fca;
    border-radius: 10px;
    font-size: 12px;
    font-weight: 900;
    padding: 6px 10px;
    min-height: 34px;
}

QPushButton#PdvFinishButton:hover {
    background: #5a53cf;
}

QPushButton#PdvPrintButton {
    background: #f3f5f8;
    color: #66758b;
    border: 1px solid #d8dee8;
    border-radius: 10px;
    font-size: 11px;
    font-weight: 700;
    padding: 5px 8px;
    min-width: 66px;
    min-height: 34px;
}

QPushButton#PdvPrintButton:hover {
    background: #e9eef5;
}

/* Density profiles for PDV checkout */
QWidget[pdvDensity="normal"] QLabel#PdvCartItemName { font-size: 14px; }
QWidget[pdvDensity="normal"] QLabel#PdvCartItemPrice { font-size: 12px; }
QWidget[pdvDensity="normal"] QPushButton#PayMethodButton { min-height: 30px; font-size: 12px; }
QWidget[pdvDensity="normal"] QComboBox#PdvSecondaryMethod,
QWidget[pdvDensity="normal"] QDoubleSpinBox#PdvSecondaryAmount,
QWidget[pdvDensity="normal"] QDoubleSpinBox#DiscountInputSpin,
QWidget[pdvDensity="normal"] QDoubleSpinBox#CashReceivedSpin,
QWidget[pdvDensity="normal"] QComboBox#DiscountModeCombo { min-height: 32px; font-size: 12px; }
QWidget[pdvDensity="normal"] QLabel#PdvTotalValue { font-size: 18px; }
QWidget[pdvDensity="normal"] QPushButton#PdvFinishButton,
QWidget[pdvDensity="normal"] QPushButton#PdvPrintButton { min-height: 38px; }

QWidget[pdvDensity="compact"] QLabel#PdvCartItemName { font-size: 13px; }
QWidget[pdvDensity="compact"] QLabel#PdvCartItemPrice { font-size: 12px; }
QWidget[pdvDensity="compact"] QPushButton#PayMethodButton { min-height: 28px; font-size: 11px; }
QWidget[pdvDensity="compact"] QComboBox#PdvSecondaryMethod,
QWidget[pdvDensity="compact"] QDoubleSpinBox#PdvSecondaryAmount,
QWidget[pdvDensity="compact"] QDoubleSpinBox#DiscountInputSpin,
QWidget[pdvDensity="compact"] QDoubleSpinBox#CashReceivedSpin,
QWidget[pdvDensity="compact"] QComboBox#DiscountModeCombo { min-height: 28px; font-size: 11px; }
QWidget[pdvDensity="compact"] QLabel#PdvTotalValue { font-size: 16px; }
QWidget[pdvDensity="compact"] QPushButton#PdvFinishButton,
QWidget[pdvDensity="compact"] QPushButton#PdvPrintButton { min-height: 34px; }

QWidget[pdvDensity="ultra"] QLabel#PdvCartItemName { font-size: 12px; }
QWidget[pdvDensity="ultra"] QLabel#PdvCartItemPrice { font-size: 11px; }
QWidget[pdvDensity="ultra"] QLabel#PdvSummaryLabel { font-size: 9px; }
QWidget[pdvDensity="ultra"] QLabel#PdvSummaryValue { font-size: 12px; }
QWidget[pdvDensity="ultra"] QLabel#PdvTotalLabel { font-size: 12px; }
QWidget[pdvDensity="ultra"] QLabel#PdvTotalValue { font-size: 14px; }
QWidget[pdvDensity="ultra"] QLabel#PdvChangeValue { font-size: 10px; }
QWidget[pdvDensity="ultra"] QPushButton#PayMethodButton { min-height: 25px; font-size: 10px; }
QWidget[pdvDensity="ultra"] QComboBox#PdvSecondaryMethod,
QWidget[pdvDensity="ultra"] QDoubleSpinBox#PdvSecondaryAmount,
QWidget[pdvDensity="ultra"] QDoubleSpinBox#DiscountInputSpin,
QWidget[pdvDensity="ultra"] QDoubleSpinBox#CashReceivedSpin,
QWidget[pdvDensity="ultra"] QComboBox#DiscountModeCombo { min-height: 24px; font-size: 10px; }
QWidget[pdvDensity="ultra"] QPushButton#PdvSecondaryFillRest,
QWidget[pdvDensity="ultra"] QPushButton#PdvSecondaryToggle { min-height: 22px; font-size: 10px; }
QWidget[pdvDensity="ultra"] QPushButton#PdvFinishButton,
QWidget[pdvDensity="ultra"] QPushButton#PdvPrintButton { min-height: 30px; font-size: 10px; }
QWidget[pdvDensity="ultra"] QScrollArea#PdvCartItemsScroll { min-height: 180px; }

QTableWidget#PdvPaymentsTable {
    background: #ffffff;
    alternate-background-color: #f8fafd;
    border: 1px solid #d4dde8;
    border-radius: 11px;
    selection-background-color: #e9eef7;
    selection-color: #1f3554;
}

QTableWidget#PdvPaymentsTable QHeaderView::section {
    background: #eef3f8;
    color: #42556f;
    border: none;
    border-bottom: 1px solid #d8e1ec;
    padding: 8px 8px;
    font-weight: 800;
}

QTableView::item {
    padding: 6px;
    border-bottom: 1px solid #eff4fa;
}

QHeaderView::section {
    background: #f7f9fe;
    color: #64748b;
    border: none;
    border-right: 1px solid #e9eef6;
    padding: 10px 8px;
    font-weight: 700;
    font-size: 12px;
}

QFrame#MetricTile {
    background: #ffffff;
    border: 1px solid #cfdeef;
    border-radius: 12px;
}

QFrame#MetricTile[pdvMetric="total"] {
    border: 1px solid #c8daf2;
    background: #edf3fb;
}

QFrame#MetricTile[pdvMetric="payments"] {
    border: 1px solid #d9e2ed;
    background: #f8fafd;
}

QFrame#MetricTile[pdvMetric="change"] {
    border: 1px solid #bbf7d0;
    background: #f0fdf4;
}

QFrame#MetricTile[pdvMetric="pending"] {
    border: 1px solid #fecaca;
    background: #fff7f7;
}

QFrame#MetricTile[metric="sales"] {
    border-top: 1px solid #dfe7f2;
}

QFrame#MetricTile[metric="profit"] {
    border-top: 1px solid #dfe7f2;
}

QFrame#MetricTile[metric="fees"] {
    border-top: 1px solid #dfe7f2;
}

QFrame#MetricTile[metric="count"] {
    border-top: 1px solid #dfe7f2;
}

QFrame#MetricTile[metric="cancel"] {
    border-top: 1px solid #dfe7f2;
}

QLabel#KpiBadge[metric="cancel"] {
    background: #fef2f2;
    color: #dc2626;
}

QLabel#KpiBadge {
    border-radius: 18px;
    font-size: 16px;
    font-weight: 700;
    color: #64748b;
}

QLabel#KpiBadge[metric="sales"] {
    background: #e8f1ff;
    color: #3b82f6;
}

QLabel#KpiBadge[metric="profit"] {
    background: #e9fbf5;
    color: #10b981;
}

QLabel#KpiBadge[metric="fees"] {
    background: #fff1f1;
    color: #ef4444;
}

QLabel#KpiBadge[metric="count"] {
    background: #f6f2e8;
    color: #a16207;
}

QLabel#MetricLabel {
    color: #4e6077;
    font-size: 11px;
    font-weight: 700;
}

QLabel#MetricValue {
    color: #0f172a;
    font-size: 34px;
    font-weight: 900;
}

QLabel#MetricLabel[pdvMetric="total"] {
    color: #1d4ed8;
}

QLabel#MetricLabel[pdvMetric="payments"] {
    color: #334155;
}

QLabel#MetricLabel[pdvMetric="change"] {
    color: #15803d;
}

QLabel#MetricLabel[pdvMetric="pending"] {
    color: #b91c1c;
}

QLabel#MetricValue[pdvMetric="total"] {
    color: #1e3a8a;
}

QLabel#MetricValue[pdvMetric="payments"] {
    color: #0f172a;
}

QLabel#MetricValue[pdvMetric="change"] {
    color: #166534;
}

QLabel#MetricValue[pdvMetric="pending"] {
    color: #b91c1c;
}

QLabel#MetricValue[pdvMetric="pending"][status="neutral"] {
    color: #5b6b85;
}

QLabel#MetricValue[pdvMetric="pending"][status="alert"] {
    color: #b91c1c;
}

QLabel#MetricValue[pdvMetric="change"][status="neutral"] {
    color: #5b6b85;
}

QLabel#MetricValue[pdvMetric="change"][status="positive"] {
    color: #15803d;
}

QTabBar::tab {
    background: #f1f4fb;
    color: #64748b;
    padding: 9px 14px;
    margin-right: 6px;
    border-top-left-radius: 10px;
    border-top-right-radius: 10px;
    font-weight: 700;
}

QTabBar::tab:selected {
    background: #635bff;
    color: #ffffff;
    border: 1px solid #564df1;
    border-bottom: 1px solid #ffffff;
}

QLabel#PageSubtitle {
    color: #7785a0;
    font-size: 14px;
}

QLabel#SectionTitle {
    color: #0f172a;
    font-size: 18px;
    font-weight: 800;
}

QLabel#PageGreeting {
    color: #0f172a;
    font-size: 36px;
    font-weight: 800;
}

QWidget#ManagementPage {
    background: #f4f6fb;
}

QWidget#ManagementPage QFrame#Card {
    background: #ffffff;
    border: 1px solid #e3eaf3;
    border-radius: 12px;
}

QWidget#ManagementPage QFrame[class="FilterBar"] {
    background: #ffffff;
    border: 1px solid #e3eaf3;
    border-radius: 12px;
}

QWidget#ManagementPage QLabel#PageSubtitle {
    color: #7785a0;
    font-size: 13px;
}

QWidget#ManagementPage QLabel#SectionTitle {
    color: #0f172a;
}

QWidget#ManagementPage QLineEdit,
QWidget#ManagementPage QComboBox,
QWidget#ManagementPage QDoubleSpinBox,
QWidget#ManagementPage QSpinBox,
QWidget#ManagementPage QTextEdit,
QWidget#ManagementPage QDateEdit {
    background: #ffffff;
    color: #0f172a;
    border: 1px solid #d6deea;
    border-radius: 9px;
    padding: 8px 10px;
    selection-background-color: #635bff;
}

QWidget#ManagementPage QComboBox {
    padding-right: 30px;
}

QComboBox::drop-down,
QWidget#ManagementPage QComboBox::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: center right;
    width: 28px;
    border: none;
    background: transparent;
}

QComboBox::down-arrow,
QWidget#ManagementPage QComboBox::down-arrow {
    image: url("__CHEVRON_DOWN__");
    width: 12px;
    height: 12px;
}

QComboBox QAbstractItemView,
QWidget#ManagementPage QComboBox QAbstractItemView {
    background: #ffffff;
    border: 1px solid #d6deea;
    border-radius: 8px;
    padding: 4px;
    outline: none;
    selection-background-color: #eef2ff;
    selection-color: #4338ca;
}

QWidget#ManagementPage QLineEdit:focus,
QWidget#ManagementPage QComboBox:focus,
QWidget#ManagementPage QDoubleSpinBox:focus,
QWidget#ManagementPage QSpinBox:focus,
QWidget#ManagementPage QTextEdit:focus,
QWidget#ManagementPage QDateEdit:focus {
    border: 1px solid #635bff;
}

QWidget#ManagementPage QPushButton {
    background: #635bff;
    color: #ffffff;
    border: 1px solid #564df1;
    border-radius: 9px;
    padding: 8px 13px;
    min-height: 20px;
    font-weight: 700;
}

QWidget#ManagementPage QPushButton:hover {
    background: #5a53eb;
    border-color: #5a53eb;
}

QWidget#ManagementPage QPushButton#SecondaryButton {
    background: #f8fafc;
    color: #334155;
    border: 1px solid #cbd5e1;
}

QWidget#ManagementPage QPushButton#SecondaryButton:hover {
    background: #eef2f7;
    border-color: #b9c4d2;
}

QWidget#ManagementPage QPushButton#SuccessButton {
    background: #635bff;
    border-color: #564df1;
}

QWidget#ManagementPage QPushButton#SuccessButton:hover {
    background: #5a53eb;
    border-color: #5a53eb;
}

QWidget#ManagementPage QPushButton#DangerButton {
    background: #fff7f5;
    color: #b54736;
    border: 1px solid #e8c7c0;
}

QWidget#ManagementPage QPushButton#DangerButton:hover {
    background: #fce9e5;
    border-color: #dca89d;
}

QWidget#ManagementPage QTableWidget,
QWidget#ManagementPage QTableView {
    background: #ffffff;
    alternate-background-color: #fbfcff;
    color: #334155;
    border: 1px solid #e0e7f1;
    border-radius: 10px;
    gridline-color: transparent;
    selection-background-color: #ece9ff;
    selection-color: #211f54;
}

QWidget#ManagementPage QTableWidget::item,
QWidget#ManagementPage QTableView::item {
    padding: 8px 9px;
    border-bottom: 1px solid #edf2f8;
}

QWidget#ManagementPage QHeaderView::section {
    background: #f5f8ff;
    color: #64748b;
    border: none;
    border-bottom: 1px solid #e6edf8;
    padding: 10px 9px;
    font-size: 11px;
    font-weight: 800;
}

QWidget#ManagementPage QTabWidget#SettingsTabs::pane {
    background: #ffffff;
    border: 1px solid #e3eaf3;
    border-radius: 0 8px 8px 8px;
    top: -1px;
}

QWidget#ManagementPage QTabWidget#SettingsTabs QTabBar::tab {
    background: #f1f4fb;
    color: #64748b;
    border: 1px solid #e3eaf3;
    border-bottom: none;
    border-top-left-radius: 7px;
    border-top-right-radius: 7px;
    padding: 10px 16px;
    margin-right: 4px;
    font-weight: 700;
}

QWidget#ManagementPage QTabWidget#SettingsTabs QTabBar::tab:selected {
    background: #ffffff;
    color: #635bff;
    border-color: #d6deea;
}

QWidget#ManagementPage QFrame#CashFlowMetrics {
    background: #ffffff;
    border: 1px solid #e3eaf3;
    border-left: 4px solid #2c7be5;
    border-radius: 9px;
}

QWidget#ManagementPage QLabel#CashFlowEntry {
    color: #334155;
    font-size: 18px;
    font-weight: 800;
}

QWidget#ManagementPage QLabel#CashFlowProfit {
    color: #635bff;
    font-size: 18px;
    font-weight: 800;
}

QWidget#ManagementPage QFrame#WhatsAppOfferCard {
    background: #ffffff;
    border: 1px solid #e3eaf3;
    border-top: 4px solid #635bff;
    border-radius: 12px;
}

QWidget#ManagementPage QLabel#WhatsAppTitle {
    color: #0f172a;
    font-size: 21px;
    font-weight: 800;
}

QWidget#ManagementPage QLabel#WhatsAppDescription {
    color: #64748b;
    font-size: 14px;
}

QWidget#ManagementPage QFrame#WhatsAppDivider {
    background: #e3eaf3;
    min-height: 1px;
    max-height: 1px;
}

QWidget#ManagementPage QLabel#WhatsAppCallout {
    color: #635bff;
    font-size: 13px;
    font-weight: 700;
}

QWidget#ManagementPage QLabel#WhatsAppContact {
    color: #334155;
    font-size: 14px;
    font-weight: 700;
}

QWidget#ManagementPage QFrame#ClientsToolbar,
QWidget#ManagementPage QFrame#ClientAdvancedFilters {
    background: #ffffff;
    border: 1px solid #e3eaf3;
    border-radius: 10px;
}

QWidget#ManagementPage QLineEdit#ClientSearchInput {
    min-height: 24px;
    background: #f8faff;
    border: 1px solid #d6deea;
    border-radius: 8px;
    padding: 8px 12px;
}

QWidget#ManagementPage QLineEdit#ClientSearchInput:focus {
    background: #ffffff;
    border: 1px solid #635bff;
}

QWidget#ManagementPage QPushButton#ClientSearchButton {
    background: #334155;
    border-color: #334155;
}

QWidget#ManagementPage QPushButton#ClientSearchButton:hover {
    background: #1e293b;
    border-color: #1e293b;
}

QWidget#ManagementPage QPushButton#ClientAdvancedButton {
    background: #f8fafc;
    color: #334155;
    border: 1px solid #cbd5e1;
}

QWidget#ManagementPage QPushButton#ClientAdvancedButton:hover,
QWidget#ManagementPage QPushButton#ClientAdvancedButton:checked {
    background: #ece9ff;
    color: #4338ca;
    border-color: #c7c2ff;
}

QWidget#ManagementPage QToolButton#ClientMoreActions {
    background: #334155;
    color: #ffffff;
    border: 1px solid #334155;
    border-radius: 8px;
    padding: 8px 12px;
    min-height: 20px;
    font-weight: 700;
}

QWidget#ManagementPage QToolButton#ClientMoreActions:hover,
QWidget#ManagementPage QToolButton#ClientMoreActions::menu-button:hover {
    background: #1e293b;
    border-color: #1e293b;
}

QWidget#ManagementPage QWidget#ClientRowActions {
    background: transparent;
}

QWidget#ManagementPage QPushButton#ClientRowEditButton,
QWidget#ManagementPage QPushButton#ClientRowDeleteButton {
    min-height: 18px;
    padding: 4px 8px;
    border-radius: 6px;
    font-size: 11px;
}

QWidget#ManagementPage QPushButton#ClientRowEditButton {
    background: #eef2ff;
    color: #4338ca;
    border: 1px solid #c7d2fe;
}

QWidget#ManagementPage QPushButton#ClientRowEditButton:hover {
    background: #e0e7ff;
}

QWidget#ManagementPage QPushButton#ClientRowDeleteButton {
    background: #fff7f5;
    color: #b54736;
    border: 1px solid #e8c7c0;
}

QWidget#ManagementPage QPushButton#ClientRowDeleteButton:hover {
    background: #fce9e5;
}

QWidget#ManagementPage QLabel#ClientsPageTitle {
    color: #0f172a;
    font-size: 23px;
    font-weight: 800;
}

QWidget#ManagementPage QFrame#ClientViewSwitch {
    background: #f8fafc;
    border: 1px solid #dbe2ec;
    border-radius: 9px;
}

QWidget#ManagementPage QPushButton#ClientViewToggle {
    background: transparent;
    color: #64748b;
    border: none;
    border-radius: 7px;
    padding: 7px 13px;
    min-height: 18px;
}

QWidget#ManagementPage QPushButton#ClientViewToggle:checked {
    background: #635bff;
    color: #ffffff;
}

QWidget#ManagementPage QPushButton#ClientViewToggle:hover:!checked {
    background: #eceef8;
    color: #334155;
}

QWidget#ManagementPage QPushButton#ClientNewButton {
    background: #635bff;
    border-color: #635bff;
    padding: 8px 16px;
}

QWidget#ManagementPage QPushButton#ClientNewButton:hover {
    background: #554de8;
    border-color: #554de8;
}

QWidget#ManagementPage QFrame#ClientMetricCard {
    background: #ffffff;
    border: 1px solid #e0e5ed;
    border-radius: 10px;
}

QWidget#ManagementPage QLabel#ClientMetricValue {
    color: #635bff;
    font-size: 25px;
    font-weight: 900;
}

QWidget#ManagementPage QFrame#ClientMetricCard[metric="revenue"] QLabel#ClientMetricValue {
    color: #10a889;
}

QWidget#ManagementPage QFrame#ClientMetricCard[metric="buyers"] QLabel#ClientMetricValue {
    color: #2c7be5;
}

QWidget#ManagementPage QLabel#ClientMetricCaption,
QWidget#ManagementPage QLabel#ClientCountLabel {
    color: #7785a0;
    font-size: 12px;
}

QWidget#ManagementPage QFrame#ClientsListing {
    background: #ffffff;
    border: 1px solid #dfe5ed;
    border-radius: 10px;
}

QWidget#ManagementPage QFrame#ClientsToolbar {
    background: #ffffff;
    border: none;
    border-bottom: 1px solid #e0e7f1;
    border-radius: 0;
}

QWidget#ManagementPage QLineEdit#ClientSearchInput {
    min-width: 270px;
    max-width: 360px;
    min-height: 20px;
    background: #f8fafc;
    border: 1px solid #dce3ec;
    border-radius: 8px;
    padding: 7px 10px;
}

QWidget#ManagementPage QTableWidget#ClientsTable {
    background: #ffffff;
    alternate-background-color: #ffffff;
    border: none;
    border-radius: 0;
    selection-background-color: #f0efff;
    selection-color: #1e293b;
}

QWidget#ManagementPage QTableWidget#ClientsTable::item {
    padding: 7px 8px;
    border-bottom: 1px solid #edf1f6;
}

QWidget#ManagementPage QTableWidget#ClientsTable::item:selected {
    background: #f0efff;
    color: #1e293b;
}

QWidget#ManagementPage QTableWidget#ClientsTable QHeaderView::section {
    background: #f8f9fb;
    color: #64748b;
    border: none;
    border-bottom: 1px solid #e7ebf1;
    padding: 10px 8px;
    font-size: 10px;
    font-weight: 800;
}

QWidget#ManagementPage QWidget#ClientIdentity,
QWidget#ManagementPage QWidget#ClientRowActions {
    background: transparent;
}

QWidget#ManagementPage QWidget#ClientIdentity {
    min-width: 0;
}

QWidget#ManagementPage QLabel#ClientAvatar {
    background: #eeedff;
    color: #635bff;
    border: none;
    border-radius: 9px;
    font-weight: 800;
}

QWidget#ManagementPage QLabel#ClientAvatar[avatarIndex="1"] {
    background: #e0f7f2;
    color: #0f9b82;
}

QWidget#ManagementPage QLabel#ClientAvatar[avatarIndex="2"] {
    background: #e3f1ff;
    color: #2c7be5;
}

QWidget#ManagementPage QLabel#ClientAvatar[avatarIndex="3"] {
    background: #fff0ed;
    color: #e56b55;
}

QWidget#ManagementPage QLabel#ClientAvatar[avatarIndex="4"] {
    background: #fff5e6;
    color: #d88a21;
}

QWidget#ManagementPage QLabel#ClientName {
    color: #17243b;
    font-size: 12px;
    font-weight: 700;
}

QWidget#ManagementPage QPushButton#ClientRowEditButton,
QWidget#ManagementPage QPushButton#ClientRowDeleteButton {
    min-width: 0;
    min-height: 0;
    padding: 2px 4px;
    font-size: 10px;
    border-radius: 6px;
}

QWidget#ManagementPage QScrollArea#ClientCardsScroll {
    background: #ffffff;
    border: none;
}

QWidget#ManagementPage QScrollArea#ClientCardsScroll > QWidget > QWidget {
    background: #ffffff;
}

QWidget#ManagementPage QFrame#ClientProfileCard {
    background: #fbfcfe;
    border: 1px solid #e1e7ef;
    border-radius: 10px;
    min-width: 190px;
}

QWidget#ManagementPage QFrame#ClientProfileCard:hover {
    border-color: #c7c2ff;
    background: #ffffff;
}

QWidget#ManagementPage QFrame#ClientProfileCard QPushButton#ClientEditButton,
QWidget#ManagementPage QFrame#ClientProfileCard QPushButton#ClientDeleteButton {
    min-width: 0;
    min-height: 0;
    padding: 3px 7px;
    font-size: 10px;
    font-weight: 700;
    border-radius: 6px;
}

QWidget#ManagementPage QFrame#ClientProfileCard QPushButton#ClientEditButton {
    background: #eef2ff;
    color: #4338ca;
    border: 1px solid #c7d2fe;
}

QWidget#ManagementPage QFrame#ClientProfileCard QPushButton#ClientEditButton:hover {
    background: #e0e7ff;
}

QWidget#ManagementPage QFrame#ClientProfileCard QPushButton#ClientDeleteButton {
    background: #fff0ee;
    color: #c24135;
    border: 1px solid #f1c8c3;
}

QWidget#ManagementPage QFrame#ClientProfileCard QPushButton#ClientDeleteButton:hover {
    background: #ffe2de;
}

QWidget#ManagementPage QLabel#ClientContactMarker {
    background: #eef1f7;
    color: #718096;
    border: none;
    border-radius: 6px;
    font-size: 9px;
    font-weight: 800;
}

QWidget#ManagementPage QLabel#ClientContactValue {
    color: #64748b;
    font-size: 11px;
}

QWidget#ManagementPage QFrame#ClientCardDivider {
    background: #e3e8ef;
    min-height: 1px;
    max-height: 1px;
}

QWidget#ManagementPage QLabel#ClientCardPurchaseTotal {
    color: #635bff;
    font-size: 16px;
    font-weight: 900;
}

QWidget#ManagementPage QLabel#ClientCardPurchaseCount {
    color: #7785a0;
    font-size: 10px;
}

QWidget#ManagementPage QFrame#ClientProfileCard QPushButton#ClientRowEditButton,
QWidget#ManagementPage QFrame#ClientProfileCard QPushButton#ClientRowDeleteButton {
    min-height: 0;
    padding: 2px 3px;
    font-size: 9px;
}

QWidget#ManagementPage QLabel#SuppliersPageTitle {
    color: #0f172a;
    font-size: 23px;
    font-weight: 800;
}

QWidget#ManagementPage QFrame#SupplierViewSwitch {
    background: #f8fafc;
    border: 1px solid #dbe2ec;
    border-radius: 9px;
}

QWidget#ManagementPage QPushButton#SupplierViewToggle {
    background: transparent;
    color: #64748b;
    border: none;
    border-radius: 7px;
    padding: 7px 13px;
    min-height: 18px;
}

QWidget#ManagementPage QPushButton#SupplierViewToggle:checked {
    background: #635bff;
    color: #ffffff;
}

QWidget#ManagementPage QPushButton#SupplierViewToggle:hover:!checked {
    background: #eceef8;
    color: #334155;
}

QWidget#ManagementPage QPushButton#SupplierNewButton {
    background: #635bff;
    border-color: #635bff;
    padding: 8px 16px;
}

QWidget#ManagementPage QPushButton#SupplierNewButton:hover {
    background: #554de8;
    border-color: #554de8;
}

QWidget#ManagementPage QFrame#SupplierMetricCard {
    background: #ffffff;
    border: 1px solid #e0e5ed;
    border-radius: 10px;
}

QWidget#ManagementPage QLabel#SupplierMetricValue {
    color: #635bff;
    font-size: 25px;
    font-weight: 900;
}

QWidget#ManagementPage QLabel#CashFlowPageTitle {
    color: #0f172a;
    font-size: 23px;
    font-weight: 800;
}

QWidget#ManagementPage QLabel#SettingsPageTitle {
    color: #0f172a;
    font-size: 23px;
    font-weight: 800;
}

QWidget#ManagementPage QPushButton#SettingsSaveButton {
    background: #635bff;
    border-color: #635bff;
    padding: 8px 16px;
}

QWidget#ManagementPage QPushButton#SettingsSaveButton:hover {
    background: #554de8;
    border-color: #554de8;
}

QWidget#ManagementPage QFrame#SettingsSidebar {
    background: #ffffff;
    border: 1px solid #e0e5ed;
    border-radius: 10px;
}

QWidget#ManagementPage QListWidget#SettingsMenu {
    background: transparent;
    border: none;
    outline: none;
}

QWidget#ManagementPage QListWidget#SettingsMenu::item {
    color: #53627a;
    min-height: 22px;
    padding: 9px 11px;
    margin: 2px 0;
    border-radius: 7px;
    font-size: 12px;
    font-weight: 600;
}

QWidget#ManagementPage QListWidget#SettingsMenu::item:hover {
    background: #f4f5fb;
    color: #334155;
}

QWidget#ManagementPage QListWidget#SettingsMenu::item:selected {
    background: #eeedff;
    color: #635bff;
    font-weight: 800;
}

QWidget#ManagementPage QFrame#SettingsPanel {
    background: #ffffff;
    border: 1px solid #e0e5ed;
    border-radius: 10px;
}

QWidget#ManagementPage QLabel#SettingsSectionTitle {
    color: #17243b;
    font-size: 15px;
    font-weight: 800;
}

QWidget#ManagementPage QLabel#SettingsSectionDescription {
    color: #7785a0;
    font-size: 12px;
}

QWidget#ManagementPage QLabel#SettingsFieldLabel {
    color: #718096;
    font-size: 11px;
    font-weight: 600;
}

QWidget#ManagementPage QWidget#SettingsField,
QWidget#ManagementPage QWidget#SettingsLogoWrap {
    background: transparent;
    border: none;
}

QWidget#ManagementPage QLabel#UsersPageTitle {
    color: #0f172a;
    font-size: 23px;
    font-weight: 800;
}

QWidget#ManagementPage QPushButton#UserNewButton {
    background: #635bff;
    border-color: #635bff;
    padding: 8px 16px;
}

QWidget#ManagementPage QPushButton#UserNewButton:hover {
    background: #554de8;
    border-color: #554de8;
}

QWidget#ManagementPage QFrame#UserMetricCard {
    background: #ffffff;
    border: 1px solid #e0e5ed;
    border-radius: 9px;
}

QWidget#ManagementPage QLabel#UserMetricValue {
    color: #635bff;
    font-size: 24px;
    font-weight: 900;
}

QWidget#ManagementPage QFrame#UserMetricCard[metric="active"] QLabel#UserMetricValue {
    color: #10a889;
}

QWidget#ManagementPage QFrame#UserMetricCard[metric="inactive"] QLabel#UserMetricValue {
    color: #ef5148;
}

QWidget#ManagementPage QFrame#UserMetricCard[metric="roles"] QLabel#UserMetricValue {
    color: #2c7be5;
}

QWidget#ManagementPage QLabel#UserMetricCaption,
QWidget#ManagementPage QLabel#UsersCountLabel {
    color: #7785a0;
    font-size: 11px;
}

QWidget#ManagementPage QFrame#UsersListing,
QWidget#ManagementPage QFrame#UsersSalesPanel {
    background: #ffffff;
    border: 1px solid #dfe5ed;
    border-radius: 9px;
}

QWidget#ManagementPage QLabel#UsersSectionTitle {
    color: #17243b;
    font-size: 13px;
    font-weight: 800;
}

QWidget#ManagementPage QFrame#UsersToolbar {
    background: #ffffff;
    border: none;
    border-bottom: 1px solid #e7ebf1;
}

QWidget#ManagementPage QLineEdit#UsersSearchInput {
    min-width: 260px;
    max-width: 380px;
    min-height: 19px;
    background: #f8fafc;
    border: 1px solid #dce3ec;
    border-radius: 8px;
    padding: 7px 10px;
}

QWidget#ManagementPage QTableWidget#UsersTable,
QWidget#ManagementPage QTableWidget#UsersSalesTable {
    background: #ffffff;
    alternate-background-color: #ffffff;
    border: none;
    border-radius: 0;
    selection-background-color: #f0efff;
    selection-color: #1e293b;
}

QWidget#ManagementPage QTableWidget#UsersTable::item,
QWidget#ManagementPage QTableWidget#UsersSalesTable::item {
    padding: 6px 8px;
    border-bottom: 1px solid #edf1f6;
}

QWidget#ManagementPage QTableWidget#UsersTable QHeaderView::section,
QWidget#ManagementPage QTableWidget#UsersSalesTable QHeaderView::section {
    background: #f8f9fb;
    color: #64748b;
    border: none;
    border-bottom: 1px solid #e7ebf1;
    padding: 9px 8px;
    font-size: 10px;
    font-weight: 800;
}

QWidget#ManagementPage QWidget#UserIdentity,
QWidget#ManagementPage QWidget#UserRoleCell,
QWidget#ManagementPage QWidget#UserStatusCell,
QWidget#ManagementPage QWidget#UserRowActions {
    background: transparent;
    border: none;
}

QWidget#ManagementPage QLabel#UserAvatar {
    background: #eeedff;
    color: #635bff;
    border: none;
    border-radius: 9px;
    font-weight: 800;
}

QWidget#ManagementPage QLabel#UserAvatar[avatarIndex="1"] {
    background: #e0f7f2;
    color: #0f9b82;
}

QWidget#ManagementPage QLabel#UserAvatar[avatarIndex="2"] {
    background: #e3f1ff;
    color: #2c7be5;
}

QWidget#ManagementPage QLabel#UserAvatar[avatarIndex="3"] {
    background: #fff0ed;
    color: #e56b55;
}

QWidget#ManagementPage QLabel#UserAvatar[avatarIndex="4"] {
    background: #ffe9f1;
    color: #ec5d91;
}

QWidget#ManagementPage QLabel#UserName {
    color: #17243b;
    font-size: 12px;
    font-weight: 700;
}

QWidget#ManagementPage QLabel#UserRoleBadge,
QWidget#ManagementPage QLabel#UserStatusBadge {
    min-width: 58px;
    padding: 3px 8px;
    border: none;
    border-radius: 10px;
    font-size: 10px;
    font-weight: 700;
}

QWidget#ManagementPage QLabel#UserRoleBadge[role="master"] {
    background: #fff0ed;
    color: #e56b55;
}

QWidget#ManagementPage QLabel#UserRoleBadge[role="operador"] {
    background: #e3f1ff;
    color: #2c7be5;
}

QWidget#ManagementPage QLabel#UserRoleBadge[role="caixa"] {
    background: #e0f7f2;
    color: #0f9b82;
}

QWidget#ManagementPage QLabel#UserStatusBadge[active="true"] {
    background: #e8f8f5;
    color: #0f9b82;
}

QWidget#ManagementPage QLabel#UserStatusBadge[active="false"] {
    background: #eef1f5;
    color: #718096;
}

QWidget#ManagementPage QPushButton#UserEditButton,
QWidget#ManagementPage QPushButton#UserDisableButton {
    min-width: 0;
    min-height: 0;
    padding: 3px 6px;
    font-size: 10px;
    border-radius: 6px;
}

QWidget#ManagementPage QPushButton#UserEditButton {
    background: #eef2ff;
    color: #4338ca;
    border: 1px solid #c7d2fe;
}

QWidget#ManagementPage QPushButton#UserEditButton:hover {
    background: #e0e7ff;
}

QWidget#ManagementPage QPushButton#UserDisableButton {
    background: #fff0ee;
    color: #c24135;
    border: 1px solid #f1c8c3;
}

QWidget#ManagementPage QPushButton#UserDisableButton:hover {
    background: #ffe2de;
}

QWidget#ManagementPage QPushButton#CashFlowAddButton {
    background: #635bff;
    border-color: #635bff;
    padding: 8px 16px;
}

QWidget#ManagementPage QPushButton#CashFlowAddButton:hover {
    background: #554de8;
    border-color: #554de8;
}

QWidget#ManagementPage QFrame#CashFlowFilters {
    background: #ffffff;
    border: 1px solid #e0e5ed;
    border-radius: 9px;
}

QWidget#ManagementPage QDateEdit#CashFlowDateEdit {
    min-width: 116px;
    min-height: 18px;
}

QWidget#ManagementPage QFrame#CashFlowFilters {
    border: 1px solid #e3eaf3;
    border-radius: 14px;
}

QWidget#ManagementPage QFrame#CashFlowFilters QDateEdit#ModernDateEdit {
    background: #f8faff;
    color: #334155;
    border: none;
    border-radius: 10px;
    padding: 7px 10px;
    min-width: 108px;
    font-weight: 700;
}

QWidget#ManagementPage QFrame#CashFlowFilters QDateEdit#ModernDateEdit:focus {
    border: none;
}

QWidget#ManagementPage QFrame#CashFlowFilters QPushButton#GhostButton {
    background: #f2f5fb;
    color: #5b6b85;
    border: 1px solid #dee6f1;
    border-radius: 9px;
    padding: 6px 10px;
    min-height: 16px;
    font-weight: 700;
}

QWidget#ManagementPage QFrame#CashFlowFilters QPushButton#GhostButton:hover {
    background: #e9eef8;
    color: #334155;
    border-color: #dee6f1;
}

QWidget#ManagementPage QPushButton#CashFlowQuickFilter {
    background: #f8fafc;
    color: #475569;
    border: 1px solid #dbe2ec;
    padding: 6px 10px;
    min-height: 18px;
}

QWidget#ManagementPage QPushButton#CashFlowQuickFilter:hover {
    background: #eef2ff;
    color: #4338ca;
    border-color: #c7d2fe;
}

QWidget#ManagementPage QFrame#CashFlowMetricCard {
    background: #ffffff;
    border: 1px solid #e0e5ed;
    border-left: 4px solid #10bfa5;
    border-radius: 9px;
}

QWidget#ManagementPage QFrame#CashFlowMetricCard[metric="outgoing"] {
    border-left-color: #f45b50;
}

QWidget#ManagementPage QFrame#CashFlowMetricCard[metric="profit"] {
    border-left-color: #6958e8;
}

QWidget#ManagementPage QLabel#CashFlowMetricCaption {
    color: #7785a0;
    font-size: 10px;
    font-weight: 700;
}

QWidget#ManagementPage QLabel#CashFlowMetricValue {
    color: #10a889;
    font-size: 22px;
    font-weight: 900;
}

QWidget#ManagementPage QFrame#CashFlowMetricCard[metric="outgoing"] QLabel#CashFlowMetricValue {
    color: #ef5148;
}

QWidget#ManagementPage QFrame#CashFlowMetricCard[metric="profit"] QLabel#CashFlowMetricValue {
    color: #6958e8;
}

QWidget#ManagementPage QFrame#CashFlowChartCard,
QWidget#ManagementPage QFrame#CashFlowHistory {
    background: #ffffff;
    border: 1px solid #dfe5ed;
    border-radius: 9px;
}

QWidget#ManagementPage QLabel#CashFlowChartTitle,
QWidget#ManagementPage QLabel#CashFlowSectionTitle {
    color: #17243b;
    font-size: 13px;
    font-weight: 800;
}

QWidget#ManagementPage QChartView#CashFlowChartView {
    background: transparent;
    border: none;
}

QWidget#ManagementPage QLabel#CashFlowChartEmpty {
    color: #7785a0;
    font-size: 12px;
}

QWidget#ManagementPage QTableWidget#CashFlowTable {
    background: #ffffff;
    alternate-background-color: #ffffff;
    border: none;
    border-radius: 0;
    selection-background-color: #f0efff;
    selection-color: #1e293b;
}

QWidget#ManagementPage QTableWidget#CashFlowTable::item {
    padding: 7px 8px;
    border-bottom: 1px solid #edf1f6;
}

QWidget#ManagementPage QTableWidget#CashFlowTable QHeaderView::section {
    background: #f8f9fb;
    color: #64748b;
    border: none;
    border-bottom: 1px solid #e7ebf1;
    padding: 9px 8px;
    font-size: 10px;
    font-weight: 800;
}

QWidget#ManagementPage QFrame#SupplierMetricCard[metric="linked"] QLabel#SupplierMetricValue {
    color: #10a889;
}

QWidget#ManagementPage QFrame#SupplierMetricCard[metric="unlinked"] QLabel#SupplierMetricValue {
    color: #2c7be5;
}

QWidget#ManagementPage QLabel#SupplierMetricCaption,
QWidget#ManagementPage QLabel#SupplierCountLabel {
    color: #7785a0;
    font-size: 12px;
}

QWidget#ManagementPage QFrame#SuppliersListing {
    background: #ffffff;
    border: 1px solid #dfe5ed;
    border-radius: 10px;
}

QDialog#ReceiptPreviewDialog {
    background: #f1f3f6;
}

QDialog#ReceiptPreviewDialog QLabel#ReceiptPreviewLogo {
    background: #ffffff;
    border: 1px solid #e1e6ed;
    border-radius: 8px;
    padding: 8px;
}

QDialog#ReceiptPreviewDialog QTextEdit#ReceiptPreviewText {
    background: #ffffff;
    color: #17243b;
    border: 1px solid #dce3ec;
    border-radius: 8px;
    padding: 12px;
    selection-background-color: #dcd9ff;
}
QWidget#ManagementPage QFrame#SuppliersToolbar {
    background: #ffffff;
    border: none;
    border-bottom: 1px solid #e0e7f1;
    border-radius: 0;
}

QWidget#ManagementPage QLineEdit#SupplierSearchInput {
    min-width: 270px;
    max-width: 360px;
    min-height: 20px;
    background: #f8fafc;
    border: 1px solid #dce3ec;
    border-radius: 8px;
    padding: 7px 10px;
}

QWidget#ManagementPage QTableWidget#SuppliersTable {
    background: #ffffff;
    alternate-background-color: #ffffff;
    border: none;
    border-radius: 0;
    selection-background-color: #f0efff;
    selection-color: #1e293b;
}

QWidget#ManagementPage QTableWidget#SuppliersTable::item {
    padding: 7px 8px;
    border-bottom: 1px solid #edf1f6;
}

QWidget#ManagementPage QTableWidget#SuppliersTable QHeaderView::section {
    background: #f8f9fb;
    color: #64748b;
    border: none;
    border-bottom: 1px solid #e7ebf1;
    padding: 10px 7px;
    font-size: 10px;
    font-weight: 800;
}

QWidget#ManagementPage QLabel#SupplierTableName,
QWidget#ManagementPage QWidget#SupplierRowActions {
    background: transparent;
}

QWidget#ManagementPage QFrame#SupplierProfileCard {
    background: #fbfcfe;
    border: 1px solid #e1e7ef;
    border-radius: 10px;
    min-width: 220px;
}

QWidget#ManagementPage QFrame#SupplierProfileCard:hover {
    background: #ffffff;
    border-color: #c7c2ff;
}

QWidget#ManagementPage QLabel#SupplierAvatar {
    background: #eeedff;
    color: #635bff;
    border: none;
    border-radius: 9px;
    font-size: 14px;
    font-weight: 800;
}

QWidget#ManagementPage QLabel#SupplierAvatar[avatarIndex="1"] {
    background: #e0f7f2;
    color: #0f9b82;
}

QWidget#ManagementPage QLabel#SupplierAvatar[avatarIndex="2"] {
    background: #e3f1ff;
    color: #2c7be5;
}

QWidget#ManagementPage QLabel#SupplierAvatar[avatarIndex="3"] {
    background: #fff0ed;
    color: #e56b55;
}

QWidget#ManagementPage QLabel#SupplierAvatar[avatarIndex="4"] {
    background: #fff5e6;
    color: #d88a21;
}

QWidget#ManagementPage QLabel#SupplierCardName {
    color: #17243b;
    font-size: 13px;
    font-weight: 800;
}

QWidget#ManagementPage QLabel#SupplierContactMarker {
    background: #eef1f7;
    color: #718096;
    border: none;
    border-radius: 6px;
    font-size: 9px;
    font-weight: 800;
}

QWidget#ManagementPage QLabel#SupplierContactValue {
    color: #64748b;
    font-size: 11px;
}

QWidget#ManagementPage QFrame#SupplierCardDivider {
    background: #e3e8ef;
    min-height: 1px;
    max-height: 1px;
}

QWidget#ManagementPage QLabel#SupplierLinkedCount {
    color: #7785a0;
    font-size: 11px;
}

QWidget#ManagementPage QPushButton#SupplierEditButton,
QWidget#ManagementPage QPushButton#SupplierDeleteButton {
    min-width: 0;
    min-height: 0;
    padding: 2px 4px;
    font-size: 10px;
    border-radius: 6px;
}

QWidget#ManagementPage QPushButton#SupplierEditButton {
    background: #eef2ff;
    color: #4338ca;
    border: 1px solid #c7d2fe;
}

QWidget#ManagementPage QPushButton#SupplierEditButton:hover {
    background: #e0e7ff;
}

QWidget#ManagementPage QPushButton#SupplierDeleteButton {
    background: #fff7f5;
    color: #b54736;
    border: 1px solid #e8c7c0;
}

QWidget#ManagementPage QPushButton#SupplierDeleteButton:hover {
    background: #fce9e5;
}

QWidget#ManagementPage QScrollArea#SupplierCardsScroll {
    background: #ffffff;
    border: none;
}

QWidget#ManagementPage QScrollArea#SupplierCardsScroll > QWidget > QWidget {
    background: #ffffff;
}

QWidget#ManagementPage QLabel#ProductsPageTitle {
    color: #0f172a;
    font-size: 23px;
    font-weight: 800;
}

QWidget#ManagementPage QPushButton#ProductsNewButton {
    background: #635bff;
    border-color: #635bff;
    padding: 8px 16px;
}

QWidget#ManagementPage QPushButton#ProductsNewButton:hover {
    background: #554de8;
    border-color: #554de8;
}

QWidget#ManagementPage QFrame#ProductMetricCard {
    background: #ffffff;
    border: 1px solid #e0e5ed;
    border-radius: 10px;
}

QWidget#ManagementPage QLabel#ProductMetricIcon {
    background: #eeedff;
    color: #635bff;
    border: none;
    border-radius: 10px;
    font-size: 18px;
    font-weight: 800;
}

QWidget#ManagementPage QLabel#ProductMetricIcon[metric="low"] {
    background: #fff5e6;
    color: #e68a00;
}

QWidget#ManagementPage QLabel#ProductMetricIcon[metric="value"] {
    background: #e8f8f5;
    color: #0f9b82;
}

QWidget#ManagementPage QLabel#ProductMetricCaption {
    color: #7785a0;
    font-size: 10px;
    font-weight: 700;
}

QWidget#ManagementPage QLabel#ProductMetricValue {
    color: #0f172a;
    font-size: 21px;
    font-weight: 900;
}

QWidget#ManagementPage QFrame#ProductsListing {
    background: #ffffff;
    border: 1px solid #dfe5ed;
    border-radius: 10px;
}

QWidget#ManagementPage QFrame#ProductsToolbar {
    background: #ffffff;
    border: none;
    border-bottom: 1px solid #e0e7f1;
    border-radius: 0;
}

QWidget#ManagementPage QLineEdit#ProductsSearchInput {
    min-width: 270px;
    max-width: 360px;
    min-height: 20px;
    background: #f8fafc;
    border: 1px solid #dce3ec;
    border-radius: 8px;
    padding: 7px 10px;
}

QWidget#ManagementPage QLabel#ProductsCountLabel {
    color: #7785a0;
    font-size: 12px;
}

QWidget#ManagementPage QTableWidget#ProductsTable {
    background: #ffffff;
    alternate-background-color: #ffffff;
    border: none;
    border-radius: 0;
    selection-background-color: #f0efff;
    selection-color: #1e293b;
}

QWidget#ManagementPage QTableWidget#ProductsTable::item {
    padding: 7px 8px;
    border-bottom: 1px solid #edf1f6;
}

QWidget#ManagementPage QTableWidget#ProductsTable::item:selected {
    background: #f0efff;
    color: #1e293b;
}

QWidget#ManagementPage QTableWidget#ProductsTable QHeaderView::section {
    background: #f8f9fb;
    color: #64748b;
    border: none;
    border-bottom: 1px solid #e7ebf1;
    padding: 10px 7px;
    font-size: 10px;
    font-weight: 800;
}

QWidget#ManagementPage QWidget#ProductIdentity,
QWidget#ManagementPage QWidget#ProductStatusWrap,
QWidget#ManagementPage QWidget#ProductRowActions {
    background: transparent;
    border: none;
}

QWidget#ManagementPage QLabel#ProductThumbnail {
    background: #f4f6fb;
    border: 1px solid #e3eaf3;
    border-radius: 7px;
}

QWidget#ManagementPage QLabel#ProductName {
    color: #17243b;
    font-size: 12px;
    font-weight: 700;
}

QWidget#ManagementPage QLabel#ProductDescription {
    color: #8491a5;
    font-size: 10px;
}

QWidget#ManagementPage QLabel#ProductStockBadge {
    min-width: 74px;
    max-width: 110px;
    padding: 4px 8px;
    border: none;
    border-radius: 10px;
    background: #e9fbf5;
    color: #0f8a70;
    font-size: 10px;
    font-weight: 700;
}

QWidget#ManagementPage QLabel#ProductStockBadge[status="low"] {
    background: #fff5df;
    color: #bd7200;
}

QWidget#ManagementPage QLabel#ProductStockBadge[status="empty"] {
    background: #fff0ee;
    color: #c24135;
}

QWidget#ManagementPage QPushButton#ProductRowEditButton,
QWidget#ManagementPage QPushButton#ProductRowDeleteButton {
    min-width: 0;
    min-height: 0;
    padding: 2px 4px;
    font-size: 10px;
    border-radius: 6px;
}

QWidget#ManagementPage QPushButton#ProductRowEditButton {
    background: #eef2ff;
    color: #4338ca;
    border: 1px solid #c7d2fe;
}

QWidget#ManagementPage QPushButton#ProductRowEditButton:hover {
    background: #e0e7ff;
}

QWidget#ManagementPage QPushButton#ProductRowDeleteButton {
    background: #fff7f5;
    color: #b54736;
    border: 1px solid #e8c7c0;
}

QWidget#ManagementPage QPushButton#ProductRowDeleteButton:hover {
    background: #fce9e5;
}

QLabel#DeltaPositive {
    color: #10b981;
    font-weight: 700;
}

QLabel#DeltaNegative {
    color: #ef4444;
    font-weight: 700;
}

QToolTip {
    background: #0f172a;
    color: #f8fafc;
    border: 1px solid #1e293b;
    padding: 6px;
}
"""

from pathlib import Path as _Path

from app.config import IMAGES_DIR as _IMAGES_DIR
_CHEVRON_DOWN = (_Path(_IMAGES_DIR) / "chevron_down.png").as_posix()
APP_STYLESHEET = APP_STYLESHEET.replace("__CHEVRON_DOWN__", _CHEVRON_DOWN)