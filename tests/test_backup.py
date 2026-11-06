"""Testes do backup diario."""
from __future__ import annotations

from datetime import datetime
from unittest import mock

import app.services.backup_service as bs
from app.services.backup_service import BackupService


def test_backup_exists_for_today(db, tmp_path):
    with mock.patch.object(bs, "BACKUP_DIR", tmp_path):
        svc = BackupService()
        assert svc.backup_exists_for_today() is False
        f = svc.create_backup_file()
        assert svc.backup_exists_for_today() is True
        assert f.name.startswith(f"backup_{datetime.now():%Y%m%d}")


def test_backup_diario_dispara_na_abertura(qapp, db, user):
    """MainWindow deve disparar o backup diario (em thread) quando nao ha backup do dia."""
    from pathlib import Path

    from app.ui.main_window import MainWindow

    with mock.patch.object(BackupService, "create_backup_file", return_value=Path("x.db")) as mk, \
         mock.patch.object(BackupService, "backup_exists_for_today", return_value=False):
        win = MainWindow(db, user)
        win._run_daily_backup()
        import time
        time.sleep(0.3)
        assert mk.called


def test_backup_diario_nao_roda_se_ja_existe(qapp, db, user):
    from app.ui.main_window import MainWindow

    with mock.patch.object(BackupService, "create_backup_file") as mk, \
         mock.patch.object(BackupService, "backup_exists_for_today", return_value=True):
        win = MainWindow(db, user)
        win._run_daily_backup()
        import time
        time.sleep(0.2)
        assert not mk.called
