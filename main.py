from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QIcon
from PySide6.QtWidgets import QApplication

from app.config import DEFAULT_SYSTEM_LOGO
from app.database import Database
from app.services.auth_service import AuthService
from app.ui.login_window import LoginWindow
from app.ui.main_window import MainWindow, install_screen_fit
from app.ui.theme import APP_STYLESHEET


def main() -> int:
    QApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    app = QApplication(sys.argv)
    install_screen_fit(app)
    app.setFont(QFont("Segoe UI", 10))
    if Path(DEFAULT_SYSTEM_LOGO).exists():
        app.setWindowIcon(QIcon(str(DEFAULT_SYSTEM_LOGO)))
    app.setStyleSheet(APP_STYLESHEET)

    db = Database()
    auth = AuthService(db)

    login = LoginWindow(auth)

    def on_authenticated(user) -> None:
        window = MainWindow(db, user)
        window.show()
        login.close()
        app.main_window = window  # type: ignore[attr-defined]

    login.authenticated.connect(on_authenticated)
    login.show()

    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
