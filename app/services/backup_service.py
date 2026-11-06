from __future__ import annotations

import smtplib
import socket
import sqlite3
import ssl
import time
from datetime import datetime
from email.message import EmailMessage
from pathlib import Path
from typing import Callable

from app.config import BACKUP_DIR, DB_PATH, SMTP_HOST, SMTP_PORT, SMTP_SENDER_EMAIL, SMTP_SENDER_PASSWORD

SMTP_TIMEOUT = 15
MAX_ATTEMPTS = 3
RETRY_DELAY = 3
MAX_ATTACHMENT_BYTES = 24 * 1024 * 1024

ProgressCallback = Callable[[str], None]


class BackupEmailError(RuntimeError):
    """Falha de envio com mensagem amigavel para o usuario."""


def _smtp_endpoint(sender: str) -> tuple[str, int, bool]:
    """Retorna (host, porta, usa_ssl_direto)."""
    if SMTP_HOST:
        port = SMTP_PORT or 465
        return SMTP_HOST, port, port == 465
    domain = sender.rsplit("@", 1)[-1].lower()
    if domain in {"outlook.com", "hotmail.com", "live.com", "msn.com"}:
        return "smtp-mail.outlook.com", 587, False
    if domain in {"yahoo.com", "yahoo.com.br"}:
        return "smtp.mail.yahoo.com", 465, True
    return "smtp.gmail.com", 465, True


class BackupService:
    def create_backup_file(self) -> Path:
        BACKUP_DIR.mkdir(exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        dest = BACKUP_DIR / f"backup_{stamp}.db"
        counter = 1
        while dest.exists():
            dest = BACKUP_DIR / f"backup_{stamp}_{counter}.db"
            counter += 1
        # A API de backup do SQLite gera uma copia consistente mesmo com o banco em uso.
        source = sqlite3.connect(str(DB_PATH))
        target = sqlite3.connect(str(dest))
        try:
            source.backup(target)
        finally:
            target.close()
            source.close()
        return dest

    def backup_exists_for_today(self) -> bool:
        """Informa se ja existe um backup gerado na data de hoje."""
        today_prefix = f"backup_{datetime.now():%Y%m%d}"
        if not BACKUP_DIR.is_dir():
            return False
        return any(p.name.startswith(today_prefix) for p in BACKUP_DIR.glob("backup_*.db"))

    def restore_backup(self, backup_file: str | Path) -> Path:
        """Restaura um backup .db sobre o banco atual. Retorna o backup de seguranca do estado anterior."""
        source_path = Path(backup_file)
        if not source_path.is_file():
            raise ValueError("Arquivo de backup não encontrado.")
        source = None
        try:
            source = sqlite3.connect(f"file:{source_path.as_posix()}?mode=ro", uri=True)
            if source.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
                raise ValueError("O arquivo de backup está corrompido.")
            tables = {r[0] for r in source.execute("SELECT name FROM sqlite_master WHERE type='table'")}
            if not {"users", "products", "sales", "company_config"} <= tables:
                raise ValueError("Este arquivo não é um backup válido do Gestão Inteligente.")
        except sqlite3.DatabaseError:
            raise ValueError("Este arquivo não é um backup válido do Gestão Inteligente.") from None
        else:
            safety = self.create_backup_file()
            target = sqlite3.connect(str(DB_PATH))
            try:
                source.backup(target)
            finally:
                target.close()
        finally:
            if source is not None:
                source.close()
        return safety
    def has_credentials(self) -> bool:
        return bool(SMTP_SENDER_EMAIL and SMTP_SENDER_PASSWORD)

    def has_internet(self) -> bool:
        host, port, _ = _smtp_endpoint(SMTP_SENDER_EMAIL)
        try:
            with socket.create_connection((host, port), timeout=6):
                return True
        except OSError:
            return False

    def _build_message(self, destination_email: str, backup_file: Path) -> EmailMessage:
        if backup_file.stat().st_size > MAX_ATTACHMENT_BYTES:
            raise BackupEmailError("O arquivo de backup excede o limite de anexo do e-mail (24 MB).")
        msg = EmailMessage()
        msg["Subject"] = f"Backup automático - Gestão Inteligente ({datetime.now():%d/%m/%Y %H:%M})"
        msg["From"] = SMTP_SENDER_EMAIL
        msg["To"] = destination_email
        msg.set_content(
            "Segue em anexo o backup do sistema Gestão Inteligente.\n"
            f"Arquivo: {backup_file.name}\n"
            f"Gerado em: {datetime.now():%d/%m/%Y %H:%M:%S}\n"
        )
        msg.add_attachment(
            backup_file.read_bytes(),
            maintype="application",
            subtype="octet-stream",
            filename=backup_file.name,
        )
        return msg

    def _send_once(self, msg: EmailMessage) -> None:
        host, port, use_ssl = _smtp_endpoint(SMTP_SENDER_EMAIL)
        context = ssl.create_default_context()
        if use_ssl:
            smtp = smtplib.SMTP_SSL(host, port, timeout=SMTP_TIMEOUT, context=context)
        else:
            smtp = smtplib.SMTP(host, port, timeout=SMTP_TIMEOUT)
        try:
            if not use_ssl:
                smtp.starttls(context=context)
            smtp.login(SMTP_SENDER_EMAIL, SMTP_SENDER_PASSWORD)
            smtp.send_message(msg)
        finally:
            try:
                smtp.quit()
            except Exception:
                pass

    def send_backup_email(
        self,
        destination_email: str,
        backup_file: Path,
        progress: ProgressCallback | None = None,
    ) -> None:
        """Envia o backup com ate MAX_ATTEMPTS tentativas. Levanta BackupEmailError em caso de falha."""
        notify = progress or (lambda _text: None)
        destination_email = (destination_email or "").strip()
        if not self.has_credentials():
            raise BackupEmailError("Credenciais de e-mail não configuradas no arquivo .env.")
        if not destination_email or "@" not in destination_email:
            raise BackupEmailError("E-mail de destino não cadastrado em Configurações > Empresa.")

        notify("Verificando conexão com a internet...")
        if not self.has_internet():
            raise BackupEmailError("Sem conexão com a internet.")

        msg = self._build_message(destination_email, backup_file)
        last_error = "erro desconhecido"
        for attempt in range(1, MAX_ATTEMPTS + 1):
            notify(f"Enviando para {destination_email} (tentativa {attempt} de {MAX_ATTEMPTS})...")
            try:
                self._send_once(msg)
                return
            except smtplib.SMTPAuthenticationError:
                raise BackupEmailError("Falha de autenticação do e-mail remetente. Verifique o .env (senha de app).")
            except smtplib.SMTPRecipientsRefused:
                raise BackupEmailError("O e-mail de destino foi recusado. Verifique o cadastro da empresa.")
            except (smtplib.SMTPException, OSError, TimeoutError) as exc:
                last_error = str(exc) or exc.__class__.__name__
                if attempt < MAX_ATTEMPTS:
                    notify(f"Falha na tentativa {attempt}. Tentando novamente...")
                    time.sleep(RETRY_DELAY)
        raise BackupEmailError(f"Não foi possível enviar após {MAX_ATTEMPTS} tentativas ({last_error}).")
