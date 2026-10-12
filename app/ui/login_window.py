from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QCursor, QIcon, QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from app.config import DEFAULT_SYSTEM_LOGO
from app.services.auth_service import AuthService, AuthUser


class LoginWindow(QWidget):
    authenticated = Signal(object)

    def __init__(self, auth_service: AuthService) -> None:
        super().__init__()
        self.auth_service = auth_service
        self.setWindowTitle("Login - Gestão Inteligente 3.0")
        if Path(DEFAULT_SYSTEM_LOGO).exists():
            self.setWindowIcon(QIcon(str(DEFAULT_SYSTEM_LOGO)))
        screen = QApplication.screenAt(QCursor.pos()) or QApplication.primaryScreen()
        area = screen.availableGeometry() if screen else None
        min_w, min_h = (min(900, area.width()), min(560, area.height())) if area else (900, 560)
        self.setMinimumSize(min_w, min_h)
        self._build_ui()
        if area:
            width = min(area.width(), max(min_w, min(1100, int(area.width() * 0.7))))
            height = min(area.height(), max(min_h, min(700, int(area.height() * 0.8))))
            self.resize(width, height)
            self.move(area.x() + (area.width() - width) // 2, area.y() + (area.height() - height) // 2)

    def _build_ui(self) -> None:
        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self.setStyleSheet(
            "QFrame#LoginShowcase {"
            "  background: qlineargradient(x1:0, y1:0, x2:1, y2:1,"
            "    stop:0 #0a1f34, stop:0.52 #133652, stop:1 #1f4e73);"
            "}"
            "QFrame#LogoWrap {"
            "  background: rgba(255,255,255,0.07);"
            "  border: 1px solid rgba(255,255,255,0.14);"
            "  border-radius: 16px;"
            "}"
            "QLabel#ShowcaseTag {"
            "  color: #dbe8fa;"
            "  font-size: 11px;"
            "  font-weight: 800;"
            "  letter-spacing: 1px;"
            "}"
            "QLabel#ShowcaseTitle { color: #f1f7ff; font-size: 29px; font-weight: 800; }"
            "QLabel#ShowcaseText { color: #c7d8ee; font-size: 13px; font-weight: 600; }"
            "QLabel#ShowcaseBullets { color: #dbe8fa; font-size: 13px; font-weight: 600; }"
            "QLabel#ShowcaseFooter { color: #a9bfd7; font-size: 11px; font-weight: 700; }"

            "QFrame#LoginWorkspace { background: #eff4fa; }"
            "QFrame#LoginPanel {"
            "  background: #ffffff;"
            "  border: 1px solid #d6e1ef;"
            "  border-radius: 14px;"
            "}"
            "QLabel#LoginTitle { color: #0f172a; font-size: 25px; font-weight: 800; }"
            "QLabel#LoginSubtitle { color: #66758b; font-size: 13px; font-weight: 600; }"
            "QLabel#LoginHint { color: #64748b; font-size: 12px; font-weight: 700; }"
            "QLabel#HelpText { color: #708197; font-size: 11px; font-weight: 600; }"

            "QLineEdit {"
            "  background: #ffffff;"
            "  border: 1px solid #d4deec;"
            "  border-radius: 9px;"
            "  padding: 8px 10px;"
            "  font-size: 13px;"
            "}"
            "QLineEdit:focus { border: 1px solid #635bff; }"
            "QFrame#PasswordWrap {"
            "  background: #ffffff;"
            "  border: 1px solid #d4deec;"
            "  border-radius: 9px;"
            "}"
            "QFrame#PasswordWrap QLineEdit {"
            "  border: none;"
            "  padding: 8px 10px;"
            "  background: transparent;"
            "}"
            "QToolButton#TogglePasswordButton {"
            "  border: none;"
            "  background: #f8fafd;"
            "  border-left: 1px solid #e2e8f0;"
            "  color: #475569;"
            "  min-width: 58px;"
            "  max-width: 58px;"
            "  border-top-right-radius: 8px;"
            "  border-bottom-right-radius: 8px;"
            "  font-weight: 700;"
            "}"
            "QToolButton#TogglePasswordButton:hover {"
            "  background: #edf2fa;"
            "  color: #635bff;"
            "}"
            "QPushButton#LoginPrimaryButton {"
            "  background: #635bff;"
            "  color: #ffffff;"
            "  border: 1px solid #5249e6;"
            "  border-radius: 10px;"
            "  padding: 9px 14px;"
            "  font-weight: 800;"
            "}"
            "QPushButton#LoginPrimaryButton:hover {"
            "  background: #5249e6;"
            "}"
        )

        left = QFrame()
        left.setObjectName("LoginShowcase")
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(42, 34, 42, 34)
        left_layout.setSpacing(12)

        badge = QLabel("GESTÃO INTELIGENTE 3.0")
        badge.setObjectName("ShowcaseTag")
        badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        left_layout.addWidget(badge, 0, Qt.AlignmentFlag.AlignCenter)

        left_layout.addStretch()

        logo_wrap = QFrame()
        logo_wrap.setObjectName("LogoWrap")
        logo_wrap_layout = QVBoxLayout(logo_wrap)
        logo_wrap_layout.setContentsMargins(16, 16, 16, 16)

        logo = QLabel()
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_path = Path(DEFAULT_SYSTEM_LOGO)
        if logo_path.exists():
            logo.setPixmap(QPixmap(str(logo_path)).scaledToWidth(170, Qt.TransformationMode.SmoothTransformation))
        logo_wrap_layout.addWidget(logo)
        left_layout.addWidget(logo_wrap, 0, Qt.AlignmentFlag.AlignCenter)

        lbl_title = QLabel("Gestão Inteligente 3.0")
        lbl_title.setObjectName("ShowcaseTitle")
        lbl_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        left_layout.addWidget(lbl_title)

        lbl_sub = QLabel("Sistema completo para vendas, PDV e controle financeiro")
        lbl_sub.setWordWrap(True)
        lbl_sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_sub.setObjectName("ShowcaseText")
        left_layout.addWidget(lbl_sub)

        bullets = QLabel("• PDV rápido e intuitivo\n• Lucro real com taxas e descontos\n• Estoque, clientes e caixa em uma só tela")
        bullets.setAlignment(Qt.AlignmentFlag.AlignCenter)
        bullets.setObjectName("ShowcaseBullets")
        left_layout.addWidget(bullets)

        left_layout.addStretch()

        footer = QLabel("Plataforma local • segura • pronta para operar")
        footer.setObjectName("ShowcaseFooter")
        footer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        left_layout.addWidget(footer)

        right = QFrame()
        right.setObjectName("LoginWorkspace")
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(56, 34, 56, 34)
        right_layout.setSpacing(0)

        card = QFrame()
        card.setObjectName("LoginPanel")
        card.setMinimumWidth(380)
        card.setMaximumWidth(460)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(30, 26, 30, 24)
        card_layout.setSpacing(9)

        title = QLabel("Entrar no Sistema")
        title.setObjectName("LoginTitle")
        card_layout.addWidget(title)

        subtitle = QLabel("Acesse com suas credenciais para continuar")
        subtitle.setObjectName("LoginSubtitle")
        card_layout.addWidget(subtitle)

        card_layout.addSpacing(6)

        self.user_edit = QLineEdit()
        self.user_edit.setPlaceholderText("Usuário")
        self.user_edit.setClearButtonEnabled(True)

        self.pass_edit = QLineEdit()
        self.pass_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.pass_edit.setPlaceholderText("Senha")

        self.user_edit.setFocus()

        card_layout.addWidget(self.user_edit)

        pass_wrap = QFrame()
        pass_wrap.setObjectName("PasswordWrap")
        pass_layout = QHBoxLayout(pass_wrap)
        pass_layout.setContentsMargins(0, 0, 0, 0)
        pass_layout.setSpacing(0)
        pass_layout.addWidget(self.pass_edit)

        self.toggle_pass_btn = QToolButton()
        self.toggle_pass_btn.setObjectName("TogglePasswordButton")
        self.toggle_pass_btn.setText("Mostrar")
        self.toggle_pass_btn.setCheckable(True)
        self.toggle_pass_btn.toggled.connect(self._toggle_password_visibility)
        pass_layout.addWidget(self.toggle_pass_btn)

        card_layout.addWidget(pass_wrap)

        card_layout.addSpacing(4)

        self.btn_login = QPushButton("Entrar")
        self.btn_login.setObjectName("LoginPrimaryButton")
        self.btn_login.clicked.connect(self._handle_login)
        card_layout.addWidget(self.btn_login)

        help_lbl = QLabel("Acesso restrito a usuários autorizados")
        help_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        help_lbl.setObjectName("HelpText")
        card_layout.addWidget(help_lbl)

        right_layout.addStretch()
        right_layout.addWidget(card, 0, Qt.AlignmentFlag.AlignCenter)
        right_layout.addStretch()

        root.addWidget(left, 2)
        root.addWidget(right, 3)

        self.user_edit.returnPressed.connect(self._handle_login)
        self.pass_edit.returnPressed.connect(self._handle_login)
        self.user_edit.setFocus()

    def _toggle_password_visibility(self, checked: bool) -> None:
        self.pass_edit.setEchoMode(QLineEdit.EchoMode.Normal if checked else QLineEdit.EchoMode.Password)
        self.toggle_pass_btn.setText("Ocultar" if checked else "Mostrar")

    def _handle_login(self) -> None:
        self.btn_login.setEnabled(False)
        user = self.auth_service.login(self.user_edit.text(), self.pass_edit.text())
        if not user:
            self.btn_login.setEnabled(True)
            QMessageBox.warning(self, "Login", "Usuario ou senha invalidos.")
            return
        self.authenticated.emit(user)


def user_display(user: AuthUser) -> str:
    return f"{user.name} ({user.role})"
