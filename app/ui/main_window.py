from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
import threading
import time
from typing import Callable

import requests

try:
    import qrcode
except Exception:  # pragma: no cover
    qrcode = None

from PySide6.QtCore import QDate, QEvent, QMargins, QObject, QPointF, QSize, Qt, QTimer, Signal
from PySide6.QtGui import QAction, QColor, QCursor, QFont, QIcon, QPainter, QPalette, QPen, QPixmap, QTextCharFormat
from PySide6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QAbstractScrollArea,
    QAbstractSpinBox,
    QCalendarWidget,
    QComboBox,
    QDateEdit,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFileDialog,
    QFormLayout,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QMenu,
    QPushButton,
    QProgressDialog,
    QScrollArea,
    QSpinBox,
    QStackedWidget,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QTextEdit,
    QToolButton,
    QToolTip,
    QVBoxLayout,
    QWidget,
    QHeaderView,
)

try:
    from PySide6.QtCharts import (
        QBarCategoryAxis,
        QBarSeries,
        QBarSet,
        QChart,
        QChartView,
        QLineSeries,
        QPieSeries,
        QSplineSeries,
        QValueAxis,
    )

    QT_CHARTS_AVAILABLE = True
except Exception:  # pragma: no cover
    QT_CHARTS_AVAILABLE = False

from app.config import APP_VERSION, DEFAULT_PRODUCT_IMAGE, DEFAULT_SYSTEM_LOGO
from app.database import Database
from app.logger import log_error, log_info
from app.services.auth_service import AuthUser, hash_password
from app.services.backup_service import BackupService
from app.services.product_lookup_service import lookup_product_by_barcode
from app.services.printer_service import PrinterService, normalize_receipt_text
from app.services.sales_service import CartItem, PaymentPart, SalesService
from app.services.update_service import UpdateInfo, check_for_update, download_update, launch_update_and_exit


def _vector_icon(kind: str, color: str, size: int = 64) -> QIcon:
    """Desenha icones em vetor (nitidos em qualquer escala/DPI), sem depender de emoji ou arquivos."""
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)
    p = QPainter(pixmap)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    pen = QPen(QColor(color))
    pen.setWidthF(size * 0.1)
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
    p.setPen(pen)
    p.setBrush(Qt.BrushStyle.NoBrush)
    s = float(size)
    if kind == "search":
        p.drawEllipse(QPointF(s * 0.43, s * 0.43), s * 0.27, s * 0.27)
        p.drawLine(QPointF(s * 0.64, s * 0.64), QPointF(s * 0.86, s * 0.86))
    elif kind == "close":
        p.drawLine(QPointF(s * 0.22, s * 0.22), QPointF(s * 0.78, s * 0.78))
        p.drawLine(QPointF(s * 0.78, s * 0.22), QPointF(s * 0.22, s * 0.78))
    elif kind == "check":
        p.drawPolyline([QPointF(s * 0.2, s * 0.54), QPointF(s * 0.42, s * 0.74), QPointF(s * 0.8, s * 0.28)])
    elif kind == "user":
        p.drawEllipse(QPointF(s * 0.5, s * 0.32), s * 0.17, s * 0.17)
        p.drawArc(int(s * 0.18), int(s * 0.58), int(s * 0.64), int(s * 0.6), 0, 180 * 16)
    elif kind == "trash":
        p.drawLine(QPointF(s * 0.2, s * 0.26), QPointF(s * 0.8, s * 0.26))
        p.drawLine(QPointF(s * 0.4, s * 0.26), QPointF(s * 0.4, s * 0.14))
        p.drawLine(QPointF(s * 0.4, s * 0.14), QPointF(s * 0.6, s * 0.14))
        p.drawLine(QPointF(s * 0.6, s * 0.14), QPointF(s * 0.6, s * 0.26))
        p.drawPolyline([QPointF(s * 0.28, s * 0.26), QPointF(s * 0.33, s * 0.84), QPointF(s * 0.67, s * 0.84), QPointF(s * 0.72, s * 0.26)])
        p.drawLine(QPointF(s * 0.43, s * 0.42), QPointF(s * 0.43, s * 0.68))
        p.drawLine(QPointF(s * 0.57, s * 0.42), QPointF(s * 0.57, s * 0.68))
    elif kind == "exchange":
        p.drawLine(QPointF(s * 0.18, s * 0.34), QPointF(s * 0.82, s * 0.34))
        p.drawPolyline([QPointF(s * 0.64, s * 0.16), QPointF(s * 0.82, s * 0.34), QPointF(s * 0.64, s * 0.52)])
        p.drawLine(QPointF(s * 0.82, s * 0.68), QPointF(s * 0.18, s * 0.68))
        p.drawPolyline([QPointF(s * 0.36, s * 0.5), QPointF(s * 0.18, s * 0.68), QPointF(s * 0.36, s * 0.86)])
    p.end()
    return QIcon(pixmap)


ROLE_MENUS = {
    "MASTER": ["Dashboard", "PDV", "Produtos", "Clientes", "Fornecedores", "Whatsapp", "Fluxo de Caixa", "Configuracoes", "Usuarios"],
    "OPERADOR": ["PDV", "Produtos", "Clientes", "Whatsapp"],
    "CAIXA": ["PDV", "Produtos", "Clientes"],
}


class SpinnerWidget(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setFixedSize(64, 64)
        self._angle = 0
        self._state = "busy"
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(30)

    def set_state(self, state: str) -> None:
        self._state = state
        if state != "busy":
            self._timer.stop()
        self.update()

    def _tick(self) -> None:
        self._angle = (self._angle + 12) % 360
        self.update()

    def paintEvent(self, _event) -> None:  # type: ignore[override]
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = self.rect().adjusted(8, 8, -8, -8)
        if self._state == "busy":
            painter.setPen(QPen(QColor("#e4e4fb"), 6))
            painter.drawEllipse(rect)
            pen = QPen(QColor("#635bff"), 6)
            pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            painter.setPen(pen)
            painter.drawArc(rect, -self._angle * 16, -110 * 16)
            return
        color = QColor("#16a34a" if self._state == "ok" else "#dc2626")
        painter.setPen(QPen(color, 5, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
        painter.drawEllipse(rect)
        cx, cy = self.width() / 2, self.height() / 2
        if self._state == "ok":
            painter.drawPolyline([QPointF(cx - 10, cy), QPointF(cx - 3, cy + 8), QPointF(cx + 11, cy - 8)])
        else:
            painter.drawLine(QPointF(cx - 9, cy - 9), QPointF(cx + 9, cy + 9))
            painter.drawLine(QPointF(cx + 9, cy - 9), QPointF(cx - 9, cy + 9))


def make_responsive_page(page: QWidget) -> QScrollArea:
    """Envolve a pagina em area rolavel: em telas pequenas surgem barras de rolagem em vez de cortar o conteudo."""
    scroll = QScrollArea()
    scroll.setObjectName("ResponsivePageScroll")
    scroll.setWidgetResizable(True)
    scroll.setFrameShape(QFrame.Shape.NoFrame)
    scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
    scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
    scroll.setWidget(page)
    return scroll


class ScreenFitFilter(QObject):
    """Mantem dialogos e janelas dentro da area util do monitor em que aparecem."""

    def eventFilter(self, obj, event) -> bool:  # type: ignore[override]
        if event.type() == QEvent.Type.Show and isinstance(obj, QWidget) and obj.isWindow() and isinstance(obj, (QDialog, QMainWindow)):
            QTimer.singleShot(0, lambda w=obj: fit_window_to_screen(w))
        return False


def fit_window_to_screen(window: QWidget) -> None:
    try:
        if not window.isVisible() or window.isMaximized() or window.isFullScreen():
            return
        screen = window.screen() or QApplication.primaryScreen()
        if screen is None:
            return
        area = screen.availableGeometry()
        frame_w = max(0, window.frameGeometry().width() - window.width())
        frame_h = max(0, window.frameGeometry().height() - window.height())
        max_w, max_h = area.width() - frame_w, area.height() - frame_h
        width, height = min(window.width(), max_w), min(window.height(), max_h)
        if width != window.width() or height != window.height():
            window.setMinimumSize(min(window.minimumWidth(), width), min(window.minimumHeight(), height))
            window.resize(width, height)
        geo = window.frameGeometry()
        x = min(max(geo.x(), area.x()), area.x() + area.width() - geo.width())
        y = min(max(geo.y(), area.y()), area.y() + area.height() - geo.height())
        if x != geo.x() or y != geo.y():
            window.move(x, y)
    except RuntimeError:
        pass


def install_screen_fit(app: QApplication) -> None:
    filt = ScreenFitFilter(app)
    app.installEventFilter(filt)
    app._screen_fit_filter = filt  # type: ignore[attr-defined]


BACKUP_SEND_DEADLINE_SECONDS = 75


def run_backup_with_progress(parent: QWidget | None, destination_email: str, title: str = "Backup") -> tuple[Path | None, bool, str]:
    """Gera o backup local e tenta envia-lo por e-mail com tela animada.

    Retorna (arquivo_local, enviado, mensagem_de_erro).
    """
    service = BackupService()
    state: dict = {"status": "running", "text": "Gerando backup...", "file": None, "error": ""}

    def worker() -> None:
        try:
            state["file"] = service.create_backup_file()
        except Exception as exc:
            state["error"] = f"N?o foi poss?vel gerar o backup: {exc}"
            state["status"] = "failed"
            return
        if not (destination_email or "").strip():
            state["status"] = "no_email"
            return
        try:
            service.send_backup_email(destination_email, state["file"], lambda text: state.update(text=text))
            state["status"] = "sent"
        except Exception as exc:
            state["error"] = str(exc) or exc.__class__.__name__
            state["status"] = "failed"

    dialog = QDialog(parent)
    dialog.setWindowTitle(title)
    dialog.setModal(True)
    dialog.setWindowFlag(Qt.WindowType.WindowCloseButtonHint, False)
    dialog.setMinimumWidth(420)
    layout = QVBoxLayout(dialog)
    layout.setContentsMargins(28, 24, 28, 20)
    layout.setSpacing(12)
    spinner = SpinnerWidget()
    layout.addWidget(spinner, 0, Qt.AlignmentFlag.AlignHCenter)
    heading = QLabel("Enviando backup por e-mail")
    heading.setAlignment(Qt.AlignmentFlag.AlignCenter)
    heading.setStyleSheet("font-size: 16px; font-weight: 700;")
    status = QLabel(state["text"])
    status.setAlignment(Qt.AlignmentFlag.AlignCenter)
    status.setWordWrap(True)
    elapsed = QLabel("")
    elapsed.setAlignment(Qt.AlignmentFlag.AlignCenter)
    elapsed.setStyleSheet("color: #8b8fa8;")
    skip = QPushButton("Pular envio")
    skip.setObjectName("SecondaryButton")
    layout.addWidget(heading)
    layout.addWidget(status)
    layout.addWidget(elapsed)
    layout.addWidget(skip, 0, Qt.AlignmentFlag.AlignHCenter)

    started = time.monotonic()
    result = {"cancelled": False, "timed_out": False}
    timer = QTimer(dialog)

    def finish(delay_ms: int) -> None:
        timer.stop()
        skip.setEnabled(False)
        QTimer.singleShot(delay_ms, dialog.accept)

    def poll() -> None:
        seconds = int(time.monotonic() - started)
        elapsed.setText(f"{seconds}s")
        status.setText(state["text"])
        current = state["status"]
        if current == "sent":
            spinner.set_state("ok")
            heading.setText("Backup enviado com sucesso!")
            status.setText(f"Enviado para {destination_email}")
            finish(1200)
        elif current in ("failed", "no_email"):
            finish(0)
        elif seconds >= BACKUP_SEND_DEADLINE_SECONDS:
            result["timed_out"] = True
            finish(0)

    def on_skip() -> None:
        result["cancelled"] = True
        finish(0)

    skip.clicked.connect(on_skip)
    timer.timeout.connect(poll)
    timer.start(150)
    threading.Thread(target=worker, daemon=True).start()
    dialog.exec()

    backup_file = state["file"]
    if state["status"] == "sent":
        log_info(f"Backup enviado por e-mail para {destination_email}")
        return backup_file, True, ""
    if state["status"] == "no_email":
        return backup_file, False, "Nenhum e-mail de backup cadastrado em Configura??es > Empresa."
    if result["cancelled"]:
        return backup_file, False, "Envio cancelado pelo usu?rio."
    if result["timed_out"]:
        log_error("Backup: tempo limite de envio excedido")
        return backup_file, False, "Tempo limite de envio excedido."
    log_error(f"Backup: falha no envio - {state['error']}")
    return backup_file, False, state["error"] or "Falha desconhecida."


def show_backup_failure(parent: QWidget | None, backup_file: Path | None, reason: str) -> None:
    if backup_file is not None:
        text = (
            "N?o foi poss?vel enviar o backup por e-mail.\n"
            f"Motivo: {reason}\n\n"
            f"Mas n?o se preocupe: o backup foi salvo na pasta de backups:\n{backup_file}"
        )
    else:
        text = f"N?o foi poss?vel gerar o backup.\nMotivo: {reason}"
    QMessageBox.warning(parent, "Backup", text)


def pick_date_dialog(parent: QWidget | None, current: QDate, title: str) -> QDate | None:
    dlg = QDialog(parent)
    dlg.setWindowTitle(title)
    dlg.resize(360, 340)
    dlg.setStyleSheet(
        "QDialog { background: #f8faff; }"
        "QCalendarWidget {"
        "  background: white;"
        "  border: 1px solid #dbe5f2;"
        "  border-radius: 12px;"
        "}"
        "QCalendarWidget QWidget#qt_calendar_navigationbar {"
        "  background: #f1f5ff;"
        "  border-bottom: 1px solid #e2e8f0;"
        "}"
        "QCalendarWidget QToolButton {"
        "  color: #334155;"
        "  font-weight: 700;"
        "  border: none;"
        "  background: transparent;"
        "  padding: 4px 8px;"
        "}"
        "QCalendarWidget QMenu {"
        "  background: #ffffff;"
        "  border: 1px solid #dbe5f2;"
        "}"
        "QCalendarWidget QSpinBox {"
        "  border: 1px solid #dbe5f2;"
        "  border-radius: 8px;"
        "  padding: 2px 6px;"
        "  background: white;"
        "}"
        "QCalendarWidget QAbstractItemView:enabled {"
        "  selection-background-color: #635bff;"
        "  selection-color: white;"
        "  color: #1e293b;"
        "  border: none;"
        "}"
        "QCalendarWidget QAbstractItemView:item:selected {"
        "  background: #635bff;"
        "  color: #ffffff;"
        "  border-radius: 6px;"
        "}"
        "QCalendarWidget QAbstractItemView:item:hover {"
        "  background: #eef2ff;"
        "  color: #334155;"
        "  border-radius: 6px;"
        "}"
        "QPushButton {"
        "  background: #635bff; color: white; border: 1px solid #564df1;"
        "  border-radius: 10px; padding: 7px 12px; font-weight: 700;"
        "}"
        "QPushButton:hover { background: #5a53eb; }"
        ""
    )
    layout = QVBoxLayout(dlg)

    calendar = QCalendarWidget()
    calendar.setSelectedDate(current)
    calendar.setVerticalHeaderFormat(QCalendarWidget.VerticalHeaderFormat.NoVerticalHeader)

    pal = calendar.palette()
    pal.setColor(QPalette.ColorRole.Highlight, QColor("#635bff"))
    pal.setColor(QPalette.ColorRole.HighlightedText, QColor("#ffffff"))
    calendar.setPalette(pal)

    today_fmt = QTextCharFormat()
    today_fmt.setBackground(QColor("#e8edff"))
    today_fmt.setForeground(QColor("#4338ca"))
    today_fmt.setFontWeight(QFont.Weight.Bold)
    calendar.setDateTextFormat(QDate.currentDate(), today_fmt)
    layout.addWidget(calendar)

    btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
    btns.accepted.connect(dlg.accept)
    btns.rejected.connect(dlg.reject)
    layout.addWidget(btns)

    if dlg.exec() == QDialog.DialogCode.Accepted:
        return calendar.selectedDate()
    return None


class MainWindow(QMainWindow):
    def __init__(self, db: Database, current_user: AuthUser) -> None:
        super().__init__()
        self.db = db
        self.current_user = current_user
        self.sales_service = SalesService(db)
        self.backup_service = BackupService()
        self.setWindowTitle("Gestao Inteligente 3.0")
        if Path(DEFAULT_SYSTEM_LOGO).exists():
            self.setWindowIcon(QIcon(str(DEFAULT_SYSTEM_LOGO)))
        screen = QApplication.screenAt(QCursor.pos()) or QApplication.primaryScreen()
        available = screen.availableGeometry() if screen else None
        if available:
            self.setMinimumSize(min(900, available.width()), min(600, available.height()))
        self._build_ui()
        if available:
            width = min(available.width(), max(self.minimumWidth(), int(available.width() * 0.94)))
            height = min(available.height(), max(self.minimumHeight(), int(available.height() * 0.92)))
            self.resize(width, height)
            self.move(
                available.x() + (available.width() - width) // 2,
                available.y() + (available.height() - height) // 2,
            )

    def _build_ui(self) -> None:
        root = QWidget()
        main = QHBoxLayout(root)
        main.setContentsMargins(0, 0, 0, 0)
        main.setSpacing(0)

        sidebar = QFrame()
        sidebar.setObjectName("Sidebar")
        side_layout = QVBoxLayout(sidebar)
        side_layout.setContentsMargins(14, 16, 14, 16)
        side_layout.setSpacing(8)

        brand = QFrame()
        brand.setObjectName("SidebarBrand")
        brand_layout = QVBoxLayout(brand)
        brand_layout.setContentsMargins(10, 10, 10, 10)
        self.sidebar_logo = QLabel()
        self.sidebar_logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        brand_layout.addWidget(self.sidebar_logo)
        self.refresh_brand_logo()
        side_layout.addWidget(brand)

        user_card = QFrame()
        user_card.setObjectName("SidebarUserCard")
        user_card_layout = QVBoxLayout(user_card)
        user_card_layout.setContentsMargins(8, 8, 8, 8)
        user_lbl = QLabel(f"{self.current_user.name}\nPerfil: {self.current_user.role}")
        user_lbl.setStyleSheet("color: #dbeafe; font-weight: 700;")
        user_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        user_card_layout.addWidget(user_lbl)
        side_layout.addWidget(user_card)

        self.menu_list = QListWidget()
        self.menu_list.setObjectName("SidebarMenu")
        self.menu_list.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.menu_list.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        side_layout.addWidget(self.menu_list, 1)

        btn_logout = QPushButton("Sair")
        btn_logout.setObjectName("SecondaryButton")
        btn_logout.clicked.connect(self.close)
        side_layout.addWidget(btn_logout)

        content_wrap = QWidget()
        content_layout = QVBoxLayout(content_wrap)
        content_layout.setContentsMargins(18, 18, 18, 18)
        self.stack = QStackedWidget()
        content_layout.addWidget(self.stack)

        sidebar.setMinimumWidth(180)
        sidebar.setMaximumWidth(260)
        main.addWidget(sidebar, 1)
        main.addWidget(content_wrap, 5)
        self.setCentralWidget(root)

        self.pages: dict[str, QWidget] = {
            "Dashboard": DashboardPage(self.db, self.current_user),
            "PDV": PdvPage(self.db, self.current_user, self.sales_service),
            "Produtos": ProductsPage(self.db, self.current_user),
            "Clientes": ClientsPage(self.db),
            "Fornecedores": SuppliersPage(self.db),
            "Whatsapp": WhatsappPage(),
            "Fluxo de Caixa": CashFlowPage(self.db),
            "Configuracoes": SettingsPage(self.db, on_saved=self.refresh_brand_logo),
            "Usuarios": UsersPage(self.db),
        }
        self.pages["Dashboard"].on_exchange = self._start_exchange
        allowed = ROLE_MENUS.get(self.current_user.role, [])
        for key in allowed:
            self.menu_list.addItem(QListWidgetItem(key))
            self.stack.addWidget(make_responsive_page(self.pages[key]))
        self._menu_keys = list(allowed)
        self.menu_list.currentRowChanged.connect(self._on_menu_changed)
        if self.menu_list.count() > 0:
            self.menu_list.setCurrentRow(0)
        QTimer.singleShot(1500, self._run_daily_backup)
        QTimer.singleShot(2500, self._check_for_updates)

    def _check_for_updates(self) -> None:
        """Verifica em segundo plano se ha uma versao mais nova publicada no GitHub."""
        def work() -> None:
            try:
                info = check_for_update()
            except Exception:
                info = None
            if info is not None:
                QTimer.singleShot(0, lambda: self._prompt_update(info))

        threading.Thread(target=work, daemon=True).start()

    def _prompt_update(self, info: UpdateInfo) -> None:
        answer = QMessageBox.question(
            self,
            "Atualização disponível",
            f"Uma nova versão do sistema está disponível: v{info.version} (atual: v{APP_VERSION}).\n\n"
            "Deseja atualizar agora?\n"
            "O sistema será fechado e a atualização será aplicada. Seus dados serão mantidos.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes,
        )
        if answer == QMessageBox.StandardButton.Yes:
            self._run_update(info)

    def _run_update(self, info: UpdateInfo) -> None:
        dialog = QDialog(self)
        dialog.setWindowTitle("Atualizando sistema")
        dialog.setModal(True)
        dialog.setWindowFlag(Qt.WindowType.WindowCloseButtonHint, False)
        dialog.setMinimumWidth(420)
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(28, 24, 28, 20)
        layout.setSpacing(12)
        spinner = SpinnerWidget()
        layout.addWidget(spinner, 0, Qt.AlignmentFlag.AlignHCenter)
        heading = QLabel(f"Baixando atualização v{info.version}...")
        heading.setAlignment(Qt.AlignmentFlag.AlignCenter)
        heading.setStyleSheet("font-size: 16px; font-weight: 700;")
        status = QLabel("Conectando...")
        status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        status.setWordWrap(True)
        layout.addWidget(heading)
        layout.addWidget(status)

        state: dict = {"file": None, "error": ""}

        def work() -> None:
            try:
                def on_progress(done: int, total: int) -> None:
                    if total > 0:
                        state["text"] = f"Baixando... {done * 100 // total}% ({done // (1024 * 1024)} de {total // (1024 * 1024)} MB)"
                    else:
                        state["text"] = f"Baixando... {done // (1024 * 1024)} MB"
                state["file"] = download_update(info, on_progress)
            except Exception as exc:
                state["error"] = str(exc) or exc.__class__.__name__

        timer = QTimer(dialog)

        def poll() -> None:
            status.setText(state.get("text", "Conectando..."))
            if state["file"] is not None:
                timer.stop()
                spinner.set_state("ok")
                heading.setText("Download concluído!")
                status.setText("Abrindo o atualizador. O sistema será fechado.")
                QTimer.singleShot(1200, lambda: launch_update_and_exit(state["file"]))
            elif state["error"]:
                timer.stop()
                dialog.reject()

        timer.timeout.connect(poll)
        timer.start(150)
        threading.Thread(target=work, daemon=True).start()
        dialog.exec()

        if state["error"]:
            log_error(f"Auto-update: falha ao baixar atualizacao - {state['error']}")
            QMessageBox.warning(
                self,
                "Atualização",
                "Não foi possível baixar a atualização.\n"
                f"Motivo: {state['error']}\n\n"
                "O sistema continuará funcionando normalmente na versão atual.",
            )

    def _run_daily_backup(self) -> None:
        """Gera um backup local silencioso uma vez por dia, sem travar a abertura do sistema."""
        if self.backup_service.backup_exists_for_today():
            return

        def work() -> None:
            try:
                self.backup_service.create_backup_file()
            except Exception:
                pass  # backup diario e silencioso; o backup ao fechar continua ativo

        threading.Thread(target=work, daemon=True).start()

    def _start_exchange(self, sale_id: int, cart: list[dict], client_id: int | None, original_total: float) -> None:
        if "PDV" not in self._menu_keys:
            return
        self.menu_list.setCurrentRow(self._menu_keys.index("PDV"))
        self.pages["PDV"].load_exchange(sale_id, cart, client_id, original_total)

    def _on_menu_changed(self, row: int) -> None:
        if row < 0 or row >= len(self._menu_keys):
            return
        page = self.pages[self._menu_keys[row]]
        refresh = getattr(page, "refresh", None)
        if callable(refresh):
            refresh()
        self.stack.setCurrentIndex(row)

    def refresh_brand_logo(self) -> None:
        pixmap = QPixmap(_resolve_logo_path(self.db))
        if pixmap.isNull():
            self.sidebar_logo.clear()
            return
        scaled = pixmap.scaled(170, 90, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        self.sidebar_logo.setPixmap(scaled)

    def closeEvent(self, event) -> None:  # type: ignore[override]
        if getattr(self, "_closing_done", False):
            event.accept()
            return
        company = self.db.fetch_one("SELECT email FROM company_config WHERE id = 1")
        destination = (company["email"] if company else "") or ""
        backup_file, sent, reason = run_backup_with_progress(self, destination, "Encerrando sistema")
        if not sent and destination.strip():
            show_backup_failure(self, backup_file, reason)
        elif not sent and backup_file is None:
            show_backup_failure(self, None, reason)
        self._closing_done = True
        event.accept()


def _build_pix_payload(key: str, amount: float, merchant: str, city: str = "BRASIL") -> str:
    def tlv(tag: str, value: str) -> str:
        return f"{tag}{len(value):02d}{value}"

    def clean(text: str, size: int) -> str:
        import unicodedata

        ascii_text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
        return (ascii_text.strip().upper() or "NA")[:size]

    account = tlv("00", "br.gov.bcb.pix") + tlv("01", key)
    payload = tlv("00", "01") + tlv("26", account) + tlv("52", "0000") + tlv("53", "986")
    if amount > 0:
        payload += tlv("54", f"{amount:.2f}")
    payload += tlv("58", "BR") + tlv("59", clean(merchant, 25)) + tlv("60", clean(city, 15))
    payload += tlv("62", tlv("05", "***")) + "6304"
    crc = 0xFFFF
    for byte in payload.encode("ascii"):
        crc ^= byte << 8
        for _ in range(8):
            crc = ((crc << 1) ^ 0x1021) & 0xFFFF if crc & 0x8000 else (crc << 1) & 0xFFFF
    return payload + f"{crc:04X}"

class BasePage(QWidget):
    def _title(self, text: str, subtitle: str = "") -> QWidget:
        wrap = QFrame()
        wrap.setObjectName("Card")
        layout = QVBoxLayout(wrap)
        title = QLabel(text)
        title.setStyleSheet("font-size: 24px; font-weight: 800;")
        layout.addWidget(title)
        if subtitle:
            sub = QLabel(subtitle)
            sub.setStyleSheet("color:#64748b;")
            layout.addWidget(sub)
        return wrap


class DashboardPage(BasePage):
    def __init__(self, db: Database, user: AuthUser | None = None) -> None:
        super().__init__()
        self.db = db
        self.user = user
        self.sales_service = SalesService(db)
        self.printer_service = PrinterService()
        self.on_exchange = None
        self._build()
        self.refresh()

    def _build(self) -> None:
        page_layout = QVBoxLayout(self)
        page_layout.setContentsMargins(0, 0, 0, 0)
        page_layout.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        content = QWidget()
        root = QVBoxLayout(content)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(8)

        scroll.setWidget(content)
        page_layout.addWidget(scroll)

        hero = QFrame()
        hero.setObjectName("Card")
        hero_layout = QVBoxLayout(hero)
        greet = QLabel("Ola, Admin")
        greet.setObjectName("PageGreeting")
        subtitle = QLabel("Acompanhe o desempenho comercial da sua empresa em tempo real.")
        subtitle.setObjectName("PageSubtitle")
        hero_layout.addWidget(greet)
        hero_layout.addWidget(subtitle)
        root.addWidget(hero)

        filters = QFrame()
        filters.setObjectName("Card")
        filters.setProperty("class", "FilterBar")
        fl = QHBoxLayout(filters)
        fl.setContentsMargins(12, 10, 12, 10)
        fl.setSpacing(8)
        self.date_start = QDateEdit()
        self.date_start.setObjectName("ModernDateEdit")
        self.date_start.setCalendarPopup(False)
        self.date_start.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        self.date_end = QDateEdit()
        self.date_end.setObjectName("ModernDateEdit")
        self.date_end.setCalendarPopup(False)
        self.date_end.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        self.date_start.setDate(QDate.currentDate().addDays(-(QDate.currentDate().day() - 1)))
        self.date_end.setDate(QDate.currentDate())

        btn_today = QPushButton("Hoje")
        btn_today.setObjectName("GhostButton")
        btn_today.clicked.connect(self._set_range_today)
        btn_week = QPushButton("7 dias")
        btn_week.setObjectName("GhostButton")
        btn_week.clicked.connect(self._set_range_week)
        btn_month = QPushButton("Este mes")
        btn_month.setObjectName("GhostButton")
        btn_month.clicked.connect(self._set_range_month)

        btn_start_cal = QToolButton()
        btn_start_cal.setObjectName("CalendarHintButton")
        btn_start_cal.setIcon(make_calendar_icon())
        btn_start_cal.setIconSize(QSize(14, 14))
        btn_start_cal.setAutoRaise(False)
        btn_start_cal.setToolTip("Abrir calendario da data inicial")
        btn_start_cal.clicked.connect(self._show_start_calendar)

        btn_end_cal = QToolButton()
        btn_end_cal.setObjectName("CalendarHintButton")
        btn_end_cal.setIcon(make_calendar_icon())
        btn_end_cal.setIconSize(QSize(14, 14))
        btn_end_cal.setAutoRaise(False)
        btn_end_cal.setToolTip("Abrir calendario da data final")
        btn_end_cal.clicked.connect(self._show_end_calendar)

        start_field = QFrame()
        start_field.setObjectName("DateFieldWrap")
        start_layout = QHBoxLayout(start_field)
        start_layout.setContentsMargins(0, 0, 0, 0)
        start_layout.setSpacing(0)
        start_layout.addWidget(self.date_start)
        start_layout.addWidget(btn_start_cal)

        end_field = QFrame()
        end_field.setObjectName("DateFieldWrap")
        end_layout = QHBoxLayout(end_field)
        end_layout.setContentsMargins(0, 0, 0, 0)
        end_layout.setSpacing(0)
        end_layout.addWidget(self.date_end)
        end_layout.addWidget(btn_end_cal)

        btn = QPushButton("Filtrar")
        btn.clicked.connect(self.refresh)

        fl.addWidget(QLabel("Inicio"))
        fl.addWidget(start_field)
        fl.addWidget(QLabel("Fim"))
        fl.addWidget(end_field)
        fl.addSpacing(8)
        fl.addWidget(btn_today)
        fl.addWidget(btn_week)
        fl.addWidget(btn_month)
        fl.addStretch()
        fl.addWidget(btn)
        root.addWidget(filters)

        kpi_row = QHBoxLayout()
        self.kpi_sales_title, self.lbl_sales, self.lbl_sales_delta, card_sales = self._make_kpi_card("FATURAMENTO", "sales", "💳")
        self.kpi_profit_title, self.lbl_profit, self.lbl_profit_delta, card_profit = self._make_kpi_card("LUCRO LIQUIDO", "profit", "📈")
        self.kpi_fees_title, self.lbl_fees, self.lbl_fees_delta, card_fees = self._make_kpi_card("TAXAS PAGAS", "fees", "🧾")
        self.kpi_count_title, self.lbl_count, self.lbl_count_delta, card_count = self._make_kpi_card("TOTAL VENDAS", "count", "🛒")
        self.kpi_count_title, self.lbl_count, self.lbl_count_delta, card_count = self._make_kpi_card("TOTAL VENDAS", "count", "🛒")
        self.kpi_cancel_title, self.lbl_cancelled, self.lbl_cancelled_delta, card_cancel = self._make_kpi_card("PEDIDOS CANCELADOS", "cancel", "🚫")
        card_sales.setProperty("metric", "sales")
        card_profit.setProperty("metric", "profit")
        card_fees.setProperty("metric", "fees")
        card_count.setProperty("metric", "count")
        card_cancel.setProperty("metric", "cancel")
        kpi_row.addWidget(card_sales)
        kpi_row.addWidget(card_profit)
        kpi_row.addWidget(card_fees)
        kpi_row.addWidget(card_count)
        kpi_row.addWidget(card_cancel)
        root.addLayout(kpi_row)

        chart_area = QHBoxLayout()
        self.sales_chart_card = QFrame()
        self.sales_chart_card.setObjectName("Card")
        sales_chart_layout = QVBoxLayout(self.sales_chart_card)
        sales_title = QLabel("Evolucao Financeira")
        sales_title.setStyleSheet("font-size:24px;font-weight:800;color:#0f172a;")
        sales_sub = QLabel("Faturamento vs Lucro Liquido")
        sales_sub.setObjectName("PageSubtitle")
        sales_chart_layout.addWidget(sales_title)
        sales_chart_layout.addWidget(sales_sub)

        self.payment_chart_card = QFrame()
        self.payment_chart_card.setObjectName("Card")
        payment_chart_layout = QVBoxLayout(self.payment_chart_card)
        payment_title = QLabel("Canais de Vendas")
        payment_title.setStyleSheet("font-size:24px;font-weight:800;color:#0f172a;")
        payment_sub = QLabel("Distribuicao por canal")
        payment_sub.setObjectName("PageSubtitle")
        payment_chart_layout.addWidget(payment_title)
        payment_chart_layout.addWidget(payment_sub)

        if QT_CHARTS_AVAILABLE:
            self.sales_chart_view = QChartView()
            self.sales_chart_view.setMinimumHeight(280)
            self.sales_chart_view.setRenderHint(QPainter.RenderHint.Antialiasing, True)
            self.sales_chart_view.setStyleSheet("background: transparent; border: none;")
            self.sales_chart_view.setFrameShape(QFrame.Shape.NoFrame)
            self.payment_chart_view = QChartView()
            self.payment_chart_view.setMinimumHeight(280)
            self.payment_chart_view.setRenderHint(QPainter.RenderHint.Antialiasing, True)
            self.payment_chart_view.setStyleSheet("background: transparent; border: none;")
            self.payment_chart_view.setFrameShape(QFrame.Shape.NoFrame)
            sales_chart_layout.addWidget(self.sales_chart_view, 1)
            payment_chart_layout.addWidget(self.payment_chart_view, 1)
        else:
            lbl = QLabel("Modulo de graficos QtCharts nao disponivel no ambiente.")
            lbl.setStyleSheet("font-weight:700;color:#475569;")
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            sales_chart_layout.addWidget(lbl)

        chart_area.addWidget(self.sales_chart_card, 2)
        chart_area.addWidget(self.payment_chart_card, 1)
        root.addLayout(chart_area)

        recents_card = QFrame()
        recents_card.setObjectName("Card")
        recents_layout = QVBoxLayout(recents_card)
        recents_header = QHBoxLayout()
        recents_title = QLabel("Ultimas Vendas")
        recents_title.setStyleSheet("font-size:24px;font-weight:800;color:#0f172a;")
        recents_header.addWidget(recents_title)
        recents_header.addStretch()
        btn_history = QPushButton("Historico Completo")
        btn_history.setObjectName("GhostButton")
        btn_history.clicked.connect(self._show_full_sales_history)
        recents_header.addWidget(btn_history)
        recents_layout.addLayout(recents_header)
        self.table = QTableWidget(0, 6)
        self.table.setObjectName("RecentSalesTable")
        self.table.setHorizontalHeaderLabels(["Pedido", "Cliente", "Produto", "Valor", "Status", "Data"])
        apply_table_preset(self.table)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.table.setWordWrap(False)
        self.table.setTextElideMode(Qt.TextElideMode.ElideRight)
        self.table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        self.table.setMinimumHeight(260)
        self.table.setSizeAdjustPolicy(QAbstractScrollArea.SizeAdjustPolicy.AdjustToContents)
        self.table.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        recents_layout.addWidget(self.table)
        root.addWidget(recents_card, 1)

    def _set_range_today(self) -> None:
        today = QDate.currentDate()
        self.date_start.setDate(today)
        self.date_end.setDate(today)
        self.refresh()

    def _set_range_week(self) -> None:
        today = QDate.currentDate()
        self.date_start.setDate(today.addDays(-6))
        self.date_end.setDate(today)
        self.refresh()

    def _set_range_month(self) -> None:
        today = QDate.currentDate()
        self.date_start.setDate(today.addDays(-(today.day() - 1)))
        self.date_end.setDate(today)
        self.refresh()

    def _show_start_calendar(self) -> None:
        selected = self._pick_date(self.date_start.date(), "Selecionar Data Inicial")
        if selected is not None:
            self.date_start.setDate(selected)
            self.refresh()

    def _show_end_calendar(self) -> None:
        selected = self._pick_date(self.date_end.date(), "Selecionar Data Final")
        if selected is not None:
            self.date_end.setDate(selected)
            self.refresh()

    def _pick_date(self, current: QDate, title: str) -> QDate | None:
        return pick_date_dialog(self, current, title)

    def _make_kpi_card(self, title_text: str, metric: str, icon_text: str) -> tuple[QLabel, QLabel, QLabel, QFrame]:
        card = QFrame()
        card.setObjectName("MetricTile")
        card.setProperty("metric", metric)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(18, 14, 18, 14)
        layout.setSpacing(6)

        top = QHBoxLayout()
        top.setSpacing(8)
        title = QLabel(title_text)
        title.setStyleSheet("color:#64748b;font-weight:800;font-size:11px;")
        icon = QLabel(icon_text)
        icon.setObjectName("KpiBadge")
        icon.setProperty("metric", metric)
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon.setFixedSize(36, 36)
        top.addWidget(title)
        top.addStretch()
        top.addWidget(icon)

        value = QLabel("R$ 0,00")
        value.setStyleSheet("font-size:31px;font-weight:800;color:#0f172a;")
        delta = QLabel("--")
        delta.setStyleSheet("font-weight:700;color:#0ea5a4;")
        layout.addLayout(top)
        layout.addWidget(value)
        layout.addWidget(delta)
        return title, value, delta, card

    def refresh(self) -> None:
        start = self.date_start.date().toString("yyyy-MM-dd")
        end = self.date_end.date().toString("yyyy-MM-dd")
        summary = self.db.fetch_one(
            """
            SELECT
                COALESCE(SUM(net_total),0) net,
                COALESCE(SUM(fee_total),0) fees,
                COALESCE(SUM(profit_total),0) profit,
                COUNT(*) qtd
            FROM sales
            WHERE DATE(created_at) BETWEEN ? AND ? AND status <> 'CANCELADA'
            """,
            (start, end),
        )
        # Cancelamentos com motivo contendo "pedido teste" nao entram na contagem
        # (cliente apenas testando o sistema ou venda feita por engano).
        cancelled = self.db.fetch_one(
            """
            SELECT COUNT(*) qtd, COALESCE(SUM(net_total),0) total
            FROM sales
            WHERE DATE(created_at) BETWEEN ? AND ? AND status = 'CANCELADA'
              AND LOWER(COALESCE(cancel_reason,'')) NOT LIKE '%pedido teste%'
            """,
            (start, end),
        )
        self.lbl_cancelled.setText(str(int(cancelled["qtd"] or 0)))
        self.lbl_cancelled_delta.setText(f"{fmt_money(cancelled['total'])} nao contabilizados")
        self.lbl_cancelled_delta.setStyleSheet("color:#ef4444;font-weight:700;")
        self.lbl_cancelled.setToolTip("Cancelamentos com motivo 'pedido teste' nao sao contabilizados.")
        self.lbl_cancelled_delta.setToolTip("Cancelamentos com motivo 'pedido teste' nao sao contabilizados.")
        self.lbl_sales.setText(fmt_money(summary["net"]))
        self.lbl_fees.setText(fmt_money(summary["fees"]))
        self.lbl_profit.setText(fmt_money(summary["profit"]))
        self.lbl_count.setText(str(summary["qtd"]))

        net = float(summary["net"] or 0.0)
        profit = float(summary["profit"] or 0.0)
        fees = float(summary["fees"] or 0.0)
        qtd = int(summary["qtd"] or 0)
        margin = (profit / net * 100) if net > 0 else 0.0
        fee_ratio = (fees / net * 100) if net > 0 else 0.0
        self._apply_kpi_palette(net, profit, margin, fee_ratio, qtd)

        rows = self.db.fetch_all(
            """
            SELECT DATE(created_at) dt,
                ROUND(SUM(net_total),2) net,
                ROUND(SUM(fee_total),2) fees,
                ROUND(SUM(profit_total),2) profit
            FROM sales
            WHERE DATE(created_at) BETWEEN ? AND ? AND status <> 'CANCELADA'
            GROUP BY DATE(created_at)
            ORDER BY dt DESC
            """,
            (start, end),
        )
        latest_sales = self.db.fetch_all(
            """
            SELECT s.id, s.created_at, COALESCE(c.name,'Consumidor Final') AS client,
                     COALESCE(MAX(p.name),'Venda PDV') AS product,
                   s.net_total, s.profit_total
            FROM sales s
            LEFT JOIN clients c ON c.id = s.client_id
            LEFT JOIN sale_items si ON si.sale_id = s.id
            LEFT JOIN products p ON p.id = si.product_id
            WHERE s.status <> 'CANCELADA'
                 GROUP BY s.id, s.created_at, c.name, s.net_total, s.profit_total
            ORDER BY s.created_at DESC
                LIMIT 10
            """
        )
        table_rows = []
        for sale in latest_sales:
            status = "Pago" if float(sale["profit_total"] or 0.0) >= 0 else "Pendente"
            table_rows.append(
                [
                    f"#{sale['id']}",
                    sale["client"],
                    sale["product"],
                    fmt_money(sale["net_total"]),
                    status,
                    fmt_date_br(str(sale["created_at"])),
                ]
            )
        fill_table(self.table, table_rows)
        self._style_sales_table()

        if QT_CHARTS_AVAILABLE:
            self._update_charts(rows, start, end)

    def _apply_kpi_palette(self, net: float, profit: float, margin: float, fee_ratio: float, qtd: int) -> None:
        self.kpi_sales_title.setStyleSheet("color:#64748b;font-weight:800;font-size:11px;")
        self.kpi_profit_title.setStyleSheet("color:#64748b;font-weight:800;font-size:11px;")
        self.kpi_fees_title.setStyleSheet("color:#64748b;font-weight:800;font-size:11px;")
        self.kpi_count_title.setStyleSheet("color:#64748b;font-weight:800;font-size:11px;")

        self.lbl_sales.setStyleSheet("font-size:31px;font-weight:800;color:#0f172a;")
        self.lbl_sales_delta.setText(f"↗ {max(0.0, margin):.1f}% este mes")
        self.lbl_sales_delta.setStyleSheet("color:#10b981;font-weight:700;")

        profit_color = "#16a34a" if profit >= 0 else "#dc2626"
        self.lbl_profit.setStyleSheet("font-size:31px;font-weight:800;color:#0f172a;")
        self.lbl_profit_delta.setText(f"↗ {margin:.1f}% este mes" if profit >= 0 else f"↘ {abs(margin):.1f}% este mes")
        self.lbl_profit_delta.setStyleSheet("color:#10b981;font-weight:700;" if profit >= 0 else "color:#ef4444;font-weight:700;")

        self.lbl_fees.setStyleSheet("font-size:31px;font-weight:800;color:#0f172a;")
        self.lbl_fees_delta.setText(f"↘ {fee_ratio:.1f}% este mes")
        self.lbl_fees_delta.setStyleSheet("color:#ef4444;font-weight:700;")

        self.lbl_count.setStyleSheet("font-size:31px;font-weight:800;color:#0f172a;")
        self.lbl_count_delta.setText(f"↗ {qtd} vendas no periodo")
        self.lbl_count_delta.setStyleSheet("color:#10b981;font-weight:700;")

    def _update_charts(self, rows: list, start: str, end: str) -> None:
        # Grafico de tendencia diaria: faturamento, lucro e taxas.
        ordered = rows[::-1]
        if len(ordered) == 1:
            base_dt = datetime.strptime(ordered[0]["dt"], "%Y-%m-%d")
            prev_dt = (base_dt - timedelta(days=1)).strftime("%Y-%m-%d")
            ordered = [
                {"dt": prev_dt, "net": 0.0, "profit": 0.0, "fees": 0.0},
                ordered[0],
            ]
        categories = [fmt_date_br(r["dt"])[:5] for r in ordered]

        if len(ordered) <= 7:
            net_set = QBarSet("Faturamento")
            profit_set = QBarSet("Lucro")
            fees_set = QBarSet("Taxas")
            net_set.setColor(QColor("#0891b2"))
            profit_set.setColor(QColor("#16a34a"))
            fees_set.setColor(QColor("#dc2626"))
            for r in ordered:
                net_set.append(float(r["net"] or 0.0))
                profit_set.append(float(r["profit"] or 0.0))
                fees_set.append(float(r["fees"] or 0.0))

            bar_series = QBarSeries()
            bar_series.append(net_set)
            bar_series.append(profit_set)
            bar_series.append(fees_set)

            trend_chart = QChart()
            trend_chart.setTitle("")
            trend_chart.setAnimationOptions(QChart.AnimationOption.SeriesAnimations)
            trend_chart.setBackgroundVisible(False)
            trend_chart.setBackgroundRoundness(0)
            trend_chart.setBackgroundBrush(Qt.BrushStyle.NoBrush)
            trend_chart.setBackgroundPen(QPen(Qt.PenStyle.NoPen))
            trend_chart.setMargins(QMargins(2, 2, 2, 2))
            trend_chart.addSeries(bar_series)

            axis_x = QBarCategoryAxis()
            axis_x.append(categories if categories else ["Sem dados"])
            axis_y = QValueAxis()
            axis_y.setLabelFormat("%.0f")
            axis_y.setTitleText("")
            axis_y.setGridLineColor(QColor("#e2e8f0"))
            values = [float(r["net"] or 0.0) for r in ordered] + [float(r["profit"] or 0.0) for r in ordered] + [float(r["fees"] or 0.0) for r in ordered]
            max_val = max(values) if values else 0.0
            axis_y.setRange(0.0, max(10.0, max_val * 1.25))

            trend_chart.addAxis(axis_x, Qt.AlignmentFlag.AlignBottom)
            trend_chart.addAxis(axis_y, Qt.AlignmentFlag.AlignLeft)
            bar_series.attachAxis(axis_x)
            bar_series.attachAxis(axis_y)
            trend_chart.legend().setVisible(True)
            trend_chart.legend().setAlignment(Qt.AlignmentFlag.AlignTop)
            self.sales_chart_view.setChart(trend_chart)
        else:
            net_series = QSplineSeries()
            net_series.setName("Faturamento")
            profit_series = QSplineSeries()
            profit_series.setName("Lucro")
            fees_series = QSplineSeries()
            fees_series.setName("Taxas")

            net_series.setPen(QPen(QColor("#0891b2"), 3))
            profit_series.setPen(QPen(QColor("#16a34a"), 3))
            fees_series.setPen(QPen(QColor("#dc2626"), 3))
            net_series.setPointsVisible(True)
            profit_series.setPointsVisible(True)
            fees_series.setPointsVisible(True)

            for i, r in enumerate(ordered):
                net_series.append(i, float(r["net"] or 0.0))
                profit_series.append(i, float(r["profit"] or 0.0))
                fees_series.append(i, float(r["fees"] or 0.0))

            trend_chart = QChart()
            trend_chart.setTitle("")
            trend_chart.setAnimationOptions(QChart.AnimationOption.SeriesAnimations)
            trend_chart.setBackgroundVisible(False)
            trend_chart.setBackgroundRoundness(0)
            trend_chart.setBackgroundBrush(Qt.BrushStyle.NoBrush)
            trend_chart.setBackgroundPen(QPen(Qt.PenStyle.NoPen))
            trend_chart.setMargins(QMargins(2, 2, 2, 2))
            trend_chart.setPlotAreaBackgroundVisible(False)
            trend_chart.addSeries(net_series)
            trend_chart.addSeries(profit_series)
            trend_chart.addSeries(fees_series)

            axis_x = QBarCategoryAxis()
            axis_x.append(categories if categories else ["Sem dados"])
            axis_y = QValueAxis()
            axis_y.setLabelFormat("%.0f")
            axis_y.setTitleText("")
            axis_y.setGridLineColor(QColor("#e2e8f0"))
            values = [float(r["net"] or 0.0) for r in ordered] + [float(r["profit"] or 0.0) for r in ordered] + [float(r["fees"] or 0.0) for r in ordered]
            max_val = max(values) if values else 0.0
            axis_y.setRange(0.0, max(10.0, max_val * 1.25))

            trend_chart.addAxis(axis_x, Qt.AlignmentFlag.AlignBottom)
            trend_chart.addAxis(axis_y, Qt.AlignmentFlag.AlignLeft)

            for series in (net_series, profit_series, fees_series):
                series.attachAxis(axis_x)
                series.attachAxis(axis_y)

            trend_chart.legend().setVisible(True)
            trend_chart.legend().setAlignment(Qt.AlignmentFlag.AlignTop)
            self.sales_chart_view.setChart(trend_chart)

        payment_rows = self.db.fetch_all(
            """
            SELECT p.method, ROUND(SUM(p.amount),2) total
            FROM sale_payments p
            JOIN sales s ON s.id = p.sale_id
            WHERE DATE(s.created_at) BETWEEN ? AND ? AND s.status <> 'CANCELADA'
            GROUP BY p.method
            ORDER BY total DESC
            """,
            (start, end),
        )
        pie = QPieSeries()
        pie.setHoleSize(0.48)
        pie_colors = ["#635bff", "#11b69b", "#f3c25f", "#a9b6c6"]
        for idx, pr in enumerate(payment_rows):
            slice_item = pie.append(pr["method"], float(pr["total"] or 0.0))
            slice_item.setLabelVisible(True)
            slice_item.setLabel(f"{pr['method']}\n{fmt_money(pr['total'])}")
            slice_item.setLabelArmLengthFactor(0.2)
            slice_item.setLabelColor(QColor("#64748b"))
            if idx < len(pie_colors):
                slice_item.setColor(QColor(pie_colors[idx]))

        pie_chart = QChart()
        pie_chart.setTitle("")
        pie_chart.setAnimationOptions(QChart.AnimationOption.SeriesAnimations)
        pie_chart.setBackgroundVisible(False)
        pie_chart.setBackgroundRoundness(0)
        pie_chart.setBackgroundBrush(Qt.BrushStyle.NoBrush)
        pie_chart.setBackgroundPen(QPen(Qt.PenStyle.NoPen))
        pie_chart.setMargins(QMargins(2, 2, 2, 2))
        pie_chart.addSeries(pie)
        pie_chart.legend().setVisible(False)
        self.payment_chart_view.setChart(pie_chart)

    def _style_sales_table(self) -> None:
        self._style_sales_rows(self.table)

    def _style_sales_rows(self, table: QTableWidget) -> None:
        for row in range(table.rowCount()):
            pedido_item = table.item(row, 0)
            valor_item = table.item(row, 3)
            status_item = table.item(row, 4)
            data_item = table.item(row, 5)
            if pedido_item:
                pedido_item.setForeground(QColor("#635bff"))
                pedido_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            if valor_item:
                valor_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            if data_item:
                data_item.setForeground(QColor("#64748b"))
                data_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            if status_item:
                text = status_item.text().strip().lower()
                status_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                if text == "pago":
                    status_item.setForeground(QColor("#10b981"))
                    status_item.setBackground(QColor("#e9fbf5"))
                elif text == "cancelada":
                    status_item.setForeground(QColor("#dc2626"))
                    status_item.setBackground(QColor("#fef2f2"))
                    for col in range(table.columnCount()):
                        cell = table.item(row, col)
                        if cell:
                            font = cell.font()
                            font.setStrikeOut(True)
                            cell.setFont(font)
                            if col != 4:
                                cell.setForeground(QColor("#94a3b8"))
                else:
                    status_item.setForeground(QColor("#d97706"))
                    status_item.setBackground(QColor("#fff7e6"))

    def _show_full_sales_history(self) -> None:
        dlg = QDialog(self)
        dlg.setWindowTitle("Historico Completo de Vendas")
        dlg.resize(1100, 680)
        layout = QVBoxLayout(dlg)

        filters = QFrame()
        filters.setObjectName("Card")
        filters.setProperty("class", "FilterBar")
        fl = QHBoxLayout(filters)
        fl.setContentsMargins(12, 10, 12, 10)
        fl.setSpacing(8)

        date_start = QDateEdit()
        date_start.setObjectName("ModernDateEdit")
        date_start.setCalendarPopup(False)
        date_start.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)

        date_end = QDateEdit()
        date_end.setObjectName("ModernDateEdit")
        date_end.setCalendarPopup(False)
        date_end.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)

        today = QDate.currentDate()
        date_start.setDate(today.addDays(-(today.day() - 1)))
        date_end.setDate(today)

        btn_start_cal = QToolButton()
        btn_start_cal.setObjectName("CalendarHintButton")
        btn_start_cal.setIcon(make_calendar_icon())
        btn_start_cal.setIconSize(QSize(14, 14))
        btn_start_cal.setAutoRaise(False)
        btn_start_cal.setToolTip("Abrir calendario da data inicial")

        btn_end_cal = QToolButton()
        btn_end_cal.setObjectName("CalendarHintButton")
        btn_end_cal.setIcon(make_calendar_icon())
        btn_end_cal.setIconSize(QSize(14, 14))
        btn_end_cal.setAutoRaise(False)
        btn_end_cal.setToolTip("Abrir calendario da data final")

        start_field = QFrame()
        start_field.setObjectName("DateFieldWrap")
        start_layout = QHBoxLayout(start_field)
        start_layout.setContentsMargins(0, 0, 0, 0)
        start_layout.setSpacing(0)
        start_layout.addWidget(date_start)
        start_layout.addWidget(btn_start_cal)

        end_field = QFrame()
        end_field.setObjectName("DateFieldWrap")
        end_layout = QHBoxLayout(end_field)
        end_layout.setContentsMargins(0, 0, 0, 0)
        end_layout.setSpacing(0)
        end_layout.addWidget(date_end)
        end_layout.addWidget(btn_end_cal)

        btn_today = QPushButton("Hoje")
        btn_today.setObjectName("GhostButton")
        btn_week = QPushButton("7 dias")
        btn_week.setObjectName("GhostButton")
        btn_month = QPushButton("Este mes")
        btn_month.setObjectName("GhostButton")

        btn_filter = QPushButton("Filtrar")

        fl.addWidget(QLabel("Inicio"))
        fl.addWidget(start_field)
        fl.addWidget(QLabel("Fim"))
        fl.addWidget(end_field)
        fl.addSpacing(8)
        fl.addWidget(btn_today)
        fl.addWidget(btn_week)
        fl.addWidget(btn_month)
        fl.addStretch()
        fl.addWidget(btn_filter)

        layout.addWidget(filters)

        table = QTableWidget(0, 7)
        table.setObjectName("RecentSalesTable")
        table.setHorizontalHeaderLabels(["Pedido", "Cliente", "Produto", "Valor", "Status", "Data", "Acoes"])
        apply_table_preset(table)
        table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        table.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        table.setWordWrap(False)
        table.setTextElideMode(Qt.TextElideMode.ElideRight)
        table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        # O padding vertical do tema encolhe a area dos botoes da coluna Acoes e corta os icones.
        table.setStyleSheet("QTableWidget::item { padding: 0px 10px; }")

        def reprint_sale(sale_id: int) -> None:
            text = self._receipt_text_from_sale(sale_id)
            logo_path, paper_type = _receipt_print_options(self.db)
            result = self.printer_service.print_receipt_text(text, logo_path=logo_path, paper_type=paper_type)
            if result.ok:
                QMessageBox.information(dlg, "Impressao", result.message)
            else:
                QMessageBox.warning(dlg, "Impressao", result.message)

        def cancel_sale(sale_id: int) -> None:
            if self.user is None:
                return
            answer = QMessageBox.question(
                dlg,
                "Cancelar venda",
                f"Cancelar a venda #{sale_id}?\n\n"
                "Os produtos voltam para o estoque e a venda sai do faturamento, lucro e fluxo de caixa.\n"
                "Esta acao nao pode ser desfeita.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if answer != QMessageBox.StandardButton.Yes:
                return
            reason, _ok = QInputDialog.getText(
                dlg,
                "Cancelar venda",
                "Motivo do cancelamento (opcional):\n\n"
                "Dica: escreva \"pedido teste\" no motivo para que este cancelamento\n"
                "NAO seja contabilizado no Dashboard (testes ou vendas por engano).",
            )
            try:
                self.sales_service.cancel_sale(sale_id, self.user.id, reason)
            except ValueError as exc:
                QMessageBox.warning(dlg, "Cancelar venda", str(exc))
                return
            refresh_history()
            self.refresh()
            QMessageBox.information(dlg, "Cancelar venda", f"Venda #{sale_id} cancelada. Estoque atualizado.")

        def exchange_sale(sale_id: int) -> None:
            if self.user is None or self.on_exchange is None:
                return
            answer = QMessageBox.question(
                dlg,
                "Trocar produto",
                f"Trocar produtos da venda #{sale_id}?\n\n"
                "A venda original sera cancelada (motivo: Troca) e os produtos voltam ao estoque.\n"
                "Os itens e o cliente serao carregados no PDV para voce ajustar e finalizar a nova venda.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if answer != QMessageBox.StandardButton.Yes:
                return
            sale = self.db.fetch_one("SELECT client_id, net_total FROM sales WHERE id = ?", (sale_id,))
            items = self.db.fetch_all(
                """
                SELECT si.product_id, p.name, si.qty, si.unit_price, si.unit_cost
                FROM sale_items si JOIN products p ON p.id = si.product_id
                WHERE si.sale_id = ?
                """,
                (sale_id,),
            )
            try:
                self.sales_service.cancel_sale(sale_id, self.user.id, f"Troca (venda #{sale_id})")
            except ValueError as exc:
                QMessageBox.warning(dlg, "Trocar produto", str(exc))
                return
            cart = [
                {
                    "product_id": int(i["product_id"]),
                    "name": i["name"],
                    "qty": float(i["qty"]),
                    "unit_price": float(i["unit_price"]),
                    "unit_cost": float(i["unit_cost"]),
                }
                for i in items
            ]
            client_id = int(sale["client_id"]) if sale and sale["client_id"] is not None else None
            self.refresh()
            dlg.accept()
            self.on_exchange(sale_id, cart, client_id, float(sale["net_total"]) if sale else 0.0)

        def apply_columns_layout() -> None:
            table.horizontalHeader().setStretchLastSection(False)
            table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
            table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
            table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
            table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
            table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
            table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
            table.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeMode.Fixed)
            table.setColumnWidth(6, 136)
            cupom_header_item = table.horizontalHeaderItem(6)
            if cupom_header_item:
                cupom_header_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

        def refresh_history() -> None:
            start = date_start.date().toString("yyyy-MM-dd")
            end = date_end.date().toString("yyyy-MM-dd")
            rows = self.db.fetch_all(
                """
                SELECT s.id, s.created_at, s.status, COALESCE(c.name,'Consumidor Final') AS client,
                       COALESCE(MAX(p.name),'Venda PDV') AS product,
                       s.net_total, s.profit_total
                FROM sales s
                LEFT JOIN clients c ON c.id = s.client_id
                LEFT JOIN sale_items si ON si.sale_id = s.id
                LEFT JOIN products p ON p.id = si.product_id
                WHERE DATE(s.created_at) BETWEEN ? AND ?
                GROUP BY s.id, s.created_at, s.status, c.name, s.net_total, s.profit_total
                ORDER BY s.created_at DESC
                """,
                (start, end),
            )

            data = []
            for sale in rows:
                if sale["status"] == "CANCELADA":
                    status = "Cancelada"
                else:
                    status = "Pago" if float(sale["profit_total"] or 0.0) >= 0 else "Pendente"
                data.append(
                    [
                        f"#{sale['id']}",
                        sale["client"],
                        sale["product"],
                        fmt_money(sale["net_total"]),
                        status,
                        fmt_date_br(str(sale["created_at"])),
                    ]
                )

            fill_table(table, data)
            apply_columns_layout()
            self._style_sales_rows(table)

            for row_idx, sale in enumerate(rows):
                table.setRowHeight(row_idx, 42)
                sale_id = int(sale["id"])
                cancelled = sale["status"] == "CANCELADA"

                btn_print_icon = QToolButton()
                btn_print_icon.setToolTip("Reimprimir cupom nao fiscal")
                btn_print_icon.setIcon(make_printer_icon())
                btn_print_icon.setIconSize(QSize(16, 16))
                btn_print_icon.setFixedSize(34, 30)
                btn_print_icon.setCursor(Qt.CursorShape.PointingHandCursor)
                btn_print_icon.setStyleSheet(
                    "QToolButton { background:#eef2ff; border:1px solid #c7d2fe; border-radius:8px; }"
                    "QToolButton:hover { background:#e0e7ff; border-color:#a5b4fc; }"
                    "QToolButton:disabled { background:#f1f5f9; border-color:#e2e8f0; }"
                )
                btn_print_icon.setEnabled(not cancelled)
                btn_print_icon.clicked.connect(lambda _=False, sid=sale_id: reprint_sale(sid))

                btn_cancel = QToolButton()
                btn_cancel.setToolTip("Venda ja cancelada" if cancelled else "Cancelar venda (devolve ao estoque)")
                btn_cancel.setIcon(_vector_icon("trash", "#cbd5e1" if cancelled else "#dc2626"))
                btn_cancel.setIconSize(QSize(16, 16))
                btn_cancel.setFixedSize(34, 30)
                btn_cancel.setCursor(Qt.CursorShape.PointingHandCursor)
                btn_cancel.setStyleSheet(
                    "QToolButton { background:#fef2f2; border:1px solid #fecaca; border-radius:8px; }"
                    "QToolButton:hover { background:#fee2e2; border-color:#fca5a5; }"
                    "QToolButton:disabled { background:#f1f5f9; border-color:#e2e8f0; }"
                )
                btn_cancel.setEnabled(not cancelled and self.user is not None)
                btn_cancel.clicked.connect(lambda _=False, sid=sale_id: cancel_sale(sid))

                btn_exchange = QToolButton()
                btn_exchange.setToolTip("Venda ja cancelada" if cancelled else "Trocar produto (cancela e abre nova venda no PDV)")
                btn_exchange.setIcon(_vector_icon("exchange", "#cbd5e1" if cancelled else "#d97706"))
                btn_exchange.setIconSize(QSize(16, 16))
                btn_exchange.setFixedSize(34, 30)
                btn_exchange.setCursor(Qt.CursorShape.PointingHandCursor)
                btn_exchange.setStyleSheet(
                    "QToolButton { background:#fffbeb; border:1px solid #fde68a; border-radius:8px; }"
                    "QToolButton:hover { background:#fef3c7; border-color:#fcd34d; }"
                    "QToolButton:disabled { background:#f1f5f9; border-color:#e2e8f0; }"
                )
                btn_exchange.setEnabled(not cancelled and self.user is not None and self.on_exchange is not None)
                btn_exchange.clicked.connect(lambda _=False, sid=sale_id: exchange_sale(sid))

                cell_wrap = QWidget()
                cell_wrap.setStyleSheet("background: transparent;")
                cell_layout = QHBoxLayout(cell_wrap)
                cell_layout.setContentsMargins(4, 0, 4, 0)
                cell_layout.setSpacing(6)
                cell_layout.addWidget(btn_print_icon, 0, Qt.AlignmentFlag.AlignCenter)
                cell_layout.addWidget(btn_exchange, 0, Qt.AlignmentFlag.AlignCenter)
                cell_layout.addWidget(btn_cancel, 0, Qt.AlignmentFlag.AlignCenter)
                table.setCellWidget(row_idx, 6, cell_wrap)

        def set_today() -> None:
            t = QDate.currentDate()
            date_start.setDate(t)
            date_end.setDate(t)
            refresh_history()

        def set_week() -> None:
            t = QDate.currentDate()
            date_start.setDate(t.addDays(-6))
            date_end.setDate(t)
            refresh_history()

        def set_month() -> None:
            t = QDate.currentDate()
            date_start.setDate(t.addDays(-(t.day() - 1)))
            date_end.setDate(t)
            refresh_history()

        def pick_start() -> None:
            selected = self._pick_date(date_start.date(), "Selecionar Data Inicial")
            if selected is not None:
                date_start.setDate(selected)
                refresh_history()

        def pick_end() -> None:
            selected = self._pick_date(date_end.date(), "Selecionar Data Final")
            if selected is not None:
                date_end.setDate(selected)
                refresh_history()

        btn_today.clicked.connect(set_today)
        btn_week.clicked.connect(set_week)
        btn_month.clicked.connect(set_month)
        btn_filter.clicked.connect(refresh_history)
        btn_start_cal.clicked.connect(pick_start)
        btn_end_cal.clicked.connect(pick_end)

        layout.addWidget(table, 1)
        refresh_history()
        dlg.exec()

    def _make_receipt_text(self, sale_id: int, preview: dict) -> str:
        return _build_receipt_text(self.db, sale_id, preview)

    def _receipt_text_from_sale(self, sale_id: int) -> str:
        sale = self.db.fetch_one("SELECT * FROM sales WHERE id = ?", (sale_id,))
        if not sale:
            return "Venda nao encontrada."

        items = self.db.fetch_all(
            """
            SELECT i.product_id, i.qty, i.unit_price, p.name AS product_name
            FROM sale_items i
            LEFT JOIN products p ON p.id = i.product_id
            WHERE i.sale_id = ?
            """,
            (sale_id,),
        )
        payments = self.db.fetch_all("SELECT * FROM sale_payments WHERE sale_id = ?", (sale_id,))

        preview = {
            "gross_total": sale["gross_total"],
            "discount_total": sale["discount_total"],
            "net_total": sale["net_total"],
            "items": [{"product_id": i["product_id"], "name": i["product_name"] or f"Produto #{i['product_id']}", "qty": i["qty"], "unit_price": i["unit_price"]} for i in items],
            "payments": [{"method": p["method"], "amount": p["amount"]} for p in payments],
        }
        return self._make_receipt_text(sale_id, preview)


class PdvPage(BasePage):
    METHODS = ["DEBITO", "CREDITO_AVISTA", "CREDITO_PARCELADO", "PIX_MAQUININHA", "PIX", "DINHEIRO"]
    PRODUCT_CARD_LIMIT = 15

    def __init__(self, db: Database, user: AuthUser, sales_service: SalesService) -> None:
        super().__init__()
        self.db = db
        self.user = user
        self.sales_service = sales_service
        self.printer_service = PrinterService()
        self.cart: list[dict] = []
        self.last_sale_id: int | None = None
        self.selected_product_id: int | None = None
        self.selected_cart_index: int | None = None
        self.selected_payment_method = "DINHEIRO"
        self.payment_shortcut_buttons: dict[str, QPushButton] = {}
        self._syncing_discount = False
        self._build()
        self.load_products()
        self.load_clients()

    def _set_selected_cart_index(self, index: int) -> None:
        if index < 0 or index >= len(self.cart):
            self.selected_cart_index = None
        else:
            self.selected_cart_index = index
        self.refresh_cart_table()

    def _clear_layout(self, layout: QVBoxLayout) -> None:
        while layout.count():
            child = layout.takeAt(0)
            widget = child.widget()
            if widget is not None:
                widget.deleteLater()

    def _gross_total(self) -> float:
        return round(sum(i["qty"] * i["unit_price"] for i in self.cart), 2)

    def _configure_discount_input(self) -> None:
        mode = self.discount_mode_combo.currentData()
        if mode == "PERCENT":
            self.discount_input_spin.setPrefix("")
            self.discount_input_spin.setSuffix(" %")
            self.discount_input_spin.setRange(0, 100)
            self.discount_input_spin.setSingleStep(1)
            gross = self._gross_total()
            percent = 0.0 if gross <= 0 else (self.discount_spin.value() / gross) * 100.0
            self.discount_input_spin.setValue(max(0.0, min(100.0, round(percent, 2))))
        else:
            self.discount_input_spin.setPrefix("R$ ")
            self.discount_input_spin.setSuffix("")
            self.discount_input_spin.setRange(0, 999999)
            self.discount_input_spin.setSingleStep(1)
            self.discount_input_spin.setValue(round(self.discount_spin.value(), 2))

    def _sync_discount_from_input(self) -> None:
        if self._syncing_discount:
            return
        gross = self._gross_total()
        mode = self.discount_mode_combo.currentData()
        typed_value = self.discount_input_spin.value()
        discount_amount = round(gross * typed_value / 100.0, 2) if mode == "PERCENT" else round(typed_value, 2)
        clamped_discount = max(0.0, min(gross, discount_amount))

        self._syncing_discount = True
        self.discount_spin.setValue(clamped_discount)
        if mode == "AMOUNT" and typed_value != clamped_discount:
            self.discount_input_spin.setValue(clamped_discount)
        self._syncing_discount = False

    def _on_discount_mode_changed(self) -> None:
        self._syncing_discount = True
        self._configure_discount_input()
        self._syncing_discount = False
        self._sync_discount_from_input()
        self.update_totals()

    def _add_quick_payment(self, method: str) -> None:
        self._set_primary_payment(method)

    def _method_display_name(self, method: str) -> str:
        names = {
            "DINHEIRO": "Dinheiro",
            "DEBITO": "Cartão Débito",
            "CREDITO_AVISTA": "Cartão Crédito",
            "PIX": "PIX",
            "CREDITO_PARCELADO": "Cartão Parcelado",
            "PIX_MAQUININHA": "PIX Maquininha",
        }
        return names.get(method, method)

    def _set_primary_payment(self, method: str) -> None:
        self.selected_payment_method = method
        for m, button in self.payment_shortcut_buttons.items():
            button.setProperty("active", "true" if m == method else "false")
            button.style().unpolish(button)
            button.style().polish(button)
        self.update_totals()

    def _on_density_changed(self) -> None:
        density = self.density_combo.currentData() or "compact"
        self._apply_density(str(density))

    def _apply_density(self, density: str) -> None:
        self.setProperty("pdvDensity", density)
        for widget in (
            self,
            self.cart_items_scroll,
            self.secondary_payment_wrap,
            self.btn_finish,
            self.pix_qr_btn,
            self.secondary_payment_btn,
        ):
            widget.style().unpolish(widget)
            widget.style().polish(widget)

    def _build_payment_parts(self, net: float) -> list[PaymentPart]:
        if net <= 0:
            return []

        payments: list[PaymentPart] = []
        if self.secondary_payment_btn.isChecked():
            secondary_method = self.secondary_method_combo.currentData() or self.secondary_method_combo.currentText()
            secondary_amount = round(min(max(self.secondary_amount_spin.value(), 0.0), net), 2)
            if str(secondary_method) == self.selected_payment_method:
                secondary_amount = 0.0
            primary_amount = round(max(0.0, net - secondary_amount), 2)
            if primary_amount > 0:
                payments.append(PaymentPart(method=self.selected_payment_method, amount=primary_amount))
            if secondary_amount > 0:
                payments.append(PaymentPart(method=str(secondary_method), amount=secondary_amount))
            return self._merge_payment_parts(payments)

        payments.append(PaymentPart(method=self.selected_payment_method, amount=net))
        return self._merge_payment_parts(payments)

    def _merge_payment_parts(self, parts: list[PaymentPart]) -> list[PaymentPart]:
        merged: dict[str, float] = {}
        for p in parts:
            merged[p.method] = round(merged.get(p.method, 0.0) + float(p.amount), 2)
        return [PaymentPart(method=method, amount=value) for method, value in merged.items() if value > 0]

    def _sale_totals(self) -> tuple[float, float, float, float, float, float]:
        gross = round(sum(i["qty"] * i["unit_price"] for i in self.cart), 2)
        net = round(max(0.0, gross - self.discount_spin.value()), 2)

        payments = self._build_payment_parts(net)
        cash_expected = round(sum(p.amount for p in payments if p.method == "DINHEIRO"), 2)

        if cash_expected > 0:
            self.cash_received_spin.setEnabled(True)
            if self.cash_received_spin.value() <= 0:
                self.cash_received_spin.setValue(cash_expected)
            received = round(self.cash_received_spin.value(), 2)
        else:
            self.cash_received_spin.setEnabled(False)
            if self.cash_received_spin.value() != 0:
                self.cash_received_spin.setValue(0)
            received = 0.0

        change = round(max(0.0, received - cash_expected), 2)
        pending = round(max(0.0, cash_expected - received), 2)
        return gross, net, cash_expected, received, change, pending

    def _build(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(12)
        root.addWidget(self._title("Frente de Caixa (PDV)", "Registre vendas rapidamente com busca de produtos e múltiplas formas de pagamento."))

        split = QHBoxLayout()
        split.setSpacing(12)
        root.addLayout(split, 1)

        left = QFrame()
        left.setObjectName("Card")
        left.setProperty("pdvPane", "catalog")
        ll = QVBoxLayout(left)
        ll.setContentsMargins(12, 12, 12, 12)
        ll.setSpacing(10)
        
        products_title = QLabel("Catálogo de Produtos")
        products_title.setObjectName("SectionTitle")
        products_sub = QLabel("Busque, confira estoque e adicione ao carrinho")
        products_sub.setObjectName("PageSubtitle")
        ll.addWidget(products_title)
        ll.addWidget(products_sub)
        self.search_edit = QLineEdit()
        self.search_edit.setObjectName("PdvSearchInput")
        self.search_edit.setPlaceholderText("Buscar produto por nome ou código de barras (Enter adiciona ao carrinho)")
        self.search_edit.textChanged.connect(self.load_products)
        self.search_edit.returnPressed.connect(self._on_search_return)
        ll.addWidget(self.search_edit)

        self.products_count = QLabel("0 produtos encontrados")
        self.products_count.setObjectName("PdvCounter")
        ll.addWidget(self.products_count)

        self.stock_hint = QLabel("Sem alerta de estoque no filtro atual.")
        self.stock_hint.setObjectName("PdvHintBadge")
        ll.addWidget(self.stock_hint)

        self.products_scroll = QScrollArea()
        self.products_scroll.setObjectName("PdvProductScroll")
        self.products_scroll.setWidgetResizable(True)
        self.products_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.products_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        products_wrap = QWidget()
        self.products_grid = QGridLayout(products_wrap)
        self.products_grid.setContentsMargins(0, 0, 0, 0)
        self.products_grid.setHorizontalSpacing(10)
        self.products_grid.setVerticalSpacing(10)
        self.products_grid.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        self.products_scroll.setWidget(products_wrap)
        ll.addWidget(self.products_scroll, 1)

        split.addWidget(left, 3)

        right = QFrame()
        right.setObjectName("Card")
        right.setProperty("pdvPane", "checkout")
        right.setMinimumWidth(420)
        right.setMaximumWidth(500)
        rl = QVBoxLayout(right)
        rl.setContentsMargins(12, 12, 12, 12)
        rl.setSpacing(10)

        header_row = QHBoxLayout()
        header_row.setSpacing(8)
        self.cart_title = QLabel("Carrinho (0)")
        self.cart_title.setObjectName("SectionTitle")
        header_row.addWidget(self.cart_title)
        header_row.addStretch()
        self.density_combo = QComboBox()
        self.density_combo.setObjectName("PdvDensityCombo")
        self.density_combo.addItem("Normal", "normal")
        self.density_combo.addItem("Compacto", "compact")
        self.density_combo.addItem("Ultra", "ultra")
        self.density_combo.currentIndexChanged.connect(self._on_density_changed)
        self.density_combo.setVisible(False)
        self.density_combo.setEnabled(False)
        rl.addLayout(header_row)

        # O combo guarda o cliente selecionado (currentData); a interface visível é o seletor abaixo.
        self.client_combo = QComboBox()
        self.client_combo.setVisible(False)
        rl.addWidget(self.client_combo)

        client_row = QHBoxLayout()
        client_row.setSpacing(6)
        self.client_pick_btn = QPushButton()
        self.client_pick_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.client_pick_btn.setMinimumHeight(38)
        self.client_pick_btn.setToolTip("Clique para escolher um cliente cadastrado")
        self.client_pick_btn.clicked.connect(self.open_client_picker)
        client_row.addWidget(self.client_pick_btn, 1)
        self.client_search_btn = QPushButton()
        self.client_search_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.client_search_btn.setFixedSize(38, 38)
        self.client_search_btn.setIcon(_vector_icon("search", "#ffffff"))
        self.client_search_btn.setIconSize(QSize(20, 20))
        self.client_search_btn.setToolTip("Pesquisar cliente")
        self.client_search_btn.setStyleSheet(
            "QPushButton { background:#2563eb; border:none; border-radius:10px; }"
            "QPushButton:hover { background:#1d4ed8; }"
            "QPushButton:pressed { background:#1e40af; }"
        )
        self.client_search_btn.clicked.connect(self.open_client_picker)
        client_row.addWidget(self.client_search_btn)
        self.client_clear_btn = QPushButton()
        self.client_clear_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.client_clear_btn.setFixedSize(38, 38)
        self.client_clear_btn.setIcon(_vector_icon("close", "#b91c1c"))
        self.client_clear_btn.setIconSize(QSize(16, 16))
        self.client_clear_btn.setToolTip("Remover cliente (voltar para Consumidor Final)")
        self.client_clear_btn.setStyleSheet(
            "QPushButton { background:#fef2f2; border:1px solid #fecaca; border-radius:10px; }"
            "QPushButton:hover { background:#fee2e2; }"
        )
        self.client_clear_btn.clicked.connect(lambda: self._set_pdv_client(None))
        client_row.addWidget(self.client_clear_btn)
        rl.addLayout(client_row)

        self.cart_items_scroll = QScrollArea()
        self.cart_items_scroll.setObjectName("PdvCartItemsScroll")
        self.cart_items_scroll.setWidgetResizable(True)
        self.cart_items_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.cart_items_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.cart_items_wrap = QWidget()
        self.cart_items_layout = QVBoxLayout(self.cart_items_wrap)
        self.cart_items_layout.setContentsMargins(0, 0, 0, 0)
        self.cart_items_layout.setSpacing(6)
        self.cart_items_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.cart_items_scroll.setWidget(self.cart_items_wrap)
        self.cart_items_scroll.setMinimumHeight(295)
        rl.addWidget(self.cart_items_scroll, 1)

        payment_section = QFrame()
        payment_section.setObjectName("PdvPaymentSection")
        payment_layout = QVBoxLayout(payment_section)
        payment_layout.setContentsMargins(10, 8, 10, 8)
        payment_layout.setSpacing(8)
        pay_title = QLabel("PAGAMENTO")
        pay_title.setObjectName("PdvSmallSectionTitle")
        payment_layout.addWidget(pay_title)

        pay_shortcuts = QGridLayout()
        pay_shortcuts.setHorizontalSpacing(8)
        pay_shortcuts.setVerticalSpacing(8)
        for idx, (label, method) in enumerate(
            (
                ("Dinheiro", "DINHEIRO"),
                ("Cartão Débito", "DEBITO"),
                ("Cartão Crédito", "CREDITO_AVISTA"),
                ("PIX", "PIX"),
            )
        ):
            b = QPushButton(label)
            b.setObjectName("PayMethodButton")
            b.setMinimumHeight(34)
            b.setCursor(Qt.CursorShape.PointingHandCursor)
            b.setStyleSheet("""
                QPushButton#PayMethodButton {
                    background-color: #F8FAFC;
                    border: 1px solid #E2E8F0;
                    border-radius: 6px;
                    color: #475569;
                    font-weight: 600;
                }
                QPushButton#PayMethodButton:hover {
                    background-color: #F1F5F9;
                    color: #0F172A;
                }
                QPushButton#PayMethodButton[active="true"] {
                    background-color: #6366F1;
                    color: #FFFFFF;
                    border-color: #4F46E5;
                }
            """)
            b.clicked.connect(lambda _=False, m=method: self._set_primary_payment(m))
            pay_shortcuts.addWidget(b, idx // 2, idx % 2)
            self.payment_shortcut_buttons[method] = b
        payment_layout.addLayout(pay_shortcuts)

        extras_row = QHBoxLayout()
        extras_row.setSpacing(6)
        self.secondary_payment_btn = QPushButton("Dividir pagamento")
        self.secondary_payment_btn.setObjectName("PdvSecondaryToggle")
        self.secondary_payment_btn.setCheckable(True)
        self.secondary_payment_btn.toggled.connect(self._toggle_secondary_payment)
        self.pix_qr_btn = QToolButton()
        self.pix_qr_btn.setObjectName("PdvPixQrButton")
        self.pix_qr_btn.setIcon(make_qr_icon())
        self.pix_qr_btn.setIconSize(QSize(14, 14))
        self.pix_qr_btn.setToolTip("Gerar QR Code PIX")
        self.pix_qr_btn.clicked.connect(lambda _=False: self._show_pix_qr_dialog())
        extras_row.addWidget(self.secondary_payment_btn)
        extras_row.addStretch()
        extras_row.addWidget(self.pix_qr_btn)
        payment_layout.addLayout(extras_row)

        self.secondary_payment_wrap = QFrame()
        self.secondary_payment_wrap.setObjectName("PdvSecondaryWrap")
        secondary_layout = QVBoxLayout(self.secondary_payment_wrap)
        secondary_layout.setContentsMargins(8, 6, 8, 6)
        secondary_layout.setSpacing(6)

        method_row = QHBoxLayout()
        method_row.setSpacing(8)
        method_row.addWidget(QLabel("2a forma"))
        self.secondary_method_combo = QComboBox()
        self.secondary_method_combo.setObjectName("PdvSecondaryMethod")
        for label, method in (
            ("Dinheiro", "DINHEIRO"),
            ("Cartão Débito", "DEBITO"),
            ("Cartão Crédito", "CREDITO_AVISTA"),
            ("PIX", "PIX"),
        ):
            self.secondary_method_combo.addItem(label, method)
        self.secondary_method_combo.currentIndexChanged.connect(self.update_totals)
        method_row.addWidget(self.secondary_method_combo, 1)
        secondary_layout.addLayout(method_row)

        amount_row = QHBoxLayout()
        amount_row.setSpacing(8)
        amount_row.addWidget(QLabel("Valor 2a forma"))
        self.secondary_amount_spin = QDoubleSpinBox()
        self.secondary_amount_spin.setObjectName("PdvSecondaryAmount")
        self.secondary_amount_spin.setPrefix("R$ ")
        self.secondary_amount_spin.setDecimals(2)
        self.secondary_amount_spin.setMaximum(999999)
        self.secondary_amount_spin.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        self.secondary_amount_spin.valueChanged.connect(self.update_totals)
        self.secondary_amount_spin.setMinimumWidth(120)
        amount_row.addWidget(self.secondary_amount_spin, 1)
        self.secondary_fill_rest_btn = QPushButton("Restante")
        self.secondary_fill_rest_btn.setObjectName("PdvSecondaryFillRest")
        self.secondary_fill_rest_btn.setMinimumHeight(26)
        self.secondary_fill_rest_btn.clicked.connect(self._fill_secondary_with_remaining)
        amount_row.addWidget(self.secondary_fill_rest_btn)
        secondary_layout.addLayout(amount_row)

        self.primary_split_label = QLabel("1a forma calculada: R$ 0,00")
        self.primary_split_label.setObjectName("PdvPrimarySplitLabel")
        secondary_layout.addWidget(self.primary_split_label)

        self.secondary_payment_wrap.setVisible(False)
        payment_layout.addWidget(self.secondary_payment_wrap)

        self.payment_split_hint = QLabel("")
        self.payment_split_hint.setObjectName("PdvSplitHint")
        payment_layout.addWidget(self.payment_split_hint)

        discount_row = QHBoxLayout()
        discount_row.setSpacing(8)
        discount_row.addWidget(QLabel("Desconto"))
        self.discount_mode_combo = QComboBox()
        self.discount_mode_combo.setObjectName("DiscountModeCombo")
        self.discount_mode_combo.addItem("%", "PERCENT")
        self.discount_mode_combo.addItem("R$", "AMOUNT")
        self.discount_mode_combo.currentIndexChanged.connect(self._on_discount_mode_changed)
        discount_row.addWidget(self.discount_mode_combo)
        self.discount_input_spin = QDoubleSpinBox()
        self.discount_input_spin.setObjectName("DiscountInputSpin")
        self.discount_input_spin.setDecimals(2)
        self.discount_input_spin.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        self.discount_input_spin.valueChanged.connect(self._sync_discount_from_input)
        discount_row.addWidget(self.discount_input_spin, 1)
        payment_layout.addLayout(discount_row)

        self.discount_spin = QDoubleSpinBox()
        self.discount_spin.setObjectName("DiscountAmountSpin")
        self.discount_spin.setPrefix("R$ ")
        self.discount_spin.setDecimals(2)
        self.discount_spin.setMaximum(999999)
        self.discount_spin.valueChanged.connect(self.update_totals)
        self.discount_spin.hide()

        cash_row = QHBoxLayout()
        cash_row.setSpacing(8)
        cash_row.addWidget(QLabel("Recebido (R$)"))
        self.cash_received_spin = QDoubleSpinBox()
        self.cash_received_spin.setObjectName("CashReceivedSpin")
        self.cash_received_spin.setPrefix("R$ ")
        self.cash_received_spin.setDecimals(2)
        self.cash_received_spin.setMaximum(999999)
        self.cash_received_spin.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        self.cash_received_spin.valueChanged.connect(self.update_totals)
        
        # INTERFACE CRÍTICA: Estilo explícito para deixar o campo cinza escuro/opaco se estiver desativado
        self.cash_received_spin.setStyleSheet("""
            QDoubleSpinBox#CashReceivedSpin {
                background-color: #FFFFFF;
                border: 1px solid #E2E8F0;
                border-radius: 6px;
                padding: 4px;
                color: #1E293B;
            }
            QDoubleSpinBox#CashReceivedSpin:disabled {
                background-color: #F1F5F9;
                color: #94A3B8;
                border-color: #E2E8F0;
            }
        """)
        cash_row.addWidget(self.cash_received_spin, 1)
        payment_layout.addLayout(cash_row)

        summary = QFrame()
        summary.setObjectName("PdvSummaryCard")
        summary_layout = QVBoxLayout(summary)
        summary_layout.setContentsMargins(8, 8, 8, 8)
        summary_layout.setSpacing(5)
        subtotal_row = QHBoxLayout()
        subtotal_lbl = QLabel("Subtotal")
        subtotal_lbl.setObjectName("PdvSummaryLabel")
        self.lbl_subtotal_value = QLabel("R$ 0,00")
        self.lbl_subtotal_value.setObjectName("PdvSummaryValue")
        subtotal_row.addWidget(subtotal_lbl)
        subtotal_row.addStretch()
        subtotal_row.addWidget(self.lbl_subtotal_value)
        
        total_row = QHBoxLayout()
        total_lbl = QLabel("Total")
        total_lbl.setObjectName("PdvTotalLabel")
        self.lbl_total_value = QLabel("R$ 0,00")
        self.lbl_total_value.setObjectName("PdvTotalValue")
        self.lbl_total_value.setStyleSheet("QLabel { font-size: 20px; font-weight: 800; color: #1E293B; }")
        total_row.addWidget(total_lbl)
        total_row.addStretch()
        total_row.addWidget(self.lbl_total_value)
        
        change_row = QHBoxLayout()
        change_lbl = QLabel("Troco")
        change_lbl.setObjectName("PdvSummaryLabel")
        self.lbl_change_value = QLabel("R$ 0,00")
        self.lbl_change_value.setObjectName("PdvChangeValue")
        change_row.addWidget(change_lbl)
        change_row.addStretch()
        change_row.addWidget(self.lbl_change_value)
        
        summary_layout.addLayout(subtotal_row)
        summary_layout.addLayout(total_row)
        summary_layout.addLayout(change_row)
        payment_layout.addWidget(summary)
        rl.addWidget(payment_section)

        actions_wrap = QFrame()
        actions_wrap.setObjectName("PdvBottomActions")
        actions = QHBoxLayout(actions_wrap)
        actions.setContentsMargins(0, 0, 0, 0)
        actions.setSpacing(8)
        
        self.btn_finish = QPushButton("Finalizar Venda")
        self.btn_finish.setObjectName("PdvFinishButton")
        self.btn_finish.setMinimumHeight(42)
        self.btn_finish.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_finish.setStyleSheet("""
            QPushButton#PdvFinishButton {
                background-color: #6366F1;
                color: white;
                border-radius: 8px;
                font-weight: bold;
                font-size: 14px;
                border: none;
            }
            QPushButton#PdvFinishButton:hover {
                background-color: #4F46E5;
            }
            QPushButton#PdvFinishButton:pressed {
                background-color: #4338CA;
            }
            QPushButton#PdvFinishButton:disabled {
                background-color: #CBD5E1;
                color: #94A3B8;
                border: 1px solid #E2E8F0;
            }
        """)
        self.btn_finish.clicked.connect(self.finalize_sale)
        
        btn_print = QPushButton("Imprimir")
        btn_print.setObjectName("PdvPrintButton")
        btn_print.setMinimumSize(54, 42)
        btn_print.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_print.setStyleSheet("""
            QPushButton#PdvPrintButton {
                background-color: #F1F5F9;
                border: 1px solid #E2E8F0;
                border-radius: 8px;
                color: #475569;
                font-weight: 600;
            }
            QPushButton#PdvPrintButton:hover {
                background-color: #E2E8F0;
                color: #0F172A;
            }
        """)
        btn_print.clicked.connect(self.print_last_sale_receipt)
        
        actions.addWidget(self.btn_finish, 1)
        actions.addWidget(btn_print)
        rl.addWidget(actions_wrap)

        self._set_primary_payment(self.selected_payment_method)
        self._on_discount_mode_changed()
        self.density_combo.setCurrentIndex(2)
        self._apply_density("ultra")
        self.refresh_cart_table()

        split.addWidget(right, 2)

        self._bind_shortcuts()

    def _bind_shortcuts(self) -> None:
        # Return/Enter NAO podem ser atalho de finalizar venda: leitores de codigo de
        # barras enviam Enter ao final da leitura, o que fechava a venda sozinho.
        # O Enter e tratado pelo campo de busca (_on_search_return).
        shortcuts = [
            ("F2", "Pagamento Dinheiro", lambda: self._add_quick_payment("DINHEIRO")),
            ("F3", "Pagamento Debito", lambda: self._add_quick_payment("DEBITO")),
            ("F4", "Pagamento Credito", lambda: self._add_quick_payment("CREDITO_AVISTA")),
            ("F5", "Pagamento PIX", lambda: self._add_quick_payment("PIX")),
            ("Escape", "Limpar Venda", self.clear_sale),
        ]
        for key, text, callback in shortcuts:
            action = QAction(text, self)
            action.setShortcut(key)
            action.setShortcutContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)
            action.triggered.connect(callback)
            self.addAction(action)

    def showEvent(self, event) -> None:  # type: ignore[override]
        super().showEvent(event)
        self.search_edit.setFocus()

    def _reset_search_for_next_scan(self) -> None:
        """Deixa o campo de busca pronto para a proxima leitura do leitor de codigo de barras."""
        self.search_edit.clear()
        self.search_edit.setFocus()

    def _on_search_return(self) -> None:
        """Enter na busca: adiciona o produto lido/encontrado; com a busca vazia, finaliza a venda."""
        term = self.search_edit.text().strip()
        if not term:
            self.finalize_sale()
            return

        product_id: int | None = None
        exact = self.db.fetch_one("SELECT id FROM products WHERE active = 1 AND barcode = ?", (term,))
        if exact:
            product_id = int(exact["id"])
        else:
            like = f"%{term}%"
            matches = self.db.fetch_all(
                "SELECT id FROM products WHERE active = 1 AND (name LIKE ? OR barcode LIKE ?) ORDER BY name LIMIT 2",
                (like, like),
            )
            if len(matches) == 1:
                product_id = int(matches[0]["id"])
            else:
                message = (
                    "Nenhum produto encontrado para esta busca."
                    if not matches
                    else "Mais de um produto encontrado. Clique no produto desejado."
                )
                QToolTip.showText(
                    self.search_edit.mapToGlobal(self.search_edit.rect().bottomLeft()),
                    message,
                    self.search_edit,
                )
                return
        self.add_product_by_id(product_id)

    def _toggle_secondary_payment(self, enabled: bool) -> None:
        self.secondary_payment_wrap.setVisible(enabled)
        if enabled:
            _gross, net, _cash_expected, _received, _change, _pending = self._sale_totals()
            self.secondary_amount_spin.setValue(round(net / 2, 2) if net > 0 else 0)
        else:
            self.secondary_amount_spin.setValue(0)
        self.update_totals()

    def _fill_secondary_with_remaining(self) -> None:
        gross = self._gross_total()
        net = round(max(0.0, gross - self.discount_spin.value()), 2)
        if net <= 0:
            self.secondary_amount_spin.setValue(0)
            return
        if str(self.secondary_method_combo.currentData() or "") == self.selected_payment_method:
            self.secondary_amount_spin.setValue(0)
            return
        self.secondary_amount_spin.setValue(net)

    def _metric_tile(self, label_text: str, value_label: QLabel, metric_name: str) -> QFrame:
        tile = QFrame()
        tile.setObjectName("MetricTile")
        tile.setProperty("pdvMetric", metric_name)
        layout = QVBoxLayout(tile)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(2)
        label = QLabel(label_text)
        label.setObjectName("MetricLabel")
        label.setProperty("pdvMetric", metric_name)
        value_label.setObjectName("MetricValue")
        value_label.setProperty("pdvMetric", metric_name)
        value_label.setMinimumHeight(22)
        value_label.setWordWrap(False)
        layout.addWidget(label)
        layout.addWidget(value_label)
        return tile

    def load_products(self) -> None:
        term = f"%{self.search_edit.text().strip()}%"
        # Contagens via SQL (sem renderizar): manter o PDV leve mesmo com muitos produtos.
        totals = self.db.fetch_one(
            """
            SELECT COUNT(*) AS total,
                   COALESCE(SUM(CASE WHEN stock_qty <= min_qty THEN 1 ELSE 0 END), 0) AS low_stock
            FROM products
            WHERE active = 1 AND (name LIKE ? OR barcode LIKE ?)
            """,
            (term, term),
        )
        total = int(totals["total"] or 0)
        low_count = int(totals["low_stock"] or 0)
        rows = self.db.fetch_all(
            """
            SELECT id, COALESCE(barcode,'') AS barcode, name, sale_price, stock_qty, min_qty, COALESCE(image_path,'') AS image_path
            FROM products
            WHERE active = 1 AND (name LIKE ? OR barcode LIKE ?)
            ORDER BY name
            LIMIT ?
            """,
            (term, term, self.PRODUCT_CARD_LIMIT),
        )

        while self.products_grid.count():
            child = self.products_grid.takeAt(0)
            widget = child.widget()
            if widget is not None:
                widget.deleteLater()

        if total > len(rows):
            self.products_count.setText(f"Mostrando {len(rows)} de {total} produtos — refine a busca")
        else:
            self.products_count.setText(f"{total} produtos encontrados")

        for idx, r in enumerate(rows):
            image_path = r["image_path"] or str(DEFAULT_PRODUCT_IMAGE)

            stock = float(r["stock_qty"] or 0.0)
            min_stock = float(r["min_qty"] or 0.0)
            status_text = "Normal"
            if stock <= min_stock:
                status_text = "Crítico"
            elif stock <= (min_stock * 1.25 if min_stock > 0 else 2):
                status_text = "Baixo"

            code_text = (r["barcode"] or f"ID-{r['id']}")[:14]
            card = QPushButton(f"{code_text}\n{r['name']}\n{fmt_money(r['sale_price'])}")
            card.setObjectName("ProductTileButton")
            card.setIcon(QIcon(load_thumbnail(image_path)))
            card.setIconSize(QSize(46, 46))
            card.setCursor(Qt.CursorShape.PointingHandCursor)
            card.setMinimumHeight(86)
            card.setToolTip(f"Estoque: {r['stock_qty']} | Status: {status_text}")
            
            # INTERFACE CRÍTICA: Ajusta alinhamento e adiciona espaçamento interno esquerdo para afastar o texto
            card.setStyleSheet("""
                QPushButton#ProductTileButton {
                    text-align: left;
                    padding-left: 12px;
                    background-color: #FFFFFF;
                    border: 1px solid #E2E8F0;
                    border-radius: 8px;
                    color: #1E293B;
                    font-weight: 500;
                }
                QPushButton#ProductTileButton:hover {
                    background-color: #F8FAFC;
                    border-color: #CBD5E1;
                }
            """)
            card.clicked.connect(lambda _=False, pid=int(r["id"]): self.add_product_by_id(pid))

            row_idx = idx // 3
            col_idx = idx % 3
            self.products_grid.addWidget(card, row_idx, col_idx)

        # INTERFACE CRÍTICA: Estilo do banner dinâmico. Limpo/transparente quando OK, colorido apenas em Alerta.
        if low_count:
            self.stock_hint.setText(f"Alerta: {low_count} produto(s) em estoque mínimo/baixo")
            self.stock_hint.setStyleSheet("""
                QLabel#PdvHintBadge {
                    background-color: #FEF3C7;
                    color: #D97706;
                    border: 1px solid #FCD34D;
                    border-radius: 6px;
                    padding: 6px 10px;
                    font-weight: 600;
                }
            """)
        else:
            self.stock_hint.setText("Sem alerta de estoque no filtro atual.")
            self.stock_hint.setStyleSheet("""
                QLabel#PdvHintBadge {
                    background-color: transparent;
                    color: #94A3B8;
                    border: none;
                    padding: 2px 0px;
                    font-weight: normal;
                }
            """)

        self.stock_hint.style().unpolish(self.stock_hint)
        self.stock_hint.style().polish(self.stock_hint)

    def _has_stock_for(self, product_id: int, wanted_qty: float) -> bool:
        row = self.db.fetch_one("SELECT name, stock_qty FROM products WHERE id = ?", (product_id,))
        available = float(row["stock_qty"] or 0) if row else 0.0
        if wanted_qty > available + 1e-9:
            name = row["name"] if row else "Produto"
            QMessageBox.warning(
                self,
                "Estoque",
                f"Estoque insuficiente para '{name}'.\nDisponível: {available:g} unidade(s).",
            )
            return False
        return True

    def add_product_by_id(self, product_id: int) -> None:
        self.selected_product_id = product_id
        product = self.db.fetch_one(
            "SELECT id, name, sale_price, cost_price, stock_qty, min_qty, COALESCE(image_path,'') AS image_path FROM products WHERE id = ?",
            (product_id,),
        )
        if not product:
            return
        if float(product["stock_qty"]) <= 0:
            QMessageBox.warning(self, "Estoque", "Produto sem estoque.")
            return

        for item in self.cart:
            if item["product_id"] == product_id:
                if not self._has_stock_for(product_id, item["qty"] + 1):
                    return
                item["qty"] += 1
                self.refresh_cart_table()
                self._reset_search_for_next_scan()
                return

        self.cart.append(
            {
                "product_id": int(product["id"]),
                "name": product["name"],
                "qty": 1,
                "unit_price": float(product["sale_price"]),
                "unit_cost": float(product["cost_price"]),
                "image_path": product["image_path"] or str(DEFAULT_PRODUCT_IMAGE),
            }
        )
        self.refresh_cart_table()
        self._reset_search_for_next_scan()

    def load_clients(self) -> None:
        current_id = self.client_combo.currentData()
        self.client_combo.clear()
        self.client_combo.addItem("Consumidor Final", None)
        for r in self.db.fetch_all("SELECT id, name FROM clients ORDER BY name"):
            self.client_combo.addItem(r["name"], int(r["id"]))
        if current_id is not None:
            idx = self.client_combo.findData(current_id)
            if idx >= 0:
                self.client_combo.setCurrentIndex(idx)
        self._update_client_display()

    def _update_client_display(self) -> None:
        client_id = self.client_combo.currentData()
        if client_id is None:
            self.client_pick_btn.setText("Consumidor Final")
            self.client_pick_btn.setIcon(_vector_icon("user", "#64748b"))
            self.client_pick_btn.setStyleSheet(
                "QPushButton { text-align:left; padding:0 12px; border:1px solid #d5dde7; border-radius:10px;"
                " background:#ffffff; color:#64748b; font-weight:600; }"
                "QPushButton:hover { border-color:#2563eb; color:#1e293b; }"
            )
            self.client_clear_btn.setVisible(False)
        else:
            self.client_pick_btn.setText(self.client_combo.currentText())
            self.client_pick_btn.setIcon(_vector_icon("check", "#16a34a"))
            self.client_pick_btn.setStyleSheet(
                "QPushButton { text-align:left; padding:0 12px; border:1px solid #86efac; border-radius:10px;"
                " background:#f0fdf4; color:#166534; font-weight:800; }"
                "QPushButton:hover { background:#dcfce7; }"
            )
            self.client_clear_btn.setVisible(True)

    def load_exchange(self, origin_sale_id: int, items: list[dict], client_id: int | None, original_total: float) -> None:
        self.cart = []
        for it in items:
            product = self.db.fetch_one("SELECT COALESCE(image_path,'') AS image_path FROM products WHERE id = ?", (it["product_id"],))
            self.cart.append({**it, "image_path": (product["image_path"] if product else "") or str(DEFAULT_PRODUCT_IMAGE)})
        self._set_pdv_client(client_id)
        self.refresh_cart_table()
        QMessageBox.information(
            self,
            "Troca de produto",
            f"Venda #{origin_sale_id} cancelada (valor original {fmt_money(original_total)}).\n\n"
            "Ajuste os itens do carrinho (troque o produto, quantidade ou preco) e finalize a nova venda.\n"
            "Se a nova venda for de valor maior, cobre a diferenca; se menor, devolva a diferenca ao cliente.",
        )

    def _set_pdv_client(self, client_id: int | None) -> None:
        idx = self.client_combo.findData(client_id)
        self.client_combo.setCurrentIndex(idx if idx >= 0 else 0)
        self._update_client_display()

    def open_client_picker(self) -> None:
        rows = self.db.fetch_all("SELECT id, name, phone FROM clients ORDER BY name")
        dlg = QDialog(self)
        dlg.setWindowTitle("Selecionar cliente")
        dlg.resize(460, 520)
        layout = QVBoxLayout(dlg)
        search = QLineEdit()
        search.setPlaceholderText("Digite o nome ou telefone do cliente...")
        search.addAction(_vector_icon("search", "#64748b"), QLineEdit.ActionPosition.LeadingPosition)
        search.setClearButtonEnabled(True)
        search.setMinimumHeight(38)
        layout.addWidget(search)
        listing = QListWidget()
        listing.setStyleSheet("QListWidget::item { padding: 10px 8px; }")
        layout.addWidget(listing, 1)
        info = QLabel()
        info.setStyleSheet("color:#64748b;")
        layout.addWidget(info)
        btn_default = QPushButton("Consumidor Final (sem cadastro)")
        btn_default.setMinimumHeight(36)
        layout.addWidget(btn_default)

        def fill() -> None:
            term = normalize_receipt_text(search.text().strip()).lower()
            listing.clear()
            for r in rows:
                phone = str(r["phone"] or "").strip()
                haystack = normalize_receipt_text(f"{r['name']} {phone}").lower()
                if term and term not in haystack:
                    continue
                item = QListWidgetItem(f"{r['name']}" + (f"   •   {phone}" if phone else ""))
                item.setData(Qt.ItemDataRole.UserRole, int(r["id"]))
                listing.addItem(item)
            info.setText(f"{listing.count()} cliente(s) encontrado(s)")
            if listing.count():
                listing.setCurrentRow(0)

        def choose(item: QListWidgetItem | None = None) -> None:
            item = item or listing.currentItem()
            if item is None:
                return
            self._set_pdv_client(item.data(Qt.ItemDataRole.UserRole))
            dlg.accept()

        def choose_default() -> None:
            self._set_pdv_client(None)
            dlg.accept()

        search.textChanged.connect(fill)
        search.returnPressed.connect(choose)
        listing.itemActivated.connect(choose)
        listing.itemDoubleClicked.connect(choose)
        btn_default.clicked.connect(choose_default)
        fill()
        search.setFocus()
        dlg.exec()

    def refresh(self) -> None:
        self.load_products()
        self.load_clients()

    def add_selected_product(self) -> None:
        if self.selected_product_id is None:
            return
        self.add_product_by_id(self.selected_product_id)

    def refresh_cart_table(self) -> None:
        if self.selected_cart_index is not None and self.selected_cart_index >= len(self.cart):
            self.selected_cart_index = None

        self.cart_title.setText(f"Carrinho ({len(self.cart)})")
        self._clear_layout(self.cart_items_layout)

        for idx, i in enumerate(self.cart):
            row = QFrame()
            row.setObjectName("PdvCartRow")
            row.setProperty("selected", "true" if idx == self.selected_cart_index else "false")
            
            row.setStyleSheet("""
                QFrame#PdvCartRow {
                    background-color: #FFFFFF;
                    border: 1px solid #E2E8F0;
                    border-radius: 8px;
                }
                QFrame#PdvCartRow:hover {
                    background-color: #F8FAFC;
                    border-color: #CBD5E1;
                }
                QFrame#PdvCartRow[selected="true"] {
                    background-color: #EFF6FF;
                    border-color: #3B82F6;
                }
            """)
            
            row_layout = QHBoxLayout(row)
            row_layout.setContentsMargins(8, 7, 8, 7)
            row_layout.setSpacing(8)

            thumb = QLabel()
            thumb.setObjectName("PdvCartThumb")
            thumb.setPixmap(load_thumbnail(i.get("image_path") or str(DEFAULT_PRODUCT_IMAGE)))
            thumb.setFixedSize(40, 40)
            thumb.setAlignment(Qt.AlignmentFlag.AlignCenter)
            thumb.setStyleSheet("QLabel { border-radius: 4px; background-color: #F1F5F9; border: none; }")

            info = QVBoxLayout()
            info.setSpacing(1)
            name = QLabel(str(i["name"]))
            name.setObjectName("PdvCartItemName")
            name.setStyleSheet("QLabel { font-weight: 600; color: #1E293B; font-size: 13px; background: transparent; border: none; }")
            
            price = QLabel(f"{fmt_money(i['unit_price'])} x {int(i['qty'])} = {fmt_money(i['qty'] * i['unit_price'])}")
            price.setObjectName("PdvCartItemPrice")
            price.setStyleSheet("QLabel { color: #64748B; font-size: 12px; font-weight: 500; background: transparent; border: none; }")
            info.addWidget(name)
            info.addWidget(price)

            controls = QHBoxLayout()
            controls.setSpacing(4)
            
            mini_btn_style = """
                QPushButton {
                    background-color: #F1F5F9;
                    border: 1px solid #E2E8F0;
                    border-radius: 6px;
                    color: #1E293B;
                    font-size: 14px;
                    font-weight: bold;
                    padding: 0px;
                }
                QPushButton:hover {
                    background-color: #E2E8F0;
                    color: #0F172A;
                    border-color: #94A3B8;
                }
                QPushButton:pressed {
                    background-color: #CBD5E1;
                }
            """

            btn_minus = QPushButton("-")
            btn_minus.setObjectName("PdvMiniButton")
            btn_minus.setFixedSize(26, 26)
            btn_minus.setStyleSheet(mini_btn_style)
            btn_minus.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_minus.clicked.connect(lambda _=False, ridx=idx: self._change_qty_row(ridx, -1))
            
            qty_lbl = QLabel(str(int(i["qty"])))
            qty_lbl.setObjectName("PdvCartQty")
            qty_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            qty_lbl.setFixedWidth(18)
            qty_lbl.setStyleSheet("QLabel { font-weight: bold; color: #1E293B; font-size: 13px; background: transparent; border: none; }")
            
            btn_plus = QPushButton("+")
            btn_plus.setObjectName("PdvMiniButton")
            btn_plus.setFixedSize(26, 26)
            btn_plus.setStyleSheet(mini_btn_style)
            btn_plus.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_plus.clicked.connect(lambda _=False, ridx=idx: self._change_qty_row(ridx, +1))
            
            btn_del = QPushButton("✕")
            btn_del.setObjectName("PdvMiniDanger")
            btn_del.setFixedSize(26, 26)
            btn_del.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_del.setStyleSheet("""
                QPushButton {
                    background-color: #FEE2E2;
                    border: 1px solid #FCA5A5;
                    border-radius: 6px;
                    color: #DC2626;
                    font-size: 12px;
                    font-weight: bold;
                    padding: 0px;
                }
                QPushButton:hover {
                    background-color: #FCA5A5;
                    color: #991B1B;
                    border-color: #F87171;
                }
                QPushButton:pressed {
                    background-color: #F87171;
                }
            """)
            btn_del.clicked.connect(lambda _=False, ridx=idx: self._remove_row(ridx))
            
            controls.addWidget(btn_minus)
            controls.addWidget(qty_lbl)
            controls.addWidget(btn_plus)
            controls.addWidget(btn_del)

            row_layout.addWidget(thumb)
            row_layout.addLayout(info, 1)
            row_layout.addLayout(controls)
            self.cart_items_layout.addWidget(row)

            row.mousePressEvent = lambda _event, ridx=idx: self._set_selected_cart_index(ridx)  # type: ignore[assignment]

        self.cart_items_layout.addStretch(1)
        self.update_totals()

    def _change_qty_row(self, row: int, delta: int) -> None:
        if row < 0 or row >= len(self.cart):
            return
        new_qty = self.cart[row]["qty"] + delta
        if delta > 0 and not self._has_stock_for(self.cart[row]["product_id"], new_qty):
            return
        if new_qty <= 0:
            self.cart.pop(row)
            if self.selected_cart_index == row:
                self.selected_cart_index = None
        else:
            self.cart[row]["qty"] = new_qty
            self.selected_cart_index = row
        self.refresh_cart_table()

    def _remove_row(self, row: int) -> None:
        if row < 0 or row >= len(self.cart):
            return
        self.cart.pop(row)
        if self.selected_cart_index == row:
            self.selected_cart_index = None
        self.refresh_cart_table()

    def update_totals(self) -> None:
        if not self._syncing_discount:
            self._sync_discount_from_input()
        gross, net, cash_expected, _received, change, pending = self._sale_totals()

        self.lbl_subtotal_value.setText(fmt_money(gross))
        self.lbl_total_value.setText(fmt_money(net))
        self.lbl_change_value.setText(fmt_money(change))

        payments = self._build_payment_parts(net)
        if payments:
            first = payments[0]
            self.primary_split_label.setText(f"1ª forma calculada: {self._method_display_name(first.method)} {fmt_money(first.amount)}")
        else:
            self.primary_split_label.setText("1ª forma calculada: R$ 0,00")

        if len(payments) <= 1:
            if payments:
                self.payment_split_hint.setText(f"Pagamento: {self._method_display_name(payments[0].method)} {fmt_money(payments[0].amount)}")
            else:
                self.payment_split_hint.setText("")
        else:
            primary = payments[0]
            secondary = payments[1]
            self.payment_split_hint.setText(
                f"1ª forma: {self._method_display_name(primary.method)} {fmt_money(primary.amount)}  |  2ª forma: {self._method_display_name(secondary.method)} {fmt_money(secondary.amount)}"
            )

        if self.secondary_payment_btn.isChecked() and str(self.secondary_method_combo.currentData() or "") == self.selected_payment_method:
            self.payment_split_hint.setText("2ª forma igual à principal: a divisão será ignorada.")

        self.lbl_change_value.setProperty("state", "ok" if change > 0 else "neutral")
        self.lbl_change_value.style().unpolish(self.lbl_change_value)
        self.lbl_change_value.style().polish(self.lbl_change_value)

        if cash_expected > 0 and pending > 0:
            self.btn_finish.setEnabled(False)
            self.btn_finish.setToolTip("Valor recebido em dinheiro menor que o total da venda.")
        else:
            self.btn_finish.setEnabled(True)
            self.btn_finish.setToolTip("")

    def _payment_sum(self) -> float:
        _gross, net, _cash_expected, _received, _change, _pending = self._sale_totals()
        return net

    def add_payment(self) -> None:
        self.update_totals()

    def _show_pix_qr_dialog(self, amount: float | None = None) -> bool:
        company = self.db.fetch_one("SELECT pix_key, fantasy_name FROM company_config WHERE id = 1")
        key = ((company["pix_key"] if company else "") or "").strip()
        if amount is None or isinstance(amount, bool):
            amount = self._sale_totals()[1] if self.cart else 0.0

        dlg = QDialog(self)
        dlg.setWindowTitle("Recebimento PIX")
        layout = QVBoxLayout(dlg)

        if not key:
            warn = QLabel("Chave PIX não cadastrada em Configurações. Confirme o recebimento manualmente.")
            warn.setWordWrap(True)
            layout.addWidget(warn)
        else:
            layout.addWidget(QLabel(f"Chave PIX: {key}"))
            if amount > 0:
                layout.addWidget(QLabel(f"Valor: {fmt_money(amount)}"))
            if qrcode:
                try:
                    name = (company["fantasy_name"] if company else "") or "LOJA"
                    payload = _build_pix_payload(key, float(amount), name)
                    img = qrcode.make(payload)
                    from io import BytesIO

                    buf = BytesIO()
                    img.save(buf, format="PNG")
                    pix = QPixmap()
                    pix.loadFromData(buf.getvalue(), "PNG")
                    lbl = QLabel()
                    lbl.setPixmap(pix.scaled(250, 250, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
                    lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
                    layout.addWidget(lbl)
                except Exception as exc:
                    layout.addWidget(QLabel(f"Não foi possível gerar o QR Code: {exc}"))
            else:
                layout.addWidget(QLabel("Módulo qrcode não instalado. Instale dependências."))

        btns = QDialogButtonBox()
        btn_confirm = btns.addButton("CONFIRMAR RECEBIMENTO", QDialogButtonBox.ButtonRole.AcceptRole)
        btn_cancel = btns.addButton("CANCELAR", QDialogButtonBox.ButtonRole.RejectRole)
        btn_confirm.clicked.connect(dlg.accept)
        btn_cancel.clicked.connect(dlg.reject)
        layout.addWidget(btns)

        return dlg.exec() == QDialog.DialogCode.Accepted
    def change_qty(self, delta: int) -> None:
        row = self.selected_cart_index
        if row is None or row < 0 or row >= len(self.cart):
            return
        new_qty = self.cart[row]["qty"] + delta
        if delta > 0 and not self._has_stock_for(self.cart[row]["product_id"], new_qty):
            return
        if new_qty <= 0:
            self.cart.pop(row)
            self.selected_cart_index = None
        else:
            self.cart[row]["qty"] = new_qty
            self.selected_cart_index = row
        self.refresh_cart_table()

    def remove_item(self) -> None:
        row = self.selected_cart_index
        if row is None or row < 0 or row >= len(self.cart):
            return
        self.cart.pop(row)
        self.selected_cart_index = None
        self.refresh_cart_table()

    def _collect_payments(self) -> list[PaymentPart]:
        _gross, net, _cash_expected, _received, _change, _pending = self._sale_totals()
        return self._build_payment_parts(net)

    def finalize_sale(self) -> None:
        if not self.cart:
            QMessageBox.warning(self, "PDV", "Carrinho vazio.")
            return

        _gross, net, cash_expected, _received, _change, pending = self._sale_totals()
        if cash_expected > 0 and pending > 0:
            QMessageBox.warning(self, "PDV", "Valor recebido em dinheiro é menor que o total da venda.")
            return

        pix_amount = sum(p.amount for p in self._collect_payments() if p.method == "PIX")
        if pix_amount > 0:
            if not self._show_pix_qr_dialog(pix_amount):
                return

        try:
            preview = self.sales_service.preview_sale(
                [
                    CartItem(
                        product_id=i["product_id"],
                        name=i["name"],
                        qty=float(i["qty"]),
                        unit_price=float(i["unit_price"]),
                        unit_cost=float(i["unit_cost"]),
                    )
                    for i in self.cart
                ],
                discount=float(self.discount_spin.value()),
                payments=self._collect_payments(),
            )
        except Exception as exc:
            QMessageBox.warning(self, "PDV", str(exc))
            return

        try:
            sale_id = self.sales_service.finalize_sale(
                user_id=self.user.id,
                client_id=self.client_combo.currentData(),
                preview=preview,
            )
        except ValueError as exc:
            log_error("Falha ao finalizar venda", exc)
            QMessageBox.warning(self, "PDV", str(exc))
            return
        self.last_sale_id = sale_id
        log_info(f"Venda #{sale_id} finalizada (total {fmt_money(preview.get('net_total', 0))})")

        msg = self._make_receipt_text(sale_id, preview)
        _show_receipt_preview(self, self.db, self.printer_service, sale_id, msg)
        self.clear_sale()

    def print_last_sale_receipt(self) -> None:
        if not self.last_sale_id:
            QMessageBox.information(self, "Impressão", "Finalize uma venda para liberar a impressão do cupom.")
            return

        text = self._receipt_text_from_sale(self.last_sale_id)
        logo_path, paper_type = _receipt_print_options(self.db)
        result = self.printer_service.print_receipt_text(text, logo_path=logo_path, paper_type=paper_type)
        if result.ok:
            QMessageBox.information(self, "Impressão", result.message)
        else:
            QMessageBox.warning(self, "Impressão", result.message)

    def _make_receipt_text(self, sale_id: int, preview: dict) -> str:
        return _build_receipt_text(self.db, sale_id, preview)

    def clear_sale(self) -> None:
        self.cart = []
        self.selected_product_id = None
        self.selected_cart_index = None
        self.cash_received_spin.setValue(0)
        self._set_pdv_client(None)
        self.secondary_payment_btn.setChecked(False)
        self.secondary_amount_spin.setValue(0)
        self.discount_mode_combo.setCurrentIndex(0)
        self.discount_input_spin.setValue(0)
        self.discount_spin.setValue(0)
        self._set_primary_payment("DINHEIRO")
        self.refresh_cart_table()

    def show_history(self) -> None:
        rows = self.db.fetch_all(
            """
            SELECT s.id, s.created_at, COALESCE(c.name,'Consumidor Final') client,
                   s.net_total, s.discount_total
            FROM sales s
            LEFT JOIN clients c ON c.id = s.client_id
            WHERE s.status <> 'CANCELADA'
            ORDER BY s.id DESC
            LIMIT 200
            """
        )
        dlg = QDialog(self)
        dlg.setWindowTitle("Histórico de Vendas")
        dlg.resize(760, 480)
        layout = QVBoxLayout(dlg)
        table = QTableWidget(0, 5)
        table.setHorizontalHeaderLabels(["Venda", "Data", "Cliente", "Total", "Desconto"])
        fill_table(table, [[r["id"], r["created_at"], r["client"], fmt_money(r["net_total"]), fmt_money(r["discount_total"])] for r in rows])
        layout.addWidget(table)
        btn = QPushButton("Reimprimir Selecionado")

        def reprint() -> None:
            row = table.currentRow()
            if row < 0:
                return
            sale_id = int(table.item(row, 0).text())
            text = self._receipt_text_from_sale(sale_id)
            logo_path, paper_type = _receipt_print_options(self.db)
            result = self.printer_service.print_receipt_text(text, logo_path=logo_path, paper_type=paper_type)
            if result.ok:
                QMessageBox.information(dlg, "Impressão", result.message)
            else:
                QMessageBox.warning(dlg, "Impressão", result.message)

        btn.clicked.connect(reprint)
        layout.addWidget(btn)

        btn_preview = QPushButton("Visualizar Cupom")

        def preview_receipt() -> None:
            row = table.currentRow()
            if row < 0:
                return
            sale_id = int(table.item(row, 0).text())
            _show_receipt_preview(dlg, self.db, self.printer_service, sale_id, self._receipt_text_from_sale(sale_id))

        btn_preview.clicked.connect(preview_receipt)
        layout.addWidget(btn_preview)
        dlg.exec()

    def _receipt_text_from_sale(self, sale_id: int) -> str:
        sale = self.db.fetch_one("SELECT * FROM sales WHERE id = ?", (sale_id,))
        if not sale:
            return "Venda nao encontrada."

        items = self.db.fetch_all(
            """
            SELECT i.product_id, i.qty, i.unit_price, p.name AS product_name
            FROM sale_items i
            LEFT JOIN products p ON p.id = i.product_id
            WHERE i.sale_id = ?
            """,
            (sale_id,),
        )
        payments = self.db.fetch_all("SELECT * FROM sale_payments WHERE sale_id = ?", (sale_id,))

        preview = {
            "gross_total": sale["gross_total"],
            "discount_total": sale["discount_total"],
            "net_total": sale["net_total"],
            "items": [{"product_id": i["product_id"], "name": i["product_name"] or f"Produto #{i['product_id']}", "qty": i["qty"], "unit_price": i["unit_price"]} for i in items],
            "payments": [{"method": p["method"], "amount": p["amount"]} for p in payments],
        }
        return self._make_receipt_text(sale_id, preview)

class ProductsPage(BasePage):
    PAGE_SIZE = 11

    def __init__(self, db: Database, user: AuthUser) -> None:
        super().__init__()
        self.setObjectName("ManagementPage")
        self.db = db
        self.user = user
        self._product_rows = []
        self._current_page = 0
        self._build()
        self.refresh()

    def _build(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(14)

        header = QHBoxLayout()
        heading = QVBoxLayout()
        heading.setSpacing(3)
        title = QLabel("Controle de Estoque")
        title.setObjectName("ProductsPageTitle")
        subtitle = QLabel("Gerencie seus produtos, quantidades e alertas de reposição.")
        subtitle.setObjectName("PageSubtitle")
        heading.addWidget(title)
        heading.addWidget(subtitle)
        header.addLayout(heading, 1)

        btn_add = QPushButton("＋  Novo Produto")
        btn_add.setObjectName("ProductsNewButton")
        btn_add.clicked.connect(self.add_item)
        header.addWidget(btn_add)
        root.addLayout(header)

        metrics = QHBoxLayout()
        metrics.setSpacing(14)
        self.metric_products = self._product_metric("▣", "TOTAL DE PRODUTOS", "0", "products")
        self.metric_low_stock = self._product_metric("!", "ESTOQUE BAIXO / CRÍTICO", "0", "low")
        self.metric_inventory_value = self._product_metric("↘", "VALOR EM ESTOQUE", "R$ 0,00", "value")
        metrics.addWidget(self.metric_products, 1)
        metrics.addWidget(self.metric_low_stock, 1)
        metrics.addWidget(self.metric_inventory_value, 1)
        root.addLayout(metrics)

        listing = QFrame()
        listing.setObjectName("ProductsListing")
        listing_layout = QVBoxLayout(listing)
        listing_layout.setContentsMargins(0, 0, 0, 0)
        listing_layout.setSpacing(0)

        top_wrap = QFrame()
        top_wrap.setObjectName("ProductsToolbar")
        top = QHBoxLayout(top_wrap)
        top.setContentsMargins(18, 12, 18, 12)
        top.setSpacing(10)
        self.search = QLineEdit()
        self.search.setObjectName("ProductsSearchInput")
        self.search.setClearButtonEnabled(True)
        self.search.setPlaceholderText("Buscar produto...")
        self.search.textChanged.connect(self._on_search_changed)
        self.search.setMaximumWidth(360)
        top.addWidget(self.search)
        top.addStretch(1)
        self.products_count_label = QLabel("0 produtos")
        self.products_count_label.setObjectName("ProductsCountLabel")
        top.addWidget(self.products_count_label)
        listing_layout.addWidget(top_wrap)

        self.table = QTableWidget(0, 9)
        self.table.setObjectName("ProductsTable")
        self.table.setHorizontalHeaderLabels(["CÓDIGO", "PRODUTO", "FORNECEDOR", "QTD", "MÍN.", "CUSTO", "PREÇO", "STATUS", "AÇÕES"])
        apply_table_preset(self.table)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.itemDoubleClicked.connect(lambda item: self._run_row_action(item.row(), "edit"))
        self.table.verticalHeader().setDefaultSectionSize(58)
        self.table.setColumnWidth(0, 100)
        self.table.setColumnWidth(1, 320)
        self.table.setColumnWidth(2, 140)
        self.table.setColumnWidth(3, 68)
        self.table.setColumnWidth(4, 68)
        self.table.setColumnWidth(5, 110)
        self.table.setColumnWidth(6, 110)
        self.table.setColumnWidth(7, 120)
        self.table.setColumnWidth(8, 132)
        self.table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.table.horizontalHeader().setDefaultAlignment(Qt.AlignmentFlag.AlignCenter)
        listing_layout.addWidget(self.table, 1)

        pager_wrap = QFrame()
        pager_wrap.setObjectName("ProductsPager")
        pager = QHBoxLayout(pager_wrap)
        pager.setContentsMargins(18, 8, 18, 12)
        pager.setSpacing(10)
        self.btn_prev_page = QPushButton("← Anterior")
        self.btn_prev_page.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_prev_page.clicked.connect(lambda: self._go_to_page(self._current_page - 1))
        pager.addWidget(self.btn_prev_page)
        pager.addStretch(1)
        self.page_label = QLabel("Página 1 de 1")
        self.page_label.setObjectName("ProductsPageLabel")
        self.page_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        pager.addWidget(self.page_label)
        pager.addStretch(1)
        self.btn_next_page = QPushButton("Próxima →")
        self.btn_next_page.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_next_page.clicked.connect(lambda: self._go_to_page(self._current_page + 1))
        pager.addWidget(self.btn_next_page)
        listing_layout.addWidget(pager_wrap)
        root.addWidget(listing, 1)

    def _product_metric(self, icon_text: str, caption_text: str, value_text: str, kind: str) -> QFrame:
        card = QFrame()
        card.setObjectName("ProductMetricCard")
        card.setProperty("metric", kind)
        layout = QHBoxLayout(card)
        layout.setContentsMargins(18, 14, 18, 14)
        layout.setSpacing(14)
        icon = QLabel(icon_text)
        icon.setObjectName("ProductMetricIcon")
        icon.setProperty("metric", kind)
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon.setFixedSize(40, 40)
        text_layout = QVBoxLayout()
        text_layout.setSpacing(2)
        caption = QLabel(caption_text)
        caption.setObjectName("ProductMetricCaption")
        value = QLabel(value_text)
        value.setObjectName("ProductMetricValue")
        text_layout.addWidget(caption)
        text_layout.addWidget(value)
        layout.addWidget(icon)
        layout.addLayout(text_layout, 1)
        card.value_label = value
        return card

    def _on_search_changed(self, *_args) -> None:
        self._current_page = 0
        self.refresh()

    def _go_to_page(self, page: int) -> None:
        page = max(0, page)
        if page == self._current_page:
            return
        self._current_page = page
        self.refresh()

    def refresh(self) -> None:
        term = f"%{self.search.text().strip()}%"
        stats = self.db.fetch_one(
            """
            SELECT COUNT(*) AS total,
                   COALESCE(SUM(CASE WHEN stock_qty <= min_qty THEN 1 ELSE 0 END), 0) AS low_stock,
                   COALESCE(SUM(stock_qty * sale_price), 0) AS inventory_value
            FROM products
            WHERE active = 1
            """
        )
        self.metric_products.value_label.setText(str(int(stats["total"] or 0)))
        self.metric_low_stock.value_label.setText(str(int(stats["low_stock"] or 0)))
        self.metric_inventory_value.value_label.setText(fmt_money(stats["inventory_value"] or 0))

        # Paginacao: conta o total filtrado e carrega/renderiza apenas a pagina atual.
        total_rows = int(
            self.db.fetch_one(
                """
                SELECT COUNT(*) AS c
                FROM products p
                LEFT JOIN suppliers s ON s.id = p.supplier_id
                WHERE p.active = 1
                  AND (p.name LIKE ? OR COALESCE(p.barcode,'') LIKE ?
                       OR COALESCE(s.fantasy_name,'') LIKE ? OR COALESCE(p.description,'') LIKE ?)
                """,
                (term, term, term, term),
            )["c"]
            or 0
        )
        total_pages = max(1, (total_rows + self.PAGE_SIZE - 1) // self.PAGE_SIZE)
        self._current_page = max(0, min(self._current_page, total_pages - 1))

        rows = self.db.fetch_all(
            """
            SELECT p.id, COALESCE(p.barcode,'') AS barcode, p.name,
                   COALESCE(p.description,'') AS description,
                   COALESCE(s.fantasy_name,'') AS supplier,
                   p.cost_price, p.sale_price, p.stock_qty, p.min_qty,
                   COALESCE(p.image_path,'') AS image_path
            FROM products p
            LEFT JOIN suppliers s ON s.id = p.supplier_id
            WHERE p.active = 1
              AND (p.name LIKE ? OR COALESCE(p.barcode,'') LIKE ?
                   OR COALESCE(s.fantasy_name,'') LIKE ? OR COALESCE(p.description,'') LIKE ?)
            ORDER BY p.name
            LIMIT ? OFFSET ?
            """,
            (term, term, term, term, self.PAGE_SIZE, self._current_page * self.PAGE_SIZE),
        )
        self._product_rows = rows
        self.products_count_label.setText(f"{total_rows} produto" + ("s" if total_rows != 1 else ""))
        self.page_label.setText(f"Página {self._current_page + 1} de {total_pages}")
        self.btn_prev_page.setEnabled(self._current_page > 0)
        self.btn_next_page.setEnabled(self._current_page < total_pages - 1)
        data = []
        for product in rows:
            barcode = product["barcode"] or f"ID-{product['id']}"
            cost = "***" if self.user.role == "CAIXA" else fmt_money(product["cost_price"])
            stock = float(product["stock_qty"] or 0)
            minimum = float(product["min_qty"] or 0)
            stock_text = str(int(stock)) if stock.is_integer() else f"{stock:g}"
            minimum_text = str(int(minimum)) if minimum.is_integer() else f"{minimum:g}"
            if stock <= 0:
                status = "Sem estoque"
            elif stock <= minimum:
                status = "Estoque baixo"
            else:
                status = "Normal"
            data.append([barcode, "", product["supplier"] or "—", stock_text, minimum_text, cost, fmt_money(product["sale_price"]), "", ""])
        fill_table(self.table, data)
        header = self.table.horizontalHeader()
        for column in (0, 2, 3, 4, 5, 6, 7, 8):
            header.setSectionResizeMode(column, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setStretchLastSection(False)

        for row_index, product in enumerate(rows):
            identity = QWidget()
            identity.setObjectName("ProductIdentity")
            identity_layout = QHBoxLayout(identity)
            identity_layout.setContentsMargins(8, 4, 8, 4)
            identity_layout.setSpacing(12)
            thumbnail = QLabel()
            thumbnail.setObjectName("ProductThumbnail")
            image_path = product["image_path"] or str(DEFAULT_PRODUCT_IMAGE)
            thumbnail.setPixmap(load_thumbnail(image_path))
            thumbnail.setFixedSize(44, 44)
            thumbnail.setAlignment(Qt.AlignmentFlag.AlignCenter)
            name_wrap = QVBoxLayout()
            name_wrap.setContentsMargins(0, 0, 0, 0)
            name_wrap.setSpacing(2)
            name = QLabel(str(product["name"]))
            name.setObjectName("ProductName")
            name.setWordWrap(False)
            name.setMinimumWidth(0)
            name.setToolTip(str(product["name"]))
            name_wrap.addWidget(name)
            description = str(product["description"] or "").strip()
            if description:
                description_label = QLabel(description)
                description_label.setObjectName("ProductDescription")
                description_label.setWordWrap(False)
                description_label.setToolTip(description)
                name_wrap.addWidget(description_label)
            identity_layout.addWidget(thumbnail)
            identity_layout.addLayout(name_wrap, 1)
            self.table.setCellWidget(row_index, 1, identity)

            for column in (0, 2, 3, 4, 5, 6):
                item = self.table.item(row_index, column)
                if item is not None:
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            stock_item = self.table.item(row_index, 3)
            stock = float(product["stock_qty"] or 0)
            minimum = float(product["min_qty"] or 0)
            if stock_item is not None and stock <= minimum:
                stock_item.setForeground(QColor("#dc2626"))
                stock_item.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))

            if stock <= 0:
                status = "Sem estoque"
                status_state = "empty"
            elif stock <= minimum:
                status = "Estoque baixo"
                status_state = "low"
            else:
                status = "Normal"
                status_state = "normal"
            status_label = QLabel(status)
            status_label.setObjectName("ProductStockBadge")
            status_label.setProperty("status", status_state)
            status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            status_label.setFixedSize(92, 32)
            status_wrap = QWidget()
            status_wrap.setObjectName("ProductStatusWrap")
            status_layout = QHBoxLayout(status_wrap)
            status_layout.setContentsMargins(0, 0, 0, 0)
            status_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            status_layout.addWidget(status_label)
            self.table.setCellWidget(row_index, 7, status_wrap)

            actions = QWidget()
            actions.setObjectName("ProductRowActions")
            actions_layout = QHBoxLayout(actions)
            actions_layout.setContentsMargins(2, 2, 2, 2)
            actions_layout.setSpacing(5)
            actions_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            edit_button = QPushButton("Editar")
            edit_button.setObjectName("ProductRowEditButton")
            edit_button.setFixedSize(56, 32)
            edit_button.setToolTip("Editar produto")
            edit_button.clicked.connect(lambda _checked=False, row=row_index: self._run_row_action(row, "edit"))
            delete_button = QPushButton("Excluir")
            delete_button.setObjectName("ProductRowDeleteButton")
            delete_button.setFixedSize(56, 32)
            delete_button.setToolTip("Excluir produto")
            delete_button.clicked.connect(lambda _checked=False, row=row_index: self._run_row_action(row, "delete"))
            actions_layout.addWidget(edit_button)
            actions_layout.addWidget(delete_button)
            self.table.setCellWidget(row_index, 8, actions)
        self.table.clearSelection()
        self.table.setCurrentCell(-1, -1)

    def _run_row_action(self, row: int, action: str) -> None:
        self.table.setCurrentCell(row, 0)
        if action == "edit":
            self.edit_item()
        else:
            self.delete_item()

    def add_item(self) -> None:
        dlg = ProductDialog(self.db, self.user)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self.refresh()

    def edit_item(self) -> None:
        row = self.table.currentRow()
        if row < 0 or row >= len(self._product_rows):
            return
        product_id = int(self._product_rows[row]["id"])
        dlg = ProductDialog(self.db, self.user, product_id)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self.refresh()

    def delete_item(self) -> None:
        row = self.table.currentRow()
        if row < 0 or row >= len(self._product_rows):
            return
        product_id = int(self._product_rows[row]["id"])
        self.db.execute("UPDATE products SET active = 0 WHERE id = ?", (product_id,))
        self.refresh()


class ProductDialog(QDialog):
    _lookup_done = Signal(object, bool)

    def __init__(self, db: Database, user: AuthUser, product_id: int | None = None) -> None:
        super().__init__()
        self.db = db
        self.user = user
        self.product_id = product_id
        self.image_path = str(DEFAULT_PRODUCT_IMAGE)
        self._lookup_running = False
        self._lookup_done.connect(self._on_lookup_done)
        self.setWindowTitle("Produto")
        self.resize(540, 520)
        self._build()
        self._load_suppliers()
        if product_id:
            self._load_data()

    def _build(self) -> None:
        form = QFormLayout(self)
        self.ed_barcode = QLineEdit()
        self.ed_name = QLineEdit()
        self.ed_desc = QTextEdit()
        self.cb_supplier = QComboBox()
        self.sp_cost = QDoubleSpinBox()
        self.sp_cost.setMaximum(999999)
        self.sp_cost.setPrefix("R$ ")
        self.sp_sale = QDoubleSpinBox()
        self.sp_sale.setMaximum(999999)
        self.sp_sale.setPrefix("R$ ")
        self.sp_stock = QDoubleSpinBox()
        self.sp_stock.setMaximum(999999)
        self.sp_min = QDoubleSpinBox()
        self.sp_min.setMaximum(999999)
        for spin in (self.sp_cost, self.sp_sale, self.sp_stock, self.sp_min):
            spin.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)

        btn_img = QPushButton("Escolher Foto")
        btn_img.clicked.connect(self._choose_image)
        self.btn_web_img = QPushButton("Buscar foto na internet")
        self.btn_web_img.setToolTip("Busca a foto e o nome do produto pelo código de barras (gratuito)")
        self.btn_web_img.clicked.connect(lambda: self._search_web_image(silent=False))
        self.ed_barcode.editingFinished.connect(self._auto_search_web_image)
        self.lbl_preview = QLabel()
        self.lbl_preview.setFixedSize(110, 110)
        self.lbl_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_preview.setStyleSheet("border:1px solid #d5dde7; border-radius:10px; background:#ffffff;")
        self.lbl_lookup_status = QLabel("")
        self.lbl_lookup_status.setWordWrap(True)
        self.lbl_lookup_status.setStyleSheet("color:#64748b;")
        photo_buttons = QHBoxLayout()
        photo_buttons.addWidget(btn_img)
        photo_buttons.addWidget(self.btn_web_img)
        photo_buttons.addStretch(1)
        photo_box = QVBoxLayout()
        photo_box.addLayout(photo_buttons)
        photo_box.addWidget(self.lbl_lookup_status)

        form.addRow("Codigo barras", self.ed_barcode)
        form.addRow("Nome", self.ed_name)
        form.addRow("Descricao", self.ed_desc)
        form.addRow("Fornecedor", self.cb_supplier)

        if self.user.role != "CAIXA":
            form.addRow("Valor custo", self.sp_cost)
        else:
            self.sp_cost.setEnabled(False)

        form.addRow("Valor venda", self.sp_sale)
        form.addRow("Estoque", self.sp_stock)
        form.addRow("Estoque minimo", self.sp_min)
        form.addRow("Foto", photo_box)
        form.addRow("", self.lbl_preview)
        self._update_preview()

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.save)
        buttons.rejected.connect(self.reject)
        form.addRow(buttons)

    def _load_suppliers(self) -> None:
        self.cb_supplier.clear()
        self.cb_supplier.addItem("Sem fornecedor", None)
        for r in self.db.fetch_all("SELECT id, fantasy_name FROM suppliers ORDER BY fantasy_name"):
            self.cb_supplier.addItem(r["fantasy_name"], r["id"])

    def _load_data(self) -> None:
        row = self.db.fetch_one("SELECT * FROM products WHERE id = ?", (self.product_id,))
        if not row:
            return
        self.ed_barcode.setText(row["barcode"] or "")
        self.ed_name.setText(row["name"])
        self.ed_desc.setPlainText(row["description"] or "")
        self.sp_cost.setValue(float(row["cost_price"]))
        self.sp_sale.setValue(float(row["sale_price"]))
        self.sp_stock.setValue(float(row["stock_qty"]))
        self.sp_min.setValue(float(row["min_qty"]))
        self.image_path = row["image_path"] or str(DEFAULT_PRODUCT_IMAGE)
        self._update_preview()
        idx = self.cb_supplier.findData(row["supplier_id"])
        if idx >= 0:
            self.cb_supplier.setCurrentIndex(idx)

    def _choose_image(self) -> None:
        file, _ = QFileDialog.getOpenFileName(self, "Imagem do produto", "", "Imagens (*.png *.jpg *.jpeg *.webp)")
        if file:
            self.image_path = file
            self._update_preview()

    def _update_preview(self) -> None:
        pix = QPixmap(self.image_path or "")
        if pix.isNull():
            pix = QPixmap(str(DEFAULT_PRODUCT_IMAGE))
        self.lbl_preview.setPixmap(pix.scaled(104, 104, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))

    def _auto_search_web_image(self) -> None:
        if self.image_path == str(DEFAULT_PRODUCT_IMAGE) and len(self.ed_barcode.text().strip()) >= 8:
            self._search_web_image(silent=True)

    def _search_web_image(self, silent: bool) -> None:
        if self._lookup_running:
            return
        code = self.ed_barcode.text().strip()
        if not code:
            if not silent:
                QMessageBox.information(self, "Produto", "Digite ou leia o código de barras primeiro.")
            return
        self._lookup_running = True
        self.btn_web_img.setEnabled(False)
        self.lbl_lookup_status.setText("Buscando na internet...")

        def work() -> None:
            try:
                result = lookup_product_by_barcode(code)
            except Exception as exc:  # noqa: BLE001
                from app.services.product_lookup_service import ProductLookupResult

                result = ProductLookupResult(False, message=f"Falha na busca: {exc}")
            self._lookup_done.emit(result, silent)

        threading.Thread(target=work, daemon=True).start()

    def _on_lookup_done(self, result, silent: bool) -> None:
        self._lookup_running = False
        self.btn_web_img.setEnabled(True)
        if not result.found:
            self.lbl_lookup_status.setText("" if silent else result.message)
            return
        parts = []
        if result.image_path:
            self.image_path = result.image_path
            self._update_preview()
            parts.append("foto")
        if result.name and not self.ed_name.text().strip():
            self.ed_name.setText(f"{result.name} {result.brand}".strip() if result.brand and result.brand.lower() not in result.name.lower() else result.name)
            parts.append("nome")
        if not result.image_path:
            self.lbl_lookup_status.setText(result.message or "Produto encontrado, mas sem foto na base. Escolha a foto manualmente.")
            return
        found = " e ".join(parts) if parts else "dados"
        self.lbl_lookup_status.setText(f"Encontrado: {found}. Confira a foto antes de salvar.")

    def save(self) -> None:
        if not self.ed_name.text().strip():
            QMessageBox.warning(self, "Produto", "Nome obrigatorio.")
            return
        if self.product_id:
            self.db.execute(
                """
                UPDATE products
                SET barcode=?, name=?, description=?, supplier_id=?, cost_price=?, sale_price=?, stock_qty=?, min_qty=?, image_path=?
                WHERE id=?
                """,
                (
                    self.ed_barcode.text().strip(),
                    self.ed_name.text().strip(),
                    self.ed_desc.toPlainText().strip(),
                    self.cb_supplier.currentData(),
                    self.sp_cost.value(),
                    self.sp_sale.value(),
                    self.sp_stock.value(),
                    self.sp_min.value(),
                    self.image_path or str(DEFAULT_PRODUCT_IMAGE),
                    self.product_id,
                ),
            )
        else:
            self.db.execute(
                """
                INSERT INTO products(
                    barcode, name, description, supplier_id, cost_price, sale_price,
                    stock_qty, min_qty, image_path, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    self.ed_barcode.text().strip(),
                    self.ed_name.text().strip(),
                    self.ed_desc.toPlainText().strip(),
                    self.cb_supplier.currentData(),
                    self.sp_cost.value(),
                    self.sp_sale.value(),
                    self.sp_stock.value(),
                    self.sp_min.value(),
                    self.image_path or str(DEFAULT_PRODUCT_IMAGE),
                    datetime.now().isoformat(timespec="seconds"),
                ),
            )
        self.accept()


class ClientsPage(BasePage):
    def __init__(self, db: Database) -> None:
        super().__init__()
        self.setObjectName("ManagementPage")
        self.db = db
        self._build()
        self.refresh()

    def _build(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(14)

        header = QHBoxLayout()
        heading = QVBoxLayout()
        heading.setSpacing(3)
        title = QLabel("Clientes")
        title.setObjectName("ClientsPageTitle")
        subtitle = QLabel("Gerencie sua base de clientes e histórico de compras.")
        subtitle.setObjectName("PageSubtitle")
        heading.addWidget(title)
        heading.addWidget(subtitle)
        header.addLayout(heading, 1)

        self.btn_table_view = QPushButton("Tabela")
        self.btn_table_view.setObjectName("ClientViewToggle")
        self.btn_table_view.setCheckable(True)
        self.btn_cards_view = QPushButton("Cards")
        self.btn_cards_view.setObjectName("ClientViewToggle")
        self.btn_cards_view.setCheckable(True)
        self.btn_table_view.clicked.connect(lambda: self._set_client_view(0))
        self.btn_cards_view.clicked.connect(lambda: self._set_client_view(1))
        view_switch = QFrame()
        view_switch.setObjectName("ClientViewSwitch")
        switch_layout = QHBoxLayout(view_switch)
        switch_layout.setContentsMargins(3, 3, 3, 3)
        switch_layout.setSpacing(2)
        switch_layout.addWidget(self.btn_table_view)
        switch_layout.addWidget(self.btn_cards_view)
        header.addWidget(view_switch)

        btn_add = QPushButton("＋  Novo Cliente")
        btn_add.setObjectName("ClientNewButton")
        btn_add.clicked.connect(self.add_item)
        header.addWidget(btn_add)
        root.addLayout(header)

        metrics = QHBoxLayout()
        metrics.setSpacing(14)
        self.metric_clients = self._client_metric("0", "Total de Clientes", "clients")
        self.metric_revenue = self._client_metric("R$ 0,00", "Receita Total", "revenue")
        self.metric_buyers = self._client_metric("0", "Clientes com compras", "buyers")
        metrics.addWidget(self.metric_clients, 1)
        metrics.addWidget(self.metric_revenue, 1)
        metrics.addWidget(self.metric_buyers, 1)
        root.addLayout(metrics)

        listing = QFrame()
        listing.setObjectName("ClientsListing")
        listing_layout = QVBoxLayout(listing)
        listing_layout.setContentsMargins(0, 0, 0, 0)
        listing_layout.setSpacing(0)

        toolbar_wrap = QFrame()
        toolbar_wrap.setObjectName("ClientsToolbar")
        top = QHBoxLayout(toolbar_wrap)
        top.setContentsMargins(18, 12, 18, 12)
        top.setSpacing(8)
        self.search = QLineEdit()
        self.search.setObjectName("ClientSearchInput")
        self.search.setClearButtonEnabled(True)
        self.search.setPlaceholderText("Buscar cliente...")
        self.search.textChanged.connect(self.refresh)
        self.search.setMaximumWidth(360)
        top.addWidget(self.search)

        self.btn_advanced = QPushButton("Busca avançada")
        self.btn_advanced.setObjectName("ClientAdvancedButton")
        self.btn_advanced.setCheckable(True)
        self.btn_advanced.toggled.connect(self._toggle_advanced_search)
        top.addWidget(self.btn_advanced)
        top.addStretch(1)
        self.client_count_label = QLabel("0 clientes")
        self.client_count_label.setObjectName("ClientCountLabel")
        top.addWidget(self.client_count_label)
        listing_layout.addWidget(toolbar_wrap)

        self.advanced_wrap = QFrame()
        self.advanced_wrap.setObjectName("ClientAdvancedFilters")
        advanced = QHBoxLayout(self.advanced_wrap)
        advanced.setContentsMargins(14, 12, 14, 12)
        advanced.setSpacing(10)
        self.filter_phone = QLineEdit()
        self.filter_phone.setPlaceholderText("Telefone")
        self.filter_city = QLineEdit()
        self.filter_city.setPlaceholderText("Cidade")
        self.filter_email = QLineEdit()
        self.filter_email.setPlaceholderText("E-mail")
        for field in (self.filter_phone, self.filter_city, self.filter_email):
            field.textChanged.connect(self.refresh)
            advanced.addWidget(field, 1)
        btn_clear_filters = QPushButton("Limpar filtros")
        btn_clear_filters.setObjectName("SecondaryButton")
        btn_clear_filters.clicked.connect(self._clear_advanced_search)
        advanced.addWidget(btn_clear_filters)
        self.advanced_wrap.setVisible(False)
        listing_layout.addWidget(self.advanced_wrap)

        self.client_views = QStackedWidget()
        self.table = QTableWidget(0, 8)
        self.table.setObjectName("ClientsTable")
        self.table.setHorizontalHeaderLabels(["CLIENTE", "CPF", "TELEFONE", "CIDADE", "TOTAL COMPRAS", "PEDIDOS", "ÚLTIMA COMPRA", "AÇÕES"])
        apply_table_preset(self.table)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.verticalHeader().setDefaultSectionSize(54)
        self.table.setColumnWidth(0, 260)
        self.table.setColumnWidth(1, 135)
        self.table.setColumnWidth(2, 140)
        self.table.setColumnWidth(3, 130)
        self.table.setColumnWidth(4, 130)
        self.table.setColumnWidth(5, 80)
        self.table.setColumnWidth(6, 125)
        self.table.setColumnWidth(7, 100)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setDefaultAlignment(Qt.AlignmentFlag.AlignCenter)
        self.client_views.addWidget(self.table)

        self.cards_scroll = QScrollArea()
        self.cards_scroll.setObjectName("ClientCardsScroll")
        self.cards_scroll.setWidgetResizable(True)
        self.cards_scroll.setFrameShape(QFrame.Shape.NoFrame)
        cards_content = QWidget()
        self.cards_grid = QGridLayout(cards_content)
        self.cards_grid.setContentsMargins(18, 18, 18, 18)
        self.cards_grid.setHorizontalSpacing(14)
        self.cards_grid.setVerticalSpacing(14)
        self.cards_grid.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        for column in range(4):
            self.cards_grid.setColumnStretch(column, 1)
        self.cards_scroll.setWidget(cards_content)
        self.client_views.addWidget(self.cards_scroll)
        listing_layout.addWidget(self.client_views, 1)
        root.addWidget(listing, 1)
        self._set_client_view(0)

    def _client_metric(self, value: str, label_text: str, kind: str) -> QFrame:
        card = QFrame()
        card.setObjectName("ClientMetricCard")
        card.setProperty("metric", kind)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(2)
        value_label = QLabel(value)
        value_label.setObjectName("ClientMetricValue")
        caption = QLabel(label_text)
        caption.setObjectName("ClientMetricCaption")
        caption.setAlignment(Qt.AlignmentFlag.AlignCenter)
        value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(value_label)
        layout.addWidget(caption)
        card.value_label = value_label
        return card

    def _set_client_view(self, index: int) -> None:
        self.client_views.setCurrentIndex(index)
        self.btn_table_view.setChecked(index == 0)
        self.btn_cards_view.setChecked(index == 1)

    def refresh(self) -> None:
        term = f"%{self.search.text().strip()}%"
        phone = f"%{self.filter_phone.text().strip()}%"
        city = f"%{self.filter_city.text().strip()}%"
        email = f"%{self.filter_email.text().strip()}%"
        rows = self.db.fetch_all(
            """
            SELECT c.id, c.name, c.cpf, c.phone, c.email, c.city, c.created_at,
                   COUNT(s.id) AS order_count,
                   COALESCE(SUM(s.net_total), 0) AS total_purchases,
                   MAX(s.created_at) AS last_purchase
            FROM clients c
            LEFT JOIN sales s ON s.client_id = c.id AND s.status <> 'CANCELADA'
            WHERE (c.name LIKE ? OR COALESCE(c.phone,'') LIKE ? OR COALESCE(c.city,'') LIKE ? OR COALESCE(c.email,'') LIKE ? OR COALESCE(c.cpf,'') LIKE ?)
              AND COALESCE(c.phone,'') LIKE ?
              AND COALESCE(c.city,'') LIKE ?
              AND COALESCE(c.email,'') LIKE ?
            GROUP BY c.id, c.name, c.cpf, c.phone, c.email, c.city, c.created_at
            ORDER BY c.name
            """,
            (term, term, term, term, term, phone, city, email),
        )
        self._client_rows = rows
        total_clients = self.db.fetch_one("SELECT COUNT(*) AS total FROM clients")
        sales_summary = self.db.fetch_one(
            "SELECT COUNT(DISTINCT client_id) AS buyers, COALESCE(SUM(net_total), 0) AS revenue FROM sales WHERE client_id IS NOT NULL AND status <> 'CANCELADA'"
        )
        self.metric_clients.value_label.setText(str(int(total_clients["total"] or 0)))
        self.metric_revenue.value_label.setText(fmt_money(sales_summary["revenue"] or 0))
        self.metric_buyers.value_label.setText(str(int(sales_summary["buyers"] or 0)))
        self.client_count_label.setText(f"{len(rows)} cliente" + ("s" if len(rows) != 1 else ""))

        fill_table(
            self.table,
            [["", _format_cpf(r["cpf"] or "") or "—", r["phone"] or "—", r["city"] or "—", fmt_money(r["total_purchases"]), r["order_count"], fmt_date_br(r["last_purchase"] or "") or "—", ""] for r in rows],
        )
        for row_index, client in enumerate(rows):
            avatar_name = str(client["name"] or "?").strip()
            initials = "".join(part[0] for part in avatar_name.split()[:2]).upper() or "?"
            identity = QWidget()
            identity.setObjectName("ClientIdentity")
            identity_layout = QHBoxLayout(identity)
            identity_layout.setContentsMargins(10, 3, 8, 3)
            identity_layout.setSpacing(10)
            avatar = QLabel(initials)
            avatar.setObjectName("ClientAvatar")
            avatar.setProperty("avatarIndex", row_index % 5)
            avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
            avatar.setFixedSize(32, 32)
            name_label = QLabel(avatar_name)
            name_label.setObjectName("ClientName")
            identity_layout.addWidget(avatar)
            identity_layout.addWidget(name_label, 1)
            self.table.setCellWidget(row_index, 0, identity)

            for column in range(1, 7):
                item = self.table.item(row_index, column)
                if item is not None:
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

            actions = QWidget()
            actions.setObjectName("ClientRowActions")
            actions_layout = QHBoxLayout(actions)
            actions_layout.setContentsMargins(2, 2, 2, 2)
            actions_layout.setSpacing(5)
            actions_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            edit_button = QPushButton("Editar")
            edit_button.setObjectName("ClientRowEditButton")
            edit_button.setFixedSize(48, 28)
            edit_button.setToolTip("Editar cliente")
            edit_button.clicked.connect(lambda _checked=False, row=row_index: self._run_row_action(row, "edit"))
            delete_button = QPushButton("Excluir")
            delete_button.setObjectName("ClientRowDeleteButton")
            delete_button.setFixedSize(52, 28)
            delete_button.setToolTip("Excluir cliente")
            delete_button.clicked.connect(lambda _checked=False, row=row_index: self._run_row_action(row, "delete"))
            actions_layout.addWidget(edit_button)
            actions_layout.addWidget(delete_button)
            self.table.setCellWidget(row_index, 7, actions)
        self._refresh_client_cards(rows)

    def _refresh_client_cards(self, rows) -> None:
        while self.cards_grid.count():
            item = self.cards_grid.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        for row_index, client in enumerate(rows):
            card = QFrame()
            card.setObjectName("ClientProfileCard")
            card.setMinimumHeight(240)
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(16, 15, 16, 13)
            card_layout.setSpacing(9)

            identity = QHBoxLayout()
            identity.setSpacing(11)
            avatar_name = str(client["name"] or "?").strip()
            initials = "".join(part[0] for part in avatar_name.split()[:2]).upper() or "?"
            avatar = QLabel(initials)
            avatar.setObjectName("ClientAvatar")
            avatar.setProperty("avatarIndex", row_index % 5)
            avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
            avatar.setFixedSize(42, 42)
            name = QLabel(avatar_name)
            name.setObjectName("ClientCardName")
            name.setWordWrap(True)
            identity.addWidget(avatar)
            identity.addWidget(name, 1)
            card_layout.addLayout(identity)

            contact = QVBoxLayout()
            contact.setSpacing(5)
            for marker, value, tooltip in (
                ("#", _format_cpf(client["cpf"] or "") or "CPF não informado", "CPF"),
                ("T", client["phone"] or "Telefone não informado", "Telefone"),
                ("@", client["email"] or "E-mail não informado", "E-mail"),
                ("L", client["city"] or "Cidade não informada", "Cidade"),
            ):
                contact_row = QHBoxLayout()
                contact_row.setSpacing(8)
                marker_label = QLabel(marker)
                marker_label.setObjectName("ClientContactMarker")
                marker_label.setToolTip(tooltip)
                marker_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                marker_label.setFixedSize(18, 18)
                value_label = QLabel(str(value))
                value_label.setObjectName("ClientContactValue")
                value_label.setToolTip(str(value))
                value_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
                value_label.setWordWrap(False)
                contact_row.addWidget(marker_label)
                contact_row.addWidget(value_label, 1)
                contact.addLayout(contact_row)
            card_layout.addLayout(contact)

            divider = QFrame()
            divider.setObjectName("ClientCardDivider")
            card_layout.addWidget(divider)

            actions = QHBoxLayout()
            purchase_info = QVBoxLayout()
            purchase_info.setSpacing(1)
            purchase_total = QLabel(fmt_money(client["total_purchases"]))
            purchase_total.setObjectName("ClientCardPurchaseTotal")
            order_count = int(client["order_count"] or 0)
            purchase_count = QLabel(f"{order_count} pedido" + ("s" if order_count != 1 else ""))
            purchase_count.setObjectName("ClientCardPurchaseCount")
            purchase_info.addWidget(purchase_total)
            purchase_info.addWidget(purchase_count)
            actions.addLayout(purchase_info, 1)

            edit_button = QPushButton("Editar")
            edit_button.setObjectName("ClientEditButton")
            edit_button.setFixedSize(78, 30)
            edit_button.clicked.connect(lambda _checked=False, row=row_index: self._run_row_action(row, "edit"))
            delete_button = QPushButton("Excluir")
            delete_button.setObjectName("ClientDeleteButton")
            delete_button.setFixedSize(88, 30)
            delete_button.clicked.connect(lambda _checked=False, row=row_index: self._run_row_action(row, "delete"))
            actions.addWidget(edit_button)
            actions.addWidget(delete_button)
            card_layout.addLayout(actions)
            self.cards_grid.addWidget(card, 0, 0)
        self._reflow_client_cards()

    def _reflow_client_cards(self) -> None:
        if not hasattr(self, "cards_grid"):
            return
        available_width = max(1, self.cards_scroll.viewport().width())
        spacing = self.cards_grid.horizontalSpacing()
        columns = self._client_card_column_count(available_width, spacing)

        cards = []
        while self.cards_grid.count():
            item = self.cards_grid.takeAt(0)
            if item.widget() is not None:
                cards.append(item.widget())

        for column in range(4):
            self.cards_grid.setColumnStretch(column, 1 if column < columns else 0)
        for index, card in enumerate(cards):
            self.cards_grid.addWidget(card, index // columns, index % columns)

    @staticmethod
    def _client_card_column_count(available_width: int, spacing: int = 14) -> int:
        card_min_width = 210
        return max(1, min(4, (max(1, available_width) + spacing) // (card_min_width + spacing)))

    def resizeEvent(self, event) -> None:  # type: ignore[override]
        super().resizeEvent(event)
        self._reflow_client_cards()

    def _toggle_advanced_search(self, visible: bool) -> None:
        self.advanced_wrap.setVisible(visible)

    def _clear_advanced_search(self) -> None:
        self.filter_phone.clear()
        self.filter_city.clear()
        self.filter_email.clear()

    def _run_row_action(self, row: int, action: str) -> None:
        self.table.setCurrentCell(row, 0)
        if action == "edit":
            self.edit_item()
        else:
            self.delete_item()

    def add_item(self) -> None:
        dlg = ClientDialog(self.db)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self.refresh()

    def edit_item(self) -> None:
        row = self.table.currentRow()
        if row < 0 or row >= len(self._client_rows):
            return
        dlg = ClientDialog(self.db, int(self._client_rows[row]["id"]))
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self.refresh()

    def delete_item(self) -> None:
        row = self.table.currentRow()
        if row < 0 or row >= len(self._client_rows):
            return
        self.db.execute("DELETE FROM clients WHERE id = ?", (int(self._client_rows[row]["id"]),))
        self.refresh()


class ClientDialog(QDialog):
    def __init__(self, db: Database, client_id: int | None = None) -> None:
        super().__init__()
        self.db = db
        self.client_id = client_id
        self.setWindowTitle("Cliente")
        self._build()
        if client_id:
            self._load()

    def _build(self) -> None:
        form = QFormLayout(self)
        form.setContentsMargins(20, 18, 20, 16)
        form.setVerticalSpacing(12)
        self.setMinimumWidth(460)
        self.ed_name = QLineEdit()
        self.ed_cpf = QLineEdit()
        self.ed_cpf.setPlaceholderText("000.000.000-00")
        self.ed_cpf.setMaxLength(14)
        self.ed_cpf.textEdited.connect(self._format_cpf_field)
        self.ed_phone = QLineEdit()
        self.ed_birth = QDateEdit()
        self.ed_birth.setObjectName("ModernDateEdit")
        self.ed_birth.setCalendarPopup(False)
        self.ed_birth.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        self.ed_birth.setDisplayFormat("dd/MM/yyyy")
        self.ed_birth.setMinimumDate(QDate(1900, 1, 1))
        self.ed_birth.setMaximumDate(QDate.currentDate())
        self.ed_birth.setSpecialValueText("dd/mm/aaaa")
        self.ed_birth.setDate(self.ed_birth.minimumDate())
        btn_birth = QToolButton()
        btn_birth.setObjectName("CalendarHintButton")
        btn_birth.setIcon(make_calendar_icon())
        btn_birth.setIconSize(QSize(14, 14))
        btn_birth.setToolTip("Abrir calendário")
        btn_birth.clicked.connect(self._pick_birth_date)
        birth_field = QFrame()
        birth_field.setObjectName("DateFieldWrap")
        birth_layout = QHBoxLayout(birth_field)
        birth_layout.setContentsMargins(0, 0, 0, 0)
        birth_layout.setSpacing(0)
        birth_layout.addWidget(self.ed_birth, 1)
        birth_layout.addWidget(btn_birth)
        self.ed_email = QLineEdit()
        self.ed_street = QLineEdit()
        self.ed_cep = QLineEdit()
        self.ed_nb = QLineEdit()
        self.ed_city = QLineEdit()

        btn_cep = QPushButton("Buscar CEP")
        btn_cep.clicked.connect(self.lookup_cep)

        form.addRow("Nome", self.ed_name)
        form.addRow("CPF", self.ed_cpf)
        form.addRow("Telefone", self.ed_phone)
        form.addRow("Nascimento", birth_field)
        form.addRow("Email", self.ed_email)
        form.addRow("Rua", self.ed_street)
        row_cep = QHBoxLayout()
        row_cep.addWidget(self.ed_cep)
        row_cep.addWidget(btn_cep)
        wrap = QWidget()
        wrap.setLayout(row_cep)
        form.addRow("CEP", wrap)
        form.addRow("Bairro", self.ed_nb)
        form.addRow("Cidade", self.ed_city)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.save)
        buttons.rejected.connect(self.reject)
        form.addRow(buttons)

    def lookup_cep(self) -> None:
        cep = self.ed_cep.text().strip().replace("-", "")
        if len(cep) != 8:
            QMessageBox.warning(self, "CEP", "CEP invalido.")
            return
        try:
            r = requests.get(f"https://viacep.com.br/ws/{cep}/json/", timeout=6)
            data = r.json()
            if data.get("erro"):
                raise ValueError("CEP nao encontrado")
            self.ed_street.setText(data.get("logradouro", ""))
            self.ed_nb.setText(data.get("bairro", ""))
            self.ed_city.setText(data.get("localidade", ""))
        except Exception as exc:
            QMessageBox.warning(self, "CEP", f"Falha ao consultar CEP: {exc}")

    def _format_cpf_field(self, text: str) -> None:
        self.ed_cpf.setText(_format_cpf(text))

    def _pick_birth_date(self) -> None:
        current = self.ed_birth.date()
        if current == self.ed_birth.minimumDate():
            current = QDate(2000, 1, 1)
        selected = pick_date_dialog(self, current, "Data de Nascimento")
        if selected is not None:
            self.ed_birth.setDate(min(selected, QDate.currentDate()))

    def _load(self) -> None:
        row = self.db.fetch_one("SELECT * FROM clients WHERE id = ?", (self.client_id,))
        if not row:
            return
        self.ed_name.setText(row["name"] or "")
        self.ed_cpf.setText(_format_cpf(row["cpf"] or ""))
        self.ed_phone.setText(row["phone"] or "")
        birth = QDate.fromString(row["birth_date"] or "", "yyyy-MM-dd")
        if birth.isValid() and birth >= self.ed_birth.minimumDate():
            self.ed_birth.setDate(birth)
        self.ed_email.setText(row["email"] or "")
        self.ed_street.setText(row["street"] or "")
        self.ed_cep.setText(row["cep"] or "")
        self.ed_nb.setText(row["neighborhood"] or "")
        self.ed_city.setText(row["city"] or "")

    def save(self) -> None:
        if not self.ed_name.text().strip():
            QMessageBox.warning(self, "Cliente", "Nome obrigatorio.")
            return
        cpf_digits = "".join(ch for ch in self.ed_cpf.text() if ch.isdigit())
        if cpf_digits and not _is_valid_cpf(cpf_digits):
            QMessageBox.warning(self, "Cliente", "CPF inválido. Verifique os números digitados.")
            return
        if cpf_digits:
            duplicate = self.db.fetch_one(
                "SELECT name FROM clients WHERE cpf = ? AND id != ?", (cpf_digits, self.client_id or 0)
            )
            if duplicate:
                QMessageBox.warning(self, "Cliente", f"Este CPF já está cadastrado para '{duplicate['name']}'.")
                return
        birth = (
            "" if self.ed_birth.date() == self.ed_birth.minimumDate() else self.ed_birth.date().toString("yyyy-MM-dd")
        )
        params = (
            self.ed_name.text().strip(),
            cpf_digits,
            self.ed_phone.text().strip(),
            birth,
            self.ed_email.text().strip(),
            self.ed_street.text().strip(),
            self.ed_cep.text().strip(),
            self.ed_nb.text().strip(),
            self.ed_city.text().strip(),
        )
        if self.client_id:
            self.db.execute(
                """
                UPDATE clients SET
                    name=?, cpf=?, phone=?, birth_date=?, email=?, street=?, cep=?, neighborhood=?, city=?
                WHERE id=?
                """,
                params + (self.client_id,),
            )
        else:
            self.db.execute(
                """
                INSERT INTO clients(name, cpf, phone, birth_date, email, street, cep, neighborhood, city, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                params + (datetime.now().isoformat(timespec="seconds"),),
            )
        self.accept()


def _format_cpf(value: str) -> str:
    digits = "".join(ch for ch in value if ch.isdigit())[:11]
    if len(digits) <= 3:
        return digits
    if len(digits) <= 6:
        return f"{digits[:3]}.{digits[3:]}"
    if len(digits) <= 9:
        return f"{digits[:3]}.{digits[3:6]}.{digits[6:]}"
    return f"{digits[:3]}.{digits[3:6]}.{digits[6:9]}-{digits[9:]}"


def _is_valid_cpf(digits: str) -> bool:
    if len(digits) != 11 or digits == digits[0] * 11:
        return False
    for length in (9, 10):
        total = sum(int(digits[i]) * (length + 1 - i) for i in range(length))
        check = (total * 10) % 11 % 10
        if check != int(digits[length]):
            return False
    return True


class SuppliersPage(BasePage):
    def __init__(self, db: Database) -> None:
        super().__init__()
        self.setObjectName("ManagementPage")
        self.db = db
        self._supplier_rows = []
        self._build()
        self.refresh()

    def _build(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(14)

        header = QHBoxLayout()
        heading = QVBoxLayout()
        heading.setSpacing(3)
        title = QLabel("Fornecedores")
        title.setObjectName("SuppliersPageTitle")
        subtitle = QLabel("Gerencie seus fornecedores, contatos e produtos vinculados.")
        subtitle.setObjectName("PageSubtitle")
        heading.addWidget(title)
        heading.addWidget(subtitle)
        header.addLayout(heading, 1)

        self.btn_table_view = QPushButton("Tabela")
        self.btn_table_view.setObjectName("SupplierViewToggle")
        self.btn_table_view.setCheckable(True)
        self.btn_cards_view = QPushButton("Cards")
        self.btn_cards_view.setObjectName("SupplierViewToggle")
        self.btn_cards_view.setCheckable(True)
        self.btn_table_view.clicked.connect(lambda: self._set_supplier_view(0))
        self.btn_cards_view.clicked.connect(lambda: self._set_supplier_view(1))
        view_switch = QFrame()
        view_switch.setObjectName("SupplierViewSwitch")
        switch_layout = QHBoxLayout(view_switch)
        switch_layout.setContentsMargins(3, 3, 3, 3)
        switch_layout.setSpacing(2)
        switch_layout.addWidget(self.btn_table_view)
        switch_layout.addWidget(self.btn_cards_view)
        header.addWidget(view_switch)

        btn_add = QPushButton("＋  Novo Fornecedor")
        btn_add.setObjectName("SupplierNewButton")
        btn_add.clicked.connect(self.add_item)
        header.addWidget(btn_add)
        root.addLayout(header)

        metrics = QHBoxLayout()
        metrics.setSpacing(14)
        self.metric_total = self._supplier_metric("0", "Total de Fornecedores", "total")
        self.metric_linked = self._supplier_metric("0", "Com produtos vinculados", "linked")
        self.metric_unlinked = self._supplier_metric("0", "Sem produtos vinculados", "unlinked")
        metrics.addWidget(self.metric_total, 1)
        metrics.addWidget(self.metric_linked, 1)
        metrics.addWidget(self.metric_unlinked, 1)
        root.addLayout(metrics)

        listing = QFrame()
        listing.setObjectName("SuppliersListing")
        listing_layout = QVBoxLayout(listing)
        listing_layout.setContentsMargins(0, 0, 0, 0)
        listing_layout.setSpacing(0)

        top_wrap = QFrame()
        top_wrap.setObjectName("SuppliersToolbar")
        top = QHBoxLayout(top_wrap)
        top.setContentsMargins(18, 12, 18, 12)
        top.setSpacing(8)
        self.search = QLineEdit()
        self.search.setObjectName("SupplierSearchInput")
        self.search.setClearButtonEnabled(True)
        self.search.setPlaceholderText("Buscar fornecedor...")
        self.search.textChanged.connect(self.refresh)
        self.search.setMaximumWidth(360)
        top.addWidget(self.search)
        top.addStretch(1)
        self.supplier_count_label = QLabel("0 fornecedores")
        self.supplier_count_label.setObjectName("SupplierCountLabel")
        top.addWidget(self.supplier_count_label)
        listing_layout.addWidget(top_wrap)

        self.supplier_views = QStackedWidget()
        self.table = QTableWidget(0, 6)
        self.table.setObjectName("SuppliersTable")
        self.table.setHorizontalHeaderLabels(["FORNECEDOR", "CNPJ", "TELEFONE", "E-MAIL", "PRODUTOS", "AÇÕES"])
        apply_table_preset(self.table)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.itemDoubleClicked.connect(lambda item: self._run_row_action(item.row(), "edit"))
        self.table.verticalHeader().setDefaultSectionSize(54)
        self.table.setColumnWidth(1, 140)
        self.table.setColumnWidth(2, 140)
        self.table.setColumnWidth(4, 100)
        self.table.setColumnWidth(5, 132)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setDefaultAlignment(Qt.AlignmentFlag.AlignCenter)
        self.supplier_views.addWidget(self.table)

        self.cards_scroll = QScrollArea()
        self.cards_scroll.setObjectName("SupplierCardsScroll")
        self.cards_scroll.setWidgetResizable(True)
        self.cards_scroll.setFrameShape(QFrame.Shape.NoFrame)
        cards_content = QWidget()
        self.cards_grid = QGridLayout(cards_content)
        self.cards_grid.setContentsMargins(18, 18, 18, 18)
        self.cards_grid.setHorizontalSpacing(14)
        self.cards_grid.setVerticalSpacing(14)
        self.cards_grid.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        for column in range(4):
            self.cards_grid.setColumnStretch(column, 1)
        self.cards_scroll.setWidget(cards_content)
        self.supplier_views.addWidget(self.cards_scroll)
        listing_layout.addWidget(self.supplier_views, 1)
        root.addWidget(listing, 1)
        self._set_supplier_view(1)

    def _supplier_metric(self, value: str, caption_text: str, kind: str) -> QFrame:
        card = QFrame()
        card.setObjectName("SupplierMetricCard")
        card.setProperty("metric", kind)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(2)
        value_label = QLabel(value)
        value_label.setObjectName("SupplierMetricValue")
        value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        caption = QLabel(caption_text)
        caption.setObjectName("SupplierMetricCaption")
        caption.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(value_label)
        layout.addWidget(caption)
        card.value_label = value_label
        return card

    def _set_supplier_view(self, index: int) -> None:
        self.supplier_views.setCurrentIndex(index)
        self.btn_table_view.setChecked(index == 0)
        self.btn_cards_view.setChecked(index == 1)

    def refresh(self) -> None:
        term = f"%{self.search.text().strip()}%"
        summary = self.db.fetch_one(
            """
            SELECT COUNT(*) AS total,
                   COALESCE(SUM(CASE WHEN EXISTS(SELECT 1 FROM products p WHERE p.supplier_id = s.id AND p.active = 1) THEN 1 ELSE 0 END), 0) AS linked
            FROM suppliers s
            """
        )
        self.metric_total.value_label.setText(str(int(summary["total"] or 0)))
        self.metric_linked.value_label.setText(str(int(summary["linked"] or 0)))
        self.metric_unlinked.value_label.setText(str(int(summary["total"] or 0) - int(summary["linked"] or 0)))

        rows = self.db.fetch_all(
            """
            SELECT s.id, s.fantasy_name, COALESCE(s.cnpj,'') AS cnpj,
                   COALESCE(s.address,'') AS address, COALESCE(s.email,'') AS email,
                   COALESCE(s.phone,'') AS phone, COUNT(p.id) AS product_count
            FROM suppliers s
            LEFT JOIN products p ON p.supplier_id = s.id AND p.active = 1
            WHERE s.fantasy_name LIKE ? OR COALESCE(s.cnpj,'') LIKE ?
               OR COALESCE(s.phone,'') LIKE ? OR COALESCE(s.email,'') LIKE ?
               OR COALESCE(s.address,'') LIKE ?
            GROUP BY s.id, s.fantasy_name, s.cnpj, s.address, s.email, s.phone
            ORDER BY s.fantasy_name
            """,
            (term, term, term, term, term),
        )
        self._supplier_rows = rows
        self.supplier_count_label.setText(f"{len(rows)} fornecedor" + ("es" if len(rows) != 1 else ""))
        fill_table(self.table, [["", r["cnpj"] or "—", r["phone"] or "—", r["email"] or "—", int(r["product_count"] or 0), ""] for r in rows])
        for row_index, supplier in enumerate(rows):
            name = QLabel(str(supplier["fantasy_name"]))
            name.setObjectName("SupplierTableName")
            name.setContentsMargins(12, 0, 0, 0)
            self.table.setCellWidget(row_index, 0, name)
            for column in (1, 2, 4):
                item = self.table.item(row_index, column)
                if item is not None:
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            actions = QWidget()
            actions.setObjectName("SupplierRowActions")
            actions_layout = QHBoxLayout(actions)
            actions_layout.setContentsMargins(2, 2, 2, 2)
            actions_layout.setSpacing(5)
            actions_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            edit_button = QPushButton("Editar")
            edit_button.setObjectName("SupplierEditButton")
            edit_button.setFixedSize(48, 28)
            edit_button.clicked.connect(lambda _checked=False, row=row_index: self._run_row_action(row, "edit"))
            delete_button = QPushButton("Excluir")
            delete_button.setObjectName("SupplierDeleteButton")
            delete_button.setFixedSize(52, 28)
            delete_button.clicked.connect(lambda _checked=False, row=row_index: self._run_row_action(row, "delete"))
            actions_layout.addWidget(edit_button)
            actions_layout.addWidget(delete_button)
            self.table.setCellWidget(row_index, 5, actions)
        self.table.clearSelection()
        self.table.setCurrentCell(-1, -1)
        self._refresh_supplier_cards(rows)

    def _refresh_supplier_cards(self, rows) -> None:
        while self.cards_grid.count():
            item = self.cards_grid.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        for row_index, supplier in enumerate(rows):
            card = QFrame()
            card.setObjectName("SupplierProfileCard")
            card.setMinimumHeight(226)
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(16, 15, 16, 13)
            card_layout.setSpacing(9)

            identity = QHBoxLayout()
            identity.setSpacing(11)
            supplier_name = str(supplier["fantasy_name"] or "?").strip()
            initials = "".join(part[0] for part in supplier_name.split()[:2]).upper() or "?"
            avatar = QLabel(initials)
            avatar.setObjectName("SupplierAvatar")
            avatar.setProperty("avatarIndex", row_index % 5)
            avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
            avatar.setFixedSize(42, 42)
            name = QLabel(supplier_name)
            name.setObjectName("SupplierCardName")
            name.setWordWrap(True)
            identity.addWidget(avatar)
            identity.addWidget(name, 1)
            card_layout.addLayout(identity)

            contact = QVBoxLayout()
            contact.setSpacing(5)
            for marker, value, tooltip in (
                ("C", supplier["cnpj"] or "CNPJ não informado", "CNPJ"),
                ("T", supplier["phone"] or "Telefone não informado", "Telefone"),
                ("@", supplier["email"] or "E-mail não informado", "E-mail"),
                ("L", supplier["address"] or "Endereço não informado", "Endereço"),
            ):
                contact_row = QHBoxLayout()
                contact_row.setSpacing(8)
                marker_label = QLabel(marker)
                marker_label.setObjectName("SupplierContactMarker")
                marker_label.setToolTip(tooltip)
                marker_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                marker_label.setFixedSize(18, 18)
                value_label = QLabel(str(value))
                value_label.setObjectName("SupplierContactValue")
                value_label.setToolTip(str(value))
                value_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
                value_label.setWordWrap(False)
                contact_row.addWidget(marker_label)
                contact_row.addWidget(value_label, 1)
                contact.addLayout(contact_row)
            card_layout.addLayout(contact)

            divider = QFrame()
            divider.setObjectName("SupplierCardDivider")
            card_layout.addWidget(divider)

            footer = QHBoxLayout()
            product_count = int(supplier["product_count"] or 0)
            linked_label = QLabel(f"{product_count} produto" + ("s" if product_count != 1 else "") + " vinculado" + ("s" if product_count != 1 else ""))
            linked_label.setObjectName("SupplierLinkedCount")
            footer.addWidget(linked_label, 1)
            edit_button = QPushButton("Editar")
            edit_button.setObjectName("SupplierEditButton")
            edit_button.setFixedSize(48, 28)
            edit_button.clicked.connect(lambda _checked=False, row=row_index: self._run_row_action(row, "edit"))
            delete_button = QPushButton("Excluir")
            delete_button.setObjectName("SupplierDeleteButton")
            delete_button.setFixedSize(52, 28)
            delete_button.clicked.connect(lambda _checked=False, row=row_index: self._run_row_action(row, "delete"))
            footer.addWidget(edit_button)
            footer.addWidget(delete_button)
            card_layout.addLayout(footer)
            self.cards_grid.addWidget(card, 0, 0)
        self._reflow_supplier_cards()

    def _reflow_supplier_cards(self) -> None:
        if not hasattr(self, "cards_grid"):
            return
        available_width = max(1, self.cards_scroll.viewport().width())
        spacing = self.cards_grid.horizontalSpacing()
        columns = max(1, min(4, (available_width + spacing) // (250 + spacing)))

        cards = []
        while self.cards_grid.count():
            item = self.cards_grid.takeAt(0)
            if item.widget() is not None:
                cards.append(item.widget())
        for column in range(4):
            self.cards_grid.setColumnStretch(column, 1 if column < columns else 0)
        for index, card in enumerate(cards):
            self.cards_grid.addWidget(card, index // columns, index % columns)

    def resizeEvent(self, event) -> None:  # type: ignore[override]
        super().resizeEvent(event)
        self._reflow_supplier_cards()

    def _run_row_action(self, row: int, action: str) -> None:
        self.table.setCurrentCell(row, 0)
        if action == "edit":
            self.edit_item()
        else:
            self.delete_item()

    def add_item(self) -> None:
        dlg = SupplierDialog(self.db)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self.refresh()

    def edit_item(self) -> None:
        row = self.table.currentRow()
        if row < 0 or row >= len(self._supplier_rows):
            return
        dlg = SupplierDialog(self.db, int(self._supplier_rows[row]["id"]))
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self.refresh()

    def delete_item(self) -> None:
        row = self.table.currentRow()
        if row < 0 or row >= len(self._supplier_rows):
            return
        self.db.execute("DELETE FROM suppliers WHERE id = ?", (int(self._supplier_rows[row]["id"]),))
        self.refresh()


class SupplierDialog(QDialog):
    def __init__(self, db: Database, supplier_id: int | None = None) -> None:
        super().__init__()
        self.db = db
        self.supplier_id = supplier_id
        self.setWindowTitle("Fornecedor")
        self._build()
        if supplier_id:
            self._load()

    def _build(self) -> None:
        form = QFormLayout(self)
        self.ed_name = QLineEdit()
        self.ed_cnpj = QLineEdit()
        self.ed_address = QLineEdit()
        self.ed_email = QLineEdit()
        self.ed_phone = QLineEdit()
        form.addRow("Nome Fantasia", self.ed_name)
        form.addRow("CNPJ", self.ed_cnpj)
        form.addRow("Endereco", self.ed_address)
        form.addRow("Email", self.ed_email)
        form.addRow("Telefone", self.ed_phone)
        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        btns.accepted.connect(self.save)
        btns.rejected.connect(self.reject)
        form.addRow(btns)

    def _load(self) -> None:
        r = self.db.fetch_one("SELECT * FROM suppliers WHERE id = ?", (self.supplier_id,))
        if not r:
            return
        self.ed_name.setText(r["fantasy_name"] or "")
        self.ed_cnpj.setText(r["cnpj"] or "")
        self.ed_address.setText(r["address"] or "")
        self.ed_email.setText(r["email"] or "")
        self.ed_phone.setText(r["phone"] or "")

    def save(self) -> None:
        if not self.ed_name.text().strip():
            QMessageBox.warning(self, "Fornecedor", "Nome fantasia obrigatorio.")
            return
        p = (
            self.ed_name.text().strip(),
            self.ed_cnpj.text().strip(),
            self.ed_address.text().strip(),
            self.ed_email.text().strip(),
            self.ed_phone.text().strip(),
        )
        if self.supplier_id:
            self.db.execute(
                "UPDATE suppliers SET fantasy_name=?, cnpj=?, address=?, email=?, phone=? WHERE id=?",
                p + (self.supplier_id,),
            )
        else:
            self.db.execute(
                "INSERT INTO suppliers(fantasy_name, cnpj, address, email, phone, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                p + (datetime.now().isoformat(timespec="seconds"),),
            )
        self.accept()


class WhatsappPage(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("ManagementPage")
        self._build()

    def _build(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        container = QFrame()
        container.setObjectName("WhatsAppOfferCard")
        container.setMaximumWidth(700)
        layout_c = QVBoxLayout(container)
        layout_c.setContentsMargins(30, 30, 30, 30)
        layout_c.setSpacing(16)

        lbl_whats = QLabel("Integração Inteligente com WhatsApp Business")
        lbl_whats.setObjectName("WhatsAppTitle")
        lbl_whats.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout_c.addWidget(lbl_whats)

        lbl_corpo = QLabel(
            "Transforme conversas em vendas automaticas.\n\n"
            "O modulo de Integracao Inteligente permite que o sistema envie cupons de aniversario automaticos, "
            "lembretes automaticos de cobranca e comprovantes de venda direto no celular do cliente.\n\n"
            "- Status: Recurso Premium Desativado\n"
            "- Beneficio: Economia de tempo e fidelizacao de clientes recorrentes em ate 35%."
        )
        lbl_corpo.setWordWrap(True)
        lbl_corpo.setObjectName("WhatsAppDescription")
        layout_c.addWidget(lbl_corpo)

        div = QFrame()
        div.setObjectName("WhatsAppDivider")
        layout_c.addWidget(div)

        lbl_venda = QLabel(
            "Para desbloquear essa automacao e impulsionar suas vendas, entre em contato com o desenvolvedor:"
        )
        lbl_venda.setWordWrap(True)
        lbl_venda.setObjectName("WhatsAppCallout")
        layout_c.addWidget(lbl_venda)

        lbl_dev = QLabel("Desenvolvedor: Renato S. Fernandes\nContato Comercial: (11) 95699-7213")
        lbl_dev.setObjectName("WhatsAppContact")
        layout_c.addWidget(lbl_dev)

        layout.addWidget(container)


class CashFlowPage(BasePage):
    def __init__(self, db: Database) -> None:
        super().__init__()
        self.setObjectName("ManagementPage")
        self.db = db
        self._build()
        self.refresh()

    def _build(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(12)

        header = QHBoxLayout()
        heading = QVBoxLayout()
        heading.setSpacing(3)
        title = QLabel("Fluxo de Caixa / Lucro")
        title.setObjectName("CashFlowPageTitle")
        subtitle = QLabel("Acompanhe entradas, saídas e o lucro líquido do seu negócio.")
        subtitle.setObjectName("PageSubtitle")
        heading.addWidget(title)
        heading.addWidget(subtitle)
        header.addLayout(heading, 1)
        add_button = QPushButton("＋  Lançamento")
        add_button.setObjectName("CashFlowAddButton")
        add_button.clicked.connect(self.add_entry)
        header.addWidget(add_button)
        root.addLayout(header)

        filters_frame = QFrame()
        filters_frame.setObjectName("CashFlowFilters")
        filters = QHBoxLayout(filters_frame)
        filters.setContentsMargins(12, 8, 12, 8)
        filters.setSpacing(8)
        self.start = QDateEdit()
        self.start.setObjectName("ModernDateEdit")
        self.start.setCalendarPopup(False)
        self.start.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        self.end = QDateEdit()
        self.end.setObjectName("ModernDateEdit")
        self.end.setCalendarPopup(False)
        self.end.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        today = QDate.currentDate()
        self.start.setDate(today.addDays(-(today.day() - 1)))
        self.end.setDate(today)

        btn_start_calendar = QToolButton()
        btn_start_calendar.setObjectName("CalendarHintButton")
        btn_start_calendar.setIcon(make_calendar_icon())
        btn_start_calendar.setIconSize(QSize(14, 14))
        btn_start_calendar.setToolTip("Abrir calendário da data inicial")
        btn_start_calendar.clicked.connect(self._show_start_calendar)
        btn_end_calendar = QToolButton()
        btn_end_calendar.setObjectName("CalendarHintButton")
        btn_end_calendar.setIcon(make_calendar_icon())
        btn_end_calendar.setIconSize(QSize(14, 14))
        btn_end_calendar.setToolTip("Abrir calendário da data final")
        btn_end_calendar.clicked.connect(self._show_end_calendar)

        start_field = QFrame()
        start_field.setObjectName("DateFieldWrap")
        start_layout = QHBoxLayout(start_field)
        start_layout.setContentsMargins(0, 0, 0, 0)
        start_layout.setSpacing(0)
        start_layout.addWidget(self.start)
        start_layout.addWidget(btn_start_calendar)
        end_field = QFrame()
        end_field.setObjectName("DateFieldWrap")
        end_layout = QHBoxLayout(end_field)
        end_layout.setContentsMargins(0, 0, 0, 0)
        end_layout.setSpacing(0)
        end_layout.addWidget(self.end)
        end_layout.addWidget(btn_end_calendar)

        btn_today = QPushButton("Hoje")
        btn_today.setObjectName("GhostButton")
        btn_today.clicked.connect(self._set_range_today)
        btn_week = QPushButton("7 dias")
        btn_week.setObjectName("GhostButton")
        btn_week.clicked.connect(self._set_range_week)
        btn_month = QPushButton("Este mês")
        btn_month.setObjectName("GhostButton")
        btn_month.clicked.connect(self._set_current_month)
        btn_filter = QPushButton("Filtrar")
        btn_filter.clicked.connect(self.refresh)

        filters.addWidget(QLabel("Início"))
        filters.addWidget(start_field)
        filters.addWidget(QLabel("Fim"))
        filters.addWidget(end_field)
        filters.addSpacing(8)
        filters.addWidget(btn_today)
        filters.addWidget(btn_week)
        filters.addWidget(btn_month)
        filters.addStretch(1)
        filters.addWidget(btn_filter)
        root.addWidget(filters_frame)

        metrics = QHBoxLayout()
        metrics.setSpacing(12)
        self.lbl_entry = self._metric_card("TOTAL ENTRADAS", "R$ 0,00", "entry")
        self.lbl_outgoing = self._metric_card("TOTAL SAÍDAS", "R$ 0,00", "outgoing")
        self.lbl_profit = self._metric_card("LUCRO LÍQUIDO", "R$ 0,00", "profit")
        metrics.addWidget(self.lbl_entry, 1)
        metrics.addWidget(self.lbl_outgoing, 1)
        metrics.addWidget(self.lbl_profit, 1)
        root.addLayout(metrics)

        chart_row = QHBoxLayout()
        chart_row.setSpacing(12)
        self.flow_chart_layout = self._chart_card(chart_row, "Evolução do Fluxo")
        self.profit_chart_layout = self._chart_card(chart_row, "Lucro por Mês")
        root.addLayout(chart_row)

        history = QFrame()
        history.setObjectName("CashFlowHistory")
        history_layout = QVBoxLayout(history)
        history_layout.setContentsMargins(0, 0, 0, 0)
        history_layout.setSpacing(0)
        history_title = QLabel("Lançamentos")
        history_title.setObjectName("CashFlowSectionTitle")
        history_title.setContentsMargins(16, 12, 16, 10)
        history_layout.addWidget(history_title)
        self.table = QTableWidget(0, 5)
        self.table.setObjectName("CashFlowTable")
        self.table.setHorizontalHeaderLabels(["DATA", "DESCRIÇÃO", "CATEGORIA", "TIPO", "VALOR"])
        apply_table_preset(self.table)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.verticalHeader().setDefaultSectionSize(38)
        self.table.setColumnWidth(0, 120)
        self.table.setColumnWidth(2, 150)
        self.table.setColumnWidth(3, 110)
        self.table.setColumnWidth(4, 140)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        history_layout.addWidget(self.table)
        root.addWidget(history, 1)

    def showEvent(self, event) -> None:  # type: ignore[override]
        super().showEvent(event)
        self.refresh()

    def _metric_card(self, caption: str, value: str, kind: str) -> QFrame:
        card = QFrame()
        card.setObjectName("CashFlowMetricCard")
        card.setProperty("metric", kind)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(18, 12, 18, 12)
        layout.setSpacing(3)
        caption_label = QLabel(caption)
        caption_label.setObjectName("CashFlowMetricCaption")
        value_label = QLabel(value)
        value_label.setObjectName("CashFlowMetricValue")
        layout.addWidget(caption_label)
        layout.addWidget(value_label)
        card.value_label = value_label
        return card

    def _chart_card(self, row: QHBoxLayout, title: str) -> QVBoxLayout:
        card = QFrame()
        card.setObjectName("CashFlowChartCard")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(14, 12, 14, 10)
        layout.setSpacing(4)
        heading = QLabel(title)
        heading.setObjectName("CashFlowChartTitle")
        layout.addWidget(heading)
        host = QWidget()
        host.setMinimumHeight(170)
        chart_layout = QVBoxLayout(host)
        chart_layout.setContentsMargins(0, 0, 0, 0)
        host.setMinimumHeight(220)
        layout.addWidget(host, 1)
        row.addWidget(card, 1)
        return chart_layout

    def _set_current_month(self) -> None:
        today = QDate.currentDate()
        self.start.setDate(today.addDays(-(today.day() - 1)))
        self.end.setDate(today)

    def _set_range_today(self) -> None:
        today = QDate.currentDate()
        self.start.setDate(today)
        self.end.setDate(today)
        self.refresh()

    def _set_range_week(self) -> None:
        today = QDate.currentDate()
        self.start.setDate(today.addDays(-6))
        self.end.setDate(today)
        self.refresh()

    def _show_start_calendar(self) -> None:
        selected = self._pick_date(self.start.date(), "Selecionar Data Inicial")
        if selected is not None:
            self.start.setDate(selected)
            self.refresh()

    def _show_end_calendar(self) -> None:
        selected = self._pick_date(self.end.date(), "Selecionar Data Final")
        if selected is not None:
            self.end.setDate(selected)
            self.refresh()

    def _pick_date(self, current: QDate, title: str) -> QDate | None:
        return pick_date_dialog(self, current, title)

    def add_entry(self) -> None:
        dialog = CashFlowEntryDialog(self.db, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.refresh()

    def showEvent(self, event) -> None:  # type: ignore[override]
        super().showEvent(event)
        self.refresh()

    def refresh(self) -> None:
        start_date = self.start.date().toString("yyyy-MM-dd")
        end_date = self.end.date().toString("yyyy-MM-dd")
        rows = self.db.fetch_all(
            """
            SELECT entry_date, type, amount, COALESCE(description,'') AS description,
                   COALESCE(reference_sale_id,'') AS reference_sale_id
            FROM cashflow_entries
            WHERE entry_date BETWEEN ? AND ?
            ORDER BY entry_date DESC, id DESC
            """,
            (start_date, end_date),
        )
        totals = self.db.fetch_one(
            """
            SELECT
                COALESCE(SUM(CASE WHEN type IN ('VENDA','ENTRADA') THEN amount ELSE 0 END), 0) AS incoming,
                COALESCE(SUM(CASE WHEN type = 'SAIDA' THEN amount ELSE 0 END), 0) AS outgoing,
                COALESCE(SUM(CASE WHEN type = 'LUCRO' THEN amount ELSE 0 END), 0)
                  + COALESCE(SUM(CASE WHEN type = 'ENTRADA' THEN amount WHEN type = 'SAIDA' THEN -amount ELSE 0 END), 0) AS profit
            FROM cashflow_entries
            WHERE entry_date BETWEEN ? AND ?
            """,
            (start_date, end_date),
        )
        self.lbl_entry.value_label.setText(fmt_money(totals["incoming"] or 0))
        self.lbl_outgoing.value_label.setText(fmt_money(totals["outgoing"] or 0))
        self.lbl_profit.value_label.setText(fmt_money(totals["profit"] or 0))

        monthly_rows = self.db.fetch_all(
            """
            SELECT substr(entry_date,1,7) AS month,
                   COALESCE(SUM(CASE WHEN type IN ('VENDA','ENTRADA') THEN amount ELSE 0 END), 0) AS incoming,
                   COALESCE(SUM(CASE WHEN type = 'SAIDA' THEN amount ELSE 0 END), 0) AS outgoing,
                   COALESCE(SUM(CASE WHEN type = 'LUCRO' THEN amount ELSE 0 END), 0)
                     + COALESCE(SUM(CASE WHEN type = 'ENTRADA' THEN amount WHEN type = 'SAIDA' THEN -amount ELSE 0 END), 0) AS profit
            FROM cashflow_entries
            WHERE entry_date BETWEEN ? AND ?
            GROUP BY substr(entry_date,1,7)
            ORDER BY month
            """,
            (start_date, end_date),
        )
        self._refresh_charts(monthly_rows)

        table_rows = []
        for row in rows:
            entry_type = str(row["type"] or "")
            description = str(row["description"] or "")
            category = "Vendas" if entry_type in ("VENDA", "LUCRO") else "Outros"
            if description.startswith("[") and "]" in description:
                category, description = description[1:].split("]", 1)
                description = description.strip()
            type_label = "↓ Saída" if entry_type == "SAIDA" else "Lucro" if entry_type == "LUCRO" else "↑ Entrada"
            prefix = "− " if entry_type == "SAIDA" else "+ " if entry_type in ("VENDA", "ENTRADA") else ""
            table_rows.append([fmt_date_br(row["entry_date"]), description, category, type_label, prefix + fmt_money(row["amount"])])
        fill_table(self.table, table_rows)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        for row_index, row in enumerate(rows):
            for column in (0, 2, 3, 4):
                item = self.table.item(row_index, column)
                if item is not None:
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            color = "#ef4444" if row["type"] == "SAIDA" else "#10a889" if row["type"] in ("VENDA", "ENTRADA") else "#635bff"
            for column in (3, 4):
                item = self.table.item(row_index, column)
                if item is not None:
                    item.setForeground(QColor(color))

    def _refresh_charts(self, monthly_rows) -> None:
        for chart_layout in (self.flow_chart_layout, self.profit_chart_layout):
            while chart_layout.count():
                item = chart_layout.takeAt(0)
                widget = item.widget()
                if widget is not None:
                    widget.deleteLater()
        if not QT_CHARTS_AVAILABLE:
            for chart_layout in (self.flow_chart_layout, self.profit_chart_layout):
                message = QLabel("Gráficos QtCharts indisponíveis neste ambiente.")
                message.setAlignment(Qt.AlignmentFlag.AlignCenter)
                message.setObjectName("CashFlowChartEmpty")
                chart_layout.addWidget(message)
            return

        month_labels = [QDate(int(str(row["month"])[:4]), int(str(row["month"])[5:7]), 1).toString("MMM/yy") for row in monthly_rows]
        if not month_labels:
            month_labels = ["Sem dados"]
        flow_rows = monthly_rows or [{"incoming": 0, "outgoing": 0}]
        flow_chart = QChart()
        flow_chart.setTheme(QChart.ChartTheme.ChartThemeLight)
        flow_chart.setBackgroundVisible(False)
        flow_chart.setBackgroundBrush(QColor("#ffffff"))
        flow_chart.setPlotAreaBackgroundBrush(QColor("#ffffff"))
        flow_chart.setPlotAreaBackgroundVisible(True)
        flow_chart.setMargins(QMargins(12, 8, 14, 6))
        flow_chart.setAnimationOptions(QChart.AnimationOption.SeriesAnimations)
        flow_chart.legend().setAlignment(Qt.AlignmentFlag.AlignBottom)
        flow_chart.legend().setLabelColor(QColor("#64748b"))
        flow_chart.legend().setFont(QFont("Segoe UI", 8))
        incoming = QLineSeries()
        incoming.setName("Entradas")
        incoming.setColor(QColor("#10bfa5"))
        outgoing = QLineSeries()
        outgoing.setName("Saídas")
        outgoing.setColor(QColor("#f45b50"))
        for index, row in enumerate(flow_rows):
            incoming.append(index, float(row["incoming"] or 0))
            outgoing.append(index, float(row["outgoing"] or 0))
        flow_chart.addSeries(incoming)
        flow_chart.addSeries(outgoing)
        flow_axis_x = QBarCategoryAxis()
        flow_axis_x.append(month_labels)
        flow_axis_y = QValueAxis()
        flow_axis_y.setLabelFormat("R$ %d")
        max_flow = max((max(float(row["incoming"] or 0), float(row["outgoing"] or 0)) for row in monthly_rows), default=1)
        flow_axis_y.setRange(0, max(1, max_flow * 1.15))
        flow_axis_y.setTickCount(5)
        flow_axis_y.setLabelsFont(QFont("Segoe UI", 8))
        flow_axis_y.setLabelsColor(QColor("#7785a0"))
        flow_axis_y.setGridLineColor(QColor("#e8edf4"))
        flow_axis_x.setLabelsFont(QFont("Segoe UI", 8))
        flow_axis_x.setLabelsColor(QColor("#7785a0"))
        flow_chart.addAxis(flow_axis_x, Qt.AlignmentFlag.AlignBottom)
        flow_chart.addAxis(flow_axis_y, Qt.AlignmentFlag.AlignLeft)
        incoming.attachAxis(flow_axis_x)
        incoming.attachAxis(flow_axis_y)
        outgoing.attachAxis(flow_axis_x)
        outgoing.attachAxis(flow_axis_y)
        flow_view = QChartView(flow_chart)
        flow_view.setObjectName("CashFlowChartView")
        flow_view.setRenderHint(QPainter.RenderHint.Antialiasing)
        flow_view.setMinimumHeight(205)
        flow_view.setStyleSheet("background: #ffffff; border: none;")
        flow_view.setFrameShape(QFrame.Shape.NoFrame)
        self.flow_chart_layout.addWidget(flow_view)

        profit_chart = QChart()
        profit_chart.setTheme(QChart.ChartTheme.ChartThemeLight)
        profit_chart.setBackgroundVisible(False)
        profit_chart.setBackgroundBrush(QColor("#ffffff"))
        profit_chart.setPlotAreaBackgroundBrush(QColor("#ffffff"))
        profit_chart.setPlotAreaBackgroundVisible(True)
        profit_chart.setMargins(QMargins(12, 8, 14, 6))
        profit_chart.setAnimationOptions(QChart.AnimationOption.SeriesAnimations)
        profit_chart.legend().setAlignment(Qt.AlignmentFlag.AlignBottom)
        profit_chart.legend().setLabelColor(QColor("#64748b"))
        profit_chart.legend().setFont(QFont("Segoe UI", 8))
        profit_set = QBarSet("Lucro líquido")
        profit_set.setColor(QColor("#6958e8"))
        for row in monthly_rows:
            profit_set.append(float(row["profit"] or 0))
        if not monthly_rows:
            profit_set.append(0)
        profit_series = QBarSeries()
        profit_series.append(profit_set)
        profit_chart.addSeries(profit_series)
        profit_axis_x = QBarCategoryAxis()
        profit_axis_x.append(month_labels)
        profit_axis_y = QValueAxis()
        profit_axis_y.setLabelFormat("R$ %d")
        min_profit = min((float(row["profit"] or 0) for row in monthly_rows), default=0)
        max_profit = max((float(row["profit"] or 0) for row in monthly_rows), default=1)
        profit_padding = max(abs(max_profit), abs(min_profit), 1) * 0.15
        profit_axis_y.setRange(min(0, min_profit - profit_padding), max(0, max_profit + profit_padding))
        profit_axis_y.setTickCount(5)
        profit_axis_y.setLabelsFont(QFont("Segoe UI", 8))
        profit_axis_y.setLabelsColor(QColor("#7785a0"))
        profit_axis_y.setGridLineColor(QColor("#e8edf4"))
        profit_axis_x.setLabelsFont(QFont("Segoe UI", 8))
        profit_axis_x.setLabelsColor(QColor("#7785a0"))
        profit_chart.addAxis(profit_axis_x, Qt.AlignmentFlag.AlignBottom)
        profit_chart.addAxis(profit_axis_y, Qt.AlignmentFlag.AlignLeft)
        profit_series.attachAxis(profit_axis_x)
        profit_series.attachAxis(profit_axis_y)
        profit_view = QChartView(profit_chart)
        profit_view.setObjectName("CashFlowChartView")
        profit_view.setRenderHint(QPainter.RenderHint.Antialiasing)
        profit_view.setMinimumHeight(205)
        profit_view.setStyleSheet("background: #ffffff; border: none;")
        profit_view.setFrameShape(QFrame.Shape.NoFrame)
        self.profit_chart_layout.addWidget(profit_view)


class CashFlowEntryDialog(QDialog):
    def __init__(self, db: Database, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.db = db
        self.setWindowTitle("Novo lançamento")
        self.setMinimumWidth(420)
        form = QFormLayout(self)
        form.setContentsMargins(20, 18, 20, 16)
        form.setVerticalSpacing(12)
        self.entry_date = QDateEdit()
        self.entry_date.setObjectName("ModernDateEdit")
        self.entry_date.setCalendarPopup(False)
        self.entry_date.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        self.entry_date.setDisplayFormat("dd/MM/yyyy")
        self.entry_date.setDate(QDate.currentDate())
        btn_calendar = QToolButton()
        btn_calendar.setObjectName("CalendarHintButton")
        btn_calendar.setIcon(make_calendar_icon())
        btn_calendar.setIconSize(QSize(14, 14))
        btn_calendar.setToolTip("Abrir calendário")
        btn_calendar.clicked.connect(self._pick_entry_date)
        date_field = QFrame()
        date_field.setObjectName("DateFieldWrap")
        date_layout = QHBoxLayout(date_field)
        date_layout.setContentsMargins(0, 0, 0, 0)
        date_layout.setSpacing(0)
        date_layout.addWidget(self.entry_date, 1)
        date_layout.addWidget(btn_calendar)
        self.entry_type = QComboBox()
        self.entry_type.addItem("Entrada", "ENTRADA")
        self.entry_type.addItem("Saída", "SAIDA")
        self.category = QComboBox()
        self.category.addItems(["Fixa", "Estoque", "Taxas", "Vendas", "Outros"])
        self.description = QLineEdit()
        self.description.setPlaceholderText("Ex.: aluguel, reposição de material")
        self.amount = QDoubleSpinBox()
        self.amount.setRange(0.01, 999999999)
        self.amount.setDecimals(2)
        self.amount.setPrefix("R$ ")
        self.amount.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        form.addRow("Data", date_field)
        form.addRow("Tipo", self.entry_type)
        form.addRow("Categoria", self.category)
        form.addRow("Descrição", self.description)
        form.addRow("Valor", self.amount)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.save)
        buttons.rejected.connect(self.reject)
        form.addRow(buttons)

    def _pick_entry_date(self) -> None:
        selected = pick_date_dialog(self, self.entry_date.date(), "Selecionar Data")
        if selected is not None:
            self.entry_date.setDate(selected)

    def save(self) -> None:
        description = self.description.text().strip()
        if not description:
            QMessageBox.warning(self, "Lançamento", "Informe uma descrição para o lançamento.")
            return
        stored_description = f"[{self.category.currentText()}] {description}"
        self.db.execute(
            """
            INSERT INTO cashflow_entries(entry_date, type, amount, description, reference_sale_id, created_by, created_at)
            VALUES (?, ?, ?, ?, NULL, NULL, ?)
            """,
            (
                self.entry_date.date().toString("yyyy-MM-dd"),
                self.entry_type.currentData(),
                self.amount.value(),
                stored_description,
                datetime.now().isoformat(timespec="seconds"),
            ),
        )
        self.accept()


class SettingsPage(BasePage):
    def __init__(self, db: Database, on_saved: Callable[[], None] | None = None) -> None:
        super().__init__()
        self.setObjectName("ManagementPage")
        self.db = db
        self.on_saved = on_saved
        self._build()
        self.load_all()

    def _build(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(14)

        header = QHBoxLayout()
        header_text = QVBoxLayout()
        header_text.setSpacing(3)
        title = QLabel("Configurações Gerais")
        title.setObjectName("SettingsPageTitle")
        subtitle = QLabel("Personalize o sistema conforme as necessidades da sua empresa.")
        subtitle.setObjectName("PageSubtitle")
        header_text.addWidget(title)
        header_text.addWidget(subtitle)
        header.addLayout(header_text, 1)
        btn_save = QPushButton("Salvar Alterações")
        btn_save.setObjectName("SettingsSaveButton")
        btn_save.clicked.connect(self.save_all)
        header.addWidget(btn_save)
        root.addLayout(header)

        body = QHBoxLayout()
        body.setSpacing(14)

        sidebar = QFrame()
        sidebar.setObjectName("SettingsSidebar")
        sidebar.setFixedWidth(196)
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(8, 8, 8, 8)
        sidebar_layout.setSpacing(4)
        self.settings_menu = QListWidget()
        self.settings_menu.setObjectName("SettingsMenu")
        self.settings_menu.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        for label in ("Empresa", "Impressão", "Backups", "Taxas da Maquininha"):
            self.settings_menu.addItem(QListWidgetItem(label))
        sidebar_layout.addWidget(self.settings_menu)
        body.addWidget(sidebar)

        self.settings_stack = QStackedWidget()
        self.settings_stack.setObjectName("SettingsStack")
        body.addWidget(self.settings_stack, 1)
        root.addLayout(body, 1)

        company_page = self._settings_section("Empresa", "Dados cadastrais e informações de recebimento e backup.")
        company_form = QGridLayout()
        company_form.setHorizontalSpacing(16)
        company_form.setVerticalSpacing(12)
        company_form.setAlignment(Qt.AlignmentFlag.AlignTop)
        company_form.setColumnStretch(0, 1)
        company_form.setColumnStretch(1, 1)
        self.ed_cnpj = QLineEdit()
        self.ed_fantasy = QLineEdit()
        self.ed_legal = QLineEdit()
        self.ed_address = QLineEdit()
        self.ed_phone = QLineEdit()
        self.ed_email = QLineEdit()
        self.ed_pix = QLineEdit()
        self.ed_logo = QLineEdit()
        btn_logo = QPushButton("Selecionar logo da loja")
        btn_logo.clicked.connect(self.pick_logo)
        row_logo = QHBoxLayout()
        row_logo.setContentsMargins(0, 0, 0, 0)
        row_logo.setSpacing(8)
        row_logo.addWidget(self.ed_logo)
        row_logo.addWidget(btn_logo)
        logo_wrap = QWidget()
        logo_wrap.setObjectName("SettingsLogoWrap")
        logo_wrap.setLayout(row_logo)
        company_fields = (
            ("Nome fantasia", self.ed_fantasy, 0, 0, 1, 2),
            ("CNPJ", self.ed_cnpj, 1, 0, 1, 1),
            ("Razão social", self.ed_legal, 1, 1, 1, 1),
            ("E-mail para backup", self.ed_email, 2, 0, 1, 1),
            ("Telefone", self.ed_phone, 2, 1, 1, 1),
            ("Endereço", self.ed_address, 3, 0, 1, 2),
            ("Chave PIX", self.ed_pix, 4, 0, 1, 1),
            ("Logo da loja", logo_wrap, 4, 1, 1, 1),
        )
        for label, widget, row, column, row_span, column_span in company_fields:
            field = self._settings_field(label, widget)
            company_form.addWidget(field, row, column, row_span, column_span)
        company_page["layout"].addLayout(company_form)
        company_page["layout"].addStretch(1)
        self.settings_stack.addWidget(company_page["page"])

        print_page = self._settings_section("Impressão", "Defina o formato e a mensagem exibida nos comprovantes.")
        print_form = QFormLayout()
        print_form.setHorizontalSpacing(18)
        print_form.setVerticalSpacing(14)
        self.cb_paper = QComboBox()
        self.cb_paper.addItems(["80mm", "A4"])
        self.ed_footer = QLineEdit()
        print_form.addRow("Tipo papel", self.cb_paper)
        print_form.addRow("Mensagem curta cupom", self.ed_footer)
        print_page["layout"].addLayout(print_form)
        print_page["layout"].addStretch(1)
        self.settings_stack.addWidget(print_page["page"])

        backup_page = self._settings_section("Backups", "Gere uma cópia local ou teste o envio para o e-mail cadastrado.")
        b_layout = QVBoxLayout()
        b_layout.setSpacing(12)
        btn_make = QPushButton("Gerar backup agora")
        btn_make.setObjectName("SecondaryButton")
        btn_make.clicked.connect(self.generate_backup)
        btn_send = QPushButton("Testar envio de backup")
        btn_send.setObjectName("SecondaryButton")
        btn_send.clicked.connect(self.send_test_backup)
        btn_restore = QPushButton("Restaurar backup")
        btn_restore.setObjectName("SecondaryButton")
        btn_restore.setToolTip("Carrega um arquivo de backup (.db) recebido por e-mail e substitui os dados atuais")
        btn_restore.clicked.connect(self.restore_backup)
        btn_reset = QPushButton("Zerar sistema")
        btn_reset.setObjectName("UserDisableButton")
        btn_reset.setToolTip("Apaga todos os dados e restaura o sistema ao estado inicial de fábrica")
        btn_reset.clicked.connect(self.reset_system)
        backup_actions = QHBoxLayout()
        backup_actions.addWidget(btn_make)
        backup_actions.addWidget(btn_send)
        backup_actions.addWidget(btn_restore)
        backup_actions.addStretch(1)
        b_layout.addLayout(backup_actions)
        b_layout.addSpacing(16)
        reset_hint = QLabel(
            "Zerar sistema: remove clientes, fornecedores, produtos, vendas, fluxo de caixa e usuários, "
            "restaurando o administrador padrão e as configurações iniciais. Um backup é gerado antes."
        )
        reset_hint.setObjectName("SettingsSectionDescription")
        reset_hint.setWordWrap(True)
        b_layout.addWidget(reset_hint)
        reset_actions = QHBoxLayout()
        reset_actions.addWidget(btn_reset)
        reset_actions.addStretch(1)
        b_layout.addLayout(reset_actions)
        b_layout.addStretch(1)
        backup_page["layout"].addLayout(b_layout)
        self.settings_stack.addWidget(backup_page["page"])

        rates_page = self._settings_section("Taxas da Maquininha", "Informe os percentuais cobrados por modalidade de pagamento.")
        rate_form = QFormLayout()
        rate_form.setHorizontalSpacing(18)
        rate_form.setVerticalSpacing(14)
        self.sp_deb = QDoubleSpinBox(); self.sp_deb.setMaximum(100); self.sp_deb.setSuffix(" %")
        self.sp_crv = QDoubleSpinBox(); self.sp_crv.setMaximum(100); self.sp_crv.setSuffix(" %")
        self.sp_crp = QDoubleSpinBox(); self.sp_crp.setMaximum(100); self.sp_crp.setSuffix(" %")
        self.sp_pixm = QDoubleSpinBox(); self.sp_pixm.setMaximum(100); self.sp_pixm.setSuffix(" %")
        for spin in (self.sp_deb, self.sp_crv, self.sp_crp, self.sp_pixm):
            spin.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
            spin.setFixedWidth(220)
        rate_form.addRow("Debito", self.sp_deb)
        rate_form.addRow("Credito a vista", self.sp_crv)
        rate_form.addRow("Credito parcelado ate 6x", self.sp_crp)
        rate_form.addRow("PIX maquininha", self.sp_pixm)
        rates_page["layout"].addLayout(rate_form)
        rates_page["layout"].addStretch(1)
        self.settings_stack.addWidget(rates_page["page"])

        self.settings_menu.currentRowChanged.connect(self.settings_stack.setCurrentIndex)
        self.settings_menu.setCurrentRow(0)

    def _settings_section(self, title: str, description: str) -> dict[str, QWidget | QVBoxLayout]:
        panel = QFrame()
        panel.setObjectName("SettingsPanel")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(22, 20, 22, 22)
        layout.setSpacing(8)
        heading = QLabel(title)
        heading.setObjectName("SettingsSectionTitle")
        detail = QLabel(description)
        detail.setObjectName("SettingsSectionDescription")
        detail.setWordWrap(True)
        layout.addWidget(heading)
        layout.addWidget(detail)
        layout.addSpacing(8)
        return {"page": panel, "layout": layout}

    def _settings_field(self, label: str, widget: QWidget) -> QWidget:
        field = QWidget()
        field.setObjectName("SettingsField")
        layout = QVBoxLayout(field)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)
        caption = QLabel(label)
        caption.setObjectName("SettingsFieldLabel")
        layout.addWidget(caption)
        layout.addWidget(widget)
        return field

    def pick_logo(self) -> None:
        file, _ = QFileDialog.getOpenFileName(self, "Selecionar Logo", "", "Imagens (*.png *.jpg *.jpeg *.webp)")
        if file:
            self.ed_logo.setText(file)

    def load_all(self) -> None:
        company = self.db.fetch_one("SELECT * FROM company_config WHERE id = 1")
        if company:
            self.ed_cnpj.setText(company["cnpj"] or "")
            self.ed_fantasy.setText(company["fantasy_name"] or "")
            self.ed_legal.setText(company["legal_name"] or "")
            self.ed_address.setText(company["address"] or "")
            self.ed_phone.setText(company["phone"] or "")
            self.ed_email.setText(company["email"] or "")
            self.ed_pix.setText(company["pix_key"] or "")
            self.ed_logo.setText(company["logo_path"] or "")

        printer = self.db.fetch_one("SELECT * FROM printer_config WHERE id = 1")
        if printer:
            idx = self.cb_paper.findText(printer["paper_type"])
            if idx >= 0:
                self.cb_paper.setCurrentIndex(idx)
            self.ed_footer.setText(printer["footer_message"] or "")
        rates = self.db.fetch_one("SELECT * FROM machine_rates WHERE id = 1")
        if rates:
            self.sp_deb.setValue(float(rates["debito"]))
            self.sp_crv.setValue(float(rates["credito_avista"]))
            self.sp_crp.setValue(float(rates["credito_parcelado"]))
            self.sp_pixm.setValue(float(rates["pix_maquininha"]))

    def save_all(self) -> None:
        self.db.execute(
            """
            UPDATE company_config
            SET cnpj=?, fantasy_name=?, legal_name=?, address=?, phone=?, email=?, logo_path=?, pix_key=?
            WHERE id = 1
            """,
            (
                self.ed_cnpj.text().strip(),
                self.ed_fantasy.text().strip(),
                self.ed_legal.text().strip(),
                self.ed_address.text().strip(),
                self.ed_phone.text().strip(),
                self.ed_email.text().strip(),
                self.ed_logo.text().strip(),
                self.ed_pix.text().strip(),
            ),
        )
        self.db.execute(
            "UPDATE printer_config SET paper_type=?, footer_message=? WHERE id=1",
            (self.cb_paper.currentText(), self.ed_footer.text().strip()),
        )
        self.db.execute(
            "UPDATE machine_rates SET debito=?, credito_avista=?, credito_parcelado=?, pix_maquininha=? WHERE id=1",
            (self.sp_deb.value(), self.sp_crv.value(), self.sp_crp.value(), self.sp_pixm.value()),
        )
        if self.on_saved:
            self.on_saved()
        QMessageBox.information(self, "Configuracoes", "Dados salvos com sucesso.")

    def generate_backup(self) -> None:
        try:
            file = BackupService().create_backup_file()
        except Exception as exc:
            QMessageBox.warning(self, "Backup", f"N?o foi poss?vel gerar o backup: {exc}")
            return
        QMessageBox.information(self, "Backup", f"Backup gerado em:\n{file}")

    def restore_backup(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Selecionar arquivo de backup", str(Path.home()), "Backup do sistema (*.db);;Todos os arquivos (*)"
        )
        if not path:
            return
        answer = QMessageBox.warning(
            self,
            "Restaurar backup",
            "Os dados atuais (clientes, produtos, vendas, fluxo de caixa, usuários e configurações) serão "
            "SUBSTITUÍDOS pelos dados do arquivo selecionado:\n\n"
            f"{path}\n\nUm backup do estado atual é salvo antes. Deseja continuar?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        try:
            safety = BackupService().restore_backup(path)
            Database(self.db.db_path)
        except Exception as exc:
            QMessageBox.critical(self, "Restaurar backup", f"Não foi possível restaurar o backup.\nMotivo: {exc}")
            return
        QMessageBox.information(
            self,
            "Restaurar backup",
            f"Backup restaurado com sucesso.\nO estado anterior foi salvo em:\n{safety}\n\n"
            "O sistema será fechado. Abra-o novamente para continuar.",
        )
        QApplication.closeAllWindows()
        QApplication.quit()

    def send_test_backup(self) -> None:
        company = self.db.fetch_one("SELECT email FROM company_config WHERE id = 1")
        dest = ((company["email"] if company else "") or "").strip()
        if not dest:
            QMessageBox.warning(self, "Backup", "Cadastre o e-mail da empresa em Empresa e salve antes de testar o envio.")
            return
        backup_file, sent, reason = run_backup_with_progress(self, dest, "Enviando backup")
        if sent:
            QMessageBox.information(self, "Backup", f"Backup enviado com sucesso para {dest}.")
        else:
            show_backup_failure(self, backup_file, reason)

    def reset_system(self) -> None:
        answer = QMessageBox.warning(
            self,
            "Zerar sistema",
            "Esta ação apaga TODOS os clientes, fornecedores, produtos, vendas, lançamentos do fluxo de caixa "
            "e usuários, e restaura as configurações da empresa, impressão e taxas para o padrão.\n\n"
            "O usuário admin (senha admin123) será recriado.\n\nDeseja continuar?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        text, ok = QInputDialog.getText(self, "Confirmação", "Digite ZERAR para confirmar:")
        if not ok or text.strip().upper() != "ZERAR":
            QMessageBox.information(self, "Zerar sistema", "Operação cancelada.")
            return
        try:
            backup_file = BackupService().create_backup_file()
            self.db.reset_to_factory()
        except Exception as exc:
            QMessageBox.critical(self, "Zerar sistema", f"Não foi possível zerar o sistema.\nMotivo: {exc}")
            return
        QMessageBox.information(
            self,
            "Zerar sistema",
            f"Sistema zerado com sucesso.\nBackup anterior salvo em:\n{backup_file}\n\n"
            "O sistema será fechado. Abra-o novamente e entre com admin / admin123.",
        )
        QApplication.closeAllWindows()
        QApplication.quit()


class UsersPage(BasePage):
    def __init__(self, db: Database) -> None:
        super().__init__()
        self.setObjectName("ManagementPage")
        self.db = db
        self._build()
        self.refresh()

    def _build(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(14)
        header = QHBoxLayout()
        heading = QVBoxLayout()
        heading.setSpacing(3)
        title = QLabel("Gerenciar Usuários")
        title.setObjectName("UsersPageTitle")
        subtitle = QLabel("Controle os acessos e permissões da equipe no sistema.")
        subtitle.setObjectName("PageSubtitle")
        heading.addWidget(title)
        heading.addWidget(subtitle)
        header.addLayout(heading, 1)
        add_button = QPushButton("＋  Novo Usuário")
        add_button.setObjectName("UserNewButton")
        add_button.clicked.connect(self.add_user)
        header.addWidget(add_button)
        root.addLayout(header)

        metrics = QHBoxLayout()
        metrics.setSpacing(12)
        self.metric_users = self._user_metric("0", "Total", "total")
        self.metric_active = self._user_metric("0", "Ativos", "active")
        self.metric_inactive = self._user_metric("0", "Inativos", "inactive")
        self.metric_roles = self._user_metric("0", "Perfis", "roles")
        for metric in (self.metric_users, self.metric_active, self.metric_inactive, self.metric_roles):
            metrics.addWidget(metric, 1)
        root.addLayout(metrics)

        users_wrap = QFrame()
        users_wrap.setObjectName("UsersListing")
        users_layout = QVBoxLayout(users_wrap)
        users_layout.setContentsMargins(0, 0, 0, 0)
        users_layout.setSpacing(0)
        listing_header = QHBoxLayout()
        listing_header.setContentsMargins(16, 12, 16, 10)
        listing_title = QLabel("Usuários do Sistema")
        listing_title.setObjectName("UsersSectionTitle")
        listing_header.addWidget(listing_title)
        listing_header.addStretch(1)
        self.users_count_label = QLabel("0 usuários")
        self.users_count_label.setObjectName("UsersCountLabel")
        listing_header.addWidget(self.users_count_label)
        users_layout.addLayout(listing_header)

        search_wrap = QFrame()
        search_wrap.setObjectName("UsersToolbar")
        search_layout = QHBoxLayout(search_wrap)
        search_layout.setContentsMargins(16, 9, 16, 9)
        self.search = QLineEdit()
        self.search.setObjectName("UsersSearchInput")
        self.search.setClearButtonEnabled(True)
        self.search.setPlaceholderText("Buscar por nome, usuário ou perfil...")
        self.search.textChanged.connect(self.refresh)
        self.search.setMaximumWidth(380)
        search_layout.addWidget(self.search)
        search_layout.addStretch(1)
        users_layout.addWidget(search_wrap)

        self.table = QTableWidget(0, 7)
        self.table.setObjectName("UsersTable")
        self.table.setHorizontalHeaderLabels(["ID", "USUÁRIO", "LOGIN", "PERFIL", "CRIADO EM", "STATUS", "AÇÕES"])
        apply_table_preset(self.table)
        self.table.setColumnHidden(0, True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.itemDoubleClicked.connect(lambda item: self._run_user_action(item.row(), "edit"))
        self.table.verticalHeader().setDefaultSectionSize(50)
        self.table.setColumnWidth(2, 170)
        self.table.setColumnWidth(4, 130)
        self.table.setColumnWidth(5, 105)
        self.table.setColumnWidth(6, 116)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        users_layout.addWidget(self.table)
        root.addWidget(users_wrap)

        sales_wrap = QFrame()
        sales_wrap.setObjectName("UsersSalesPanel")
        sales_layout = QVBoxLayout(sales_wrap)
        sales_layout.setContentsMargins(0, 0, 0, 0)
        sales_layout.setSpacing(0)
        sales_header = QHBoxLayout()
        sales_header.setContentsMargins(16, 12, 16, 10)
        sales_title = QLabel("Desempenho de Vendas por Usuário")
        sales_title.setObjectName("UsersSectionTitle")
        sales_header.addWidget(sales_title)
        sales_header.addStretch(1)
        self.filter_user = QComboBox()
        self.filter_user.addItem("Todos", None)
        self.filter_user.currentIndexChanged.connect(self.refresh_graph)
        self.filter_user.setObjectName("UsersSalesFilter")
        self.filter_user.setMinimumWidth(160)
        sales_header.addWidget(QLabel("Usuário:"))
        sales_header.addWidget(self.filter_user)
        sales_layout.addLayout(sales_header)

        self.sales_table = QTableWidget(0, 3)
        self.sales_table.setObjectName("UsersSalesTable")
        self.sales_table.setHorizontalHeaderLabels(["Usuario", "Qtd Vendas", "Total Vendido"])
        apply_table_preset(self.sales_table)
        self.sales_table.verticalHeader().setDefaultSectionSize(36)
        self._configure_sales_table_columns()
        sales_layout.addWidget(self.sales_table)
        root.addWidget(sales_wrap)

    def _user_metric(self, value: str, label: str, kind: str) -> QFrame:
        card = QFrame()
        card.setObjectName("UserMetricCard")
        card.setProperty("metric", kind)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(2)
        value_label = QLabel(value)
        value_label.setObjectName("UserMetricValue")
        value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        caption = QLabel(label)
        caption.setObjectName("UserMetricCaption")
        caption.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(value_label)
        layout.addWidget(caption)
        card.value_label = value_label
        return card

    def _centered_user_cell(self, child: QWidget, object_name: str) -> QWidget:
        wrapper = QWidget()
        wrapper.setObjectName(object_name)
        layout = QHBoxLayout(wrapper)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(child)
        return wrapper

    def _configure_sales_table_columns(self) -> None:
        header = self.sales_table.horizontalHeader()
        header.setStretchLastSection(False)
        for column in range(self.sales_table.columnCount()):
            header.setSectionResizeMode(column, QHeaderView.ResizeMode.ResizeToContents)
        header.setDefaultAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

    def _run_user_action(self, row: int, action: str) -> None:
        self.table.setCurrentCell(row, 0)
        if action == "edit":
            self.edit_user()
        else:
            self.disable_user()

    def refresh(self) -> None:
        term = f"%{self.search.text().strip()}%"
        users = self.db.fetch_all(
            "SELECT id, name, username, role, active, created_at FROM users WHERE name LIKE ? OR username LIKE ? OR role LIKE ? ORDER BY id",
            (term, term, term),
        )
        all_users = self.db.fetch_all("SELECT id, name, username, role, active, created_at FROM users ORDER BY id")
        active_count = sum(1 for user in all_users if int(user["active"] or 0) == 1)
        self.metric_users.value_label.setText(str(len(all_users)))
        self.metric_active.value_label.setText(str(active_count))
        self.metric_inactive.value_label.setText(str(len(all_users) - active_count))
        self.metric_roles.value_label.setText(str(len({str(user["role"]) for user in all_users})))
        self.users_count_label.setText(f"{len(users)} usuário" + ("s" if len(users) != 1 else ""))

        data = []
        for user in users:
            created = fmt_date_br(str(user["created_at"] or "").split("T")[0]) or "—"
            data.append([user["id"], "", user["username"], "", created, "", ""])
        fill_table(self.table, data)
        self.table.setColumnHidden(0, True)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        for row, user in enumerate(users):
            name = str(user["name"] or "?").strip()
            initials = "".join(part[0] for part in name.split()[:2]).upper() or "?"
            identity = QWidget()
            identity.setObjectName("UserIdentity")
            identity_layout = QHBoxLayout(identity)
            identity_layout.setContentsMargins(12, 3, 8, 3)
            identity_layout.setSpacing(10)
            avatar = QLabel(initials)
            avatar.setObjectName("UserAvatar")
            avatar.setProperty("avatarIndex", row % 5)
            avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
            avatar.setFixedSize(34, 34)
            name_label = QLabel(name)
            name_label.setObjectName("UserName")
            identity_layout.addWidget(avatar)
            identity_layout.addWidget(name_label, 1)
            self.table.setCellWidget(row, 1, identity)

            role = str(user["role"] or "")
            role_badge = QLabel({"MASTER": "Master", "OPERADOR": "Operador", "CAIXA": "Caixa"}.get(role, role.title()))
            role_badge.setObjectName("UserRoleBadge")
            role_badge.setProperty("role", role.lower())
            role_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setCellWidget(row, 3, self._centered_user_cell(role_badge, "UserRoleCell"))

            status_badge = QLabel("Ativo" if user["active"] else "Inativo")
            status_badge.setObjectName("UserStatusBadge")
            status_badge.setProperty("active", "true" if user["active"] else "false")
            status_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setCellWidget(row, 5, self._centered_user_cell(status_badge, "UserStatusCell"))

            actions = QWidget()
            actions.setObjectName("UserRowActions")
            action_layout = QHBoxLayout(actions)
            action_layout.setContentsMargins(2, 2, 2, 2)
            action_layout.setSpacing(6)
            action_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            edit_button = QPushButton("Editar")
            edit_button.setObjectName("UserEditButton")
            edit_button.setFixedSize(50, 28)
            edit_button.clicked.connect(lambda _checked=False, selected=row: self._run_user_action(selected, "edit"))
            action_layout.addWidget(edit_button)
            if int(user["active"] or 0) == 1:
                disable_button = QPushButton("Inativar")
                disable_button.setObjectName("UserDisableButton")
                disable_button.setFixedSize(58, 28)
                disable_button.clicked.connect(lambda _checked=False, selected=row: self._run_user_action(selected, "disable"))
                action_layout.addWidget(disable_button)
            self.table.setCellWidget(row, 6, actions)

        self.table.clearSelection()
        self.table.setCurrentCell(-1, -1)
        self.filter_user.blockSignals(True)
        self.filter_user.clear()
        self.filter_user.addItem("Todos", None)
        for u in all_users:
            self.filter_user.addItem(u["name"], u["id"])
        self.filter_user.blockSignals(False)
        self.refresh_graph()

    def refresh_graph(self) -> None:
        user_id = self.filter_user.currentData()
        query = (
            """
            SELECT u.name, COUNT(s.id) qtd, COALESCE(SUM(s.net_total),0) total
            FROM users u
            LEFT JOIN sales s ON s.user_id = u.id AND s.status <> 'CANCELADA'
            {where}
            GROUP BY u.id, u.name
            ORDER BY total DESC
            """
        )
        where = "WHERE u.id = ?" if user_id else ""
        rows = self.db.fetch_all(query.format(where=where), (user_id,) if user_id else ())
        fill_table(self.sales_table, [[r["name"], r["qtd"], fmt_money(r["total"])] for r in rows])
        self._configure_sales_table_columns()

    def add_user(self) -> None:
        dlg = UserDialog(self.db)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self.refresh()

    def edit_user(self) -> None:
        row = self.table.currentRow()
        if row < 0:
            return
        dlg = UserDialog(self.db, int(self.table.item(row, 0).text()))
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self.refresh()

    def disable_user(self) -> None:
        row = self.table.currentRow()
        if row < 0:
            return
        user_id = int(self.table.item(row, 0).text())
        self.db.execute("UPDATE users SET active = 0 WHERE id = ?", (user_id,))
        self.refresh()


class UserDialog(QDialog):
    def __init__(self, db: Database, user_id: int | None = None) -> None:
        super().__init__()
        self.db = db
        self.user_id = user_id
        self.setWindowTitle("Usuario")
        self._build()
        if user_id:
            self._load()

    def _build(self) -> None:
        form = QFormLayout(self)
        self.ed_name = QLineEdit()
        self.ed_user = QLineEdit()
        self.ed_pass = QLineEdit()
        self.ed_pass.setEchoMode(QLineEdit.EchoMode.Password)
        self.cb_role = QComboBox()
        self.cb_role.addItems(["MASTER", "OPERADOR", "CAIXA"])
        form.addRow("Nome", self.ed_name)
        form.addRow("Usuario", self.ed_user)
        form.addRow("Senha", self.ed_pass)
        form.addRow("Perfil", self.cb_role)
        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        btns.accepted.connect(self.save)
        btns.rejected.connect(self.reject)
        form.addRow(btns)

    def _load(self) -> None:
        u = self.db.fetch_one("SELECT * FROM users WHERE id = ?", (self.user_id,))
        if not u:
            return
        self.ed_name.setText(u["name"])
        self.ed_user.setText(u["username"])
        idx = self.cb_role.findText(u["role"])
        if idx >= 0:
            self.cb_role.setCurrentIndex(idx)
        self.ed_pass.setPlaceholderText("Deixe em branco para manter a senha atual")

    def save(self) -> None:
        name = self.ed_name.text().strip()
        username = self.ed_user.text().strip()
        role = self.cb_role.currentText()
        if not name or not username:
            QMessageBox.warning(self, "Usuario", "Nome e usuario obrigatorios.")
            return
        if self.user_id:
            if self.ed_pass.text().strip():
                self.db.execute(
                    "UPDATE users SET name=?, username=?, role=?, password_hash=? WHERE id=?",
                    (name, username, role, hash_password(self.ed_pass.text().strip()), self.user_id),
                )
            else:
                self.db.execute(
                    "UPDATE users SET name=?, username=?, role=? WHERE id=?",
                    (name, username, role, self.user_id),
                )
        else:
            pwd = self.ed_pass.text().strip()
            if not pwd:
                QMessageBox.warning(self, "Usuario", "Senha obrigatoria para novo usuario.")
                return
            self.db.execute(
                """
                INSERT INTO users(name, username, password_hash, role, active, created_at)
                VALUES (?, ?, ?, ?, 1, ?)
                """,
                (name, username, hash_password(pwd), role, datetime.now().isoformat(timespec="seconds")),
            )
        self.accept()


def fill_table(table: QTableWidget, rows: list[list]) -> None:
    apply_table_preset(table)
    table.setRowCount(len(rows))
    table.clearContents()
    for r, row in enumerate(rows):
        for c, value in enumerate(row):
            item = QTableWidgetItem(str(value))
            table.setItem(r, c, item)


def apply_table_preset(table: QTableWidget) -> None:
    table.setAlternatingRowColors(True)
    table.setShowGrid(False)
    table.verticalHeader().setVisible(False)
    table.horizontalHeader().setStretchLastSection(True)
    table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)


def fmt_money(value: float) -> str:
    txt = f"{float(value):,.2f}"
    txt = txt.replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {txt}"


def _resolve_logo_path(db: Database) -> str:
    company = db.fetch_one("SELECT logo_path FROM company_config WHERE id = 1")
    configured_path = str(company["logo_path"] or "").strip() if company else ""
    logo_path = Path(configured_path) if configured_path else DEFAULT_SYSTEM_LOGO
    if not logo_path.is_file() or QPixmap(str(logo_path)).isNull():
        logo_path = DEFAULT_SYSTEM_LOGO
    return str(logo_path)


def _receipt_print_options(db: Database) -> tuple[str, str]:
    logo_path = _resolve_logo_path(db)
    printer = db.fetch_one("SELECT paper_type FROM printer_config WHERE id = 1")
    paper_type = str(printer["paper_type"] or "80mm") if printer else "80mm"
    return logo_path, paper_type


def _receipt_payment_name(method: str) -> str:
    return {
        "DINHEIRO": "Dinheiro",
        "PIX": "PIX",
        "PIX_MAQUININHA": "PIX Maquininha",
        "DEBITO": "Cartão Débito",
        "CREDITO_AVISTA": "Cartão Crédito",
        "CREDITO_PARCELADO": "Crédito Parcelado",
    }.get(str(method), str(method).replace("_", " ").title())


def _show_receipt_preview(
    parent: QWidget,
    db: Database,
    printer_service: PrinterService,
    sale_id: int,
    receipt_text: str,
) -> None:
    logo_path, paper_type = _receipt_print_options(db)
    dialog = QDialog(parent)
    dialog.setObjectName("ReceiptPreviewDialog")
    dialog.setWindowTitle("Cupom não fiscal")
    dialog.setMinimumSize(440, 620)
    layout = QVBoxLayout(dialog)
    layout.setContentsMargins(20, 18, 20, 16)
    layout.setSpacing(12)

    logo_label = QLabel()
    logo_label.setObjectName("ReceiptPreviewLogo")
    logo_pixmap = QPixmap(logo_path)
    if not logo_pixmap.isNull():
        logo_label.setPixmap(logo_pixmap.scaled(220, 100, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(logo_label)

    receipt = QTextEdit()
    receipt.setObjectName("ReceiptPreviewText")
    receipt.setReadOnly(True)
    receipt.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)
    receipt.setFont(QFont("Consolas", 10))
    receipt.setPlainText(receipt_text)
    layout.addWidget(receipt, 1)

    actions = QHBoxLayout()
    actions.addStretch(1)
    close_button = QPushButton("Fechar")
    close_button.setObjectName("SecondaryButton")
    close_button.clicked.connect(dialog.accept)
    print_button = QPushButton("Imprimir cupom")
    print_button.setObjectName("SuccessButton")

    def print_receipt() -> None:
        result = printer_service.print_receipt_text(
            receipt_text,
            logo_path=logo_path,
            paper_type=paper_type,
        )
        if result.ok:
            QMessageBox.information(dialog, "Impressão", result.message)
        else:
            QMessageBox.warning(dialog, "Impressão", result.message)

    print_button.clicked.connect(print_receipt)
    actions.addWidget(close_button)
    actions.addWidget(print_button)
    layout.addLayout(actions)
    dialog.exec()


def _build_receipt_text(db: Database, sale_id: int, preview: dict) -> str:
    company = db.fetch_one("SELECT * FROM company_config WHERE id = 1")
    printer = db.fetch_one("SELECT paper_type, footer_message FROM printer_config WHERE id = 1")
    sale = db.fetch_one(
        """
        SELECT s.created_at, COALESCE(u.name,'') AS seller,
               COALESCE(c.name,'Consumidor Final') AS client,
               COALESCE(c.cpf,'') AS client_cpf
        FROM sales s
        LEFT JOIN users u ON u.id = s.user_id
        LEFT JOIN clients c ON c.id = s.client_id
        WHERE s.id = ?
        """,
        (sale_id,),
    )

    width = 48 if printer and str(printer["paper_type"] or "") == "A4" else 42
    separator = "-" * width
    store_name = (company["fantasy_name"] or company["legal_name"] or "Gestão Inteligente").strip() if company else "Gestão Inteligente"
    address = str(company["address"] or "").strip() if company else ""
    phone = str(company["phone"] or "").strip() if company else ""
    cnpj = str(company["cnpj"] or "").strip() if company else ""
    footer = str(printer["footer_message"] or "").strip() if printer else ""
    created_at = str(sale["created_at"] or datetime.now().isoformat(timespec="seconds")) if sale else datetime.now().isoformat(timespec="seconds")
    try:
        sale_datetime = datetime.fromisoformat(created_at)
    except ValueError:
        sale_datetime = datetime.now()
    seller = str(sale["seller"] or "").strip() if sale else ""
    client = str(sale["client"] or "Consumidor Final").strip() if sale else "Consumidor Final"

    lines = [store_name.upper()[:width].center(width)]
    if cnpj:
        lines.append(f"CNPJ: {cnpj}"[:width])
    if address:
        lines.append(address[:width])
    if phone:
        lines.append(phone[:width])
    lines.extend((separator, "CUPOM NÃO FISCAL".center(width), "DOCUMENTO AUXILIAR DE VENDA".center(width), separator))
    date_label = sale_datetime.strftime("DATA: %d/%m/%Y")
    time_label = sale_datetime.strftime("HORA: %H:%M")
    lines.append(date_label.ljust(max(0, width - len(time_label))) + time_label)
    if seller:
        lines.append(f"VENDEDOR: {seller}"[:width])
    lines.append(f"VENDA: #{sale_id}"[:width])
    lines.append(f"CLIENTE: {client}"[:width])
    client_cpf = _format_cpf(str(sale["client_cpf"] or "")) if sale else ""
    if client_cpf:
        lines.append(f"CPF: {client_cpf}"[:width])
    lines.append(separator)

    code_width = 4 if width >= 48 else 3
    description_width = 18 if width >= 48 else 15
    quantity_width = 4 if width >= 48 else 3
    unit_width = 10 if width >= 48 else 9
    total_width = 8
    header = (
        f"{'CÓD.':<{code_width}} "
        f"{'DESCRIÇÃO':<{description_width}} "
        f"{'QTD.':>{quantity_width}} "
        f"{'VL.UNIT.':>{unit_width}} "
        f"{'VL.TOTAL':>{total_width}}"
    )
    lines.append(header[:width])

    for item in preview.get("items", []):
        quantity_value = float(item.get("qty", 0) or 0)
        quantity = str(int(quantity_value)) if quantity_value.is_integer() else f"{quantity_value:g}"
        unit_price = float(item.get("unit_price", 0) or 0)
        gross_line = round(quantity_value * unit_price, 2)
        unit_text = fmt_money(unit_price).replace("R$ ", "")
        total_text = fmt_money(gross_line).replace("R$ ", "")
        name = str(item.get("name") or "Produto")
        if len(name) > description_width:
            name = name[:max(1, description_width - 3)] + "..."
        code = str(item.get("product_id") or "")[:code_width]
        item_line = (
            f"{code:<{code_width}} "
            f"{name:<{description_width}} "
            f"{quantity:>{quantity_width}} "
            f"{unit_text:>{unit_width}} "
            f"{total_text:>{total_width}}"
        )
        lines.append(item_line[:width])

    lines.append(separator)
    lines.append(f"{'SUBTOTAL':<{width - len(fmt_money(preview['gross_total']))}}{fmt_money(preview['gross_total'])}")
    discount = float(preview.get("discount_total", 0) or 0)
    if discount > 0:
        lines.append(f"{'DESCONTO':<{width - len(fmt_money(discount))}}{fmt_money(discount)}")
    lines.append(f"{'TOTAL':<{width - len(fmt_money(preview['net_total']))}}{fmt_money(preview['net_total'])}")
    lines.append(separator)
    lines.append("ESTE CUPOM NÃO TEM VALOR FISCAL".center(width))
    lines.append("COMPROVANTE DE VENDA".center(width))
    payments = preview.get("payments", [])
    if payments:
        lines.append(separator)
        lines.append("PAGAMENTOS".center(width))
        for payment in payments:
            label = _receipt_payment_name(str(payment.get("method", "")))
            amount = fmt_money(float(payment.get("amount", 0) or 0))
            lines.append(f"{label[:width - len(amount) - 1]:<{width - len(amount)}}{amount}")
    lines.append(separator)
    if footer:
        lines.append(footer[:width].center(width))
    else:
        lines.append("Obrigado pela sua compra!".center(width))
        lines.append("Volte sempre!".center(width))
    return normalize_receipt_text("\n".join(lines))


def fmt_date_br(value: str) -> str:
    raw = (value or "").strip()
    if not raw:
        return ""
    base = raw.split("T")[0].split(" ")[0]
    try:
        dt = datetime.strptime(base, "%Y-%m-%d")
        return dt.strftime("%d/%m/%Y")
    except ValueError:
        return raw


def parse_money(text: str) -> float:
    return float(text.replace("R$", "").replace(".", "").replace(",", ".").strip())


def load_thumbnail(path: str) -> QPixmap:
    fallback = QPixmap(str(DEFAULT_PRODUCT_IMAGE)).scaled(40, 40, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
    p = Path(path)
    if not p.exists():
        return fallback
    pix = QPixmap(str(p))
    if pix.isNull():
        return fallback
    return pix.scaled(40, 40, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)


def apply_payment_badge(item: QTableWidgetItem, method: str) -> None:
    palette = {
        "DINHEIRO": ("#14532d", "#dcfce7"),
        "PIX": ("#0f766e", "#ccfbf1"),
        "PIX_MAQUININHA": ("#115e59", "#ccfbf1"),
        "DEBITO": ("#1e3a8a", "#dbeafe"),
        "CREDITO_AVISTA": ("#7c2d12", "#ffedd5"),
        "CREDITO_PARCELADO": ("#701a75", "#fae8ff"),
    }
    fg_hex, bg_hex = palette.get(method, ("#334155", "#e2e8f0"))
    item.setForeground(QColor(fg_hex))
    item.setBackground(QColor(bg_hex))


def apply_stock_badge(item: QTableWidgetItem, status: str) -> None:
    palette = {
        "OK": ("#166534", "#dcfce7"),
        "BAIXO": ("#92400e", "#fef3c7"),
        "CRITICO": ("#991b1b", "#fee2e2"),
    }
    fg_hex, bg_hex = palette.get(status, ("#334155", "#e2e8f0"))
    item.setForeground(QColor(fg_hex))
    item.setBackground(QColor(bg_hex))


def make_calendar_icon() -> QIcon:
    pix = QPixmap(16, 16)
    pix.fill(Qt.GlobalColor.transparent)

    painter = QPainter(pix)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

    painter.setPen(QPen(QColor("#4f46e5"), 1))
    painter.setBrush(QColor("#eef2ff"))
    painter.drawRoundedRect(1, 2, 14, 13, 2, 2)

    painter.setBrush(QColor("#c7d2fe"))
    painter.setPen(Qt.PenStyle.NoPen)
    painter.drawRect(1, 2, 14, 4)

    painter.setPen(QPen(QColor("#6366f1"), 1))
    painter.drawLine(5, 1, 5, 4)
    painter.drawLine(11, 1, 11, 4)

    painter.setPen(QPen(QColor("#94a3b8"), 1))
    for x in (4, 8, 12):
        for y in (8, 11, 14):
            painter.drawPoint(x, y)

    painter.end()
    return QIcon(pix)


def make_qr_icon() -> QIcon:
    pix = QPixmap(16, 16)
    pix.fill(Qt.GlobalColor.transparent)

    painter = QPainter(pix)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)
    painter.setPen(Qt.PenStyle.NoPen)

    dark = QColor("#0f766e")
    light = QColor("#ccfbf1")
    painter.setBrush(light)
    painter.drawRect(0, 0, 16, 16)

    painter.setBrush(dark)
    for x, y, w, h in (
        (1, 1, 5, 5),
        (2, 2, 3, 3),
        (10, 1, 5, 5),
        (11, 2, 3, 3),
        (1, 10, 5, 5),
        (2, 11, 3, 3),
        (9, 9, 2, 2),
        (12, 9, 2, 2),
        (9, 12, 2, 2),
        (12, 12, 2, 2),
        (7, 7, 1, 1),
        (8, 6, 1, 1),
    ):
        painter.drawRect(x, y, w, h)

    painter.end()
    return QIcon(pix)


def make_printer_icon() -> QIcon:
    pix = QPixmap(16, 16)
    pix.fill(Qt.GlobalColor.transparent)

    painter = QPainter(pix)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

    # Folha superior
    painter.setPen(QPen(QColor("#64748b"), 1))
    painter.setBrush(QColor("#f8fafc"))
    painter.drawRoundedRect(4, 1, 8, 4, 1, 1)

    # Corpo da impressora
    painter.setPen(QPen(QColor("#334155"), 1))
    painter.setBrush(QColor("#e2e8f0"))
    painter.drawRoundedRect(2, 5, 12, 7, 2, 2)

    # Faixa/entrada
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(QColor("#94a3b8"))
    painter.drawRect(3, 6, 10, 2)

    # Folha saindo
    painter.setPen(QPen(QColor("#64748b"), 1))
    painter.setBrush(QColor("#ffffff"))
    painter.drawRoundedRect(4, 10, 8, 5, 1, 1)

    painter.end()
    return QIcon(pix)
