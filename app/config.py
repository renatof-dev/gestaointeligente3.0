from __future__ import annotations

import os
import sys
from pathlib import Path

FROZEN = bool(getattr(sys, "frozen", False))
# Recursos somente leitura (imagens) e pasta de instalacao (onde fica o .env).
RESOURCE_DIR = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent.parent))
INSTALL_DIR = Path(sys.executable).resolve().parent if FROZEN else Path(__file__).resolve().parent.parent
# Dados do cliente ficam em pasta gravavel do usuario quando instalado (Program Files nao e gravavel).
BASE_DIR = (Path(os.environ.get("LOCALAPPDATA") or Path.home()) / "GestaoInteligente") if FROZEN else INSTALL_DIR
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "gestao_inteligente.db"

IMAGES_DIR = RESOURCE_DIR / "imagens"
DEFAULT_PRODUCT_IMAGE = IMAGES_DIR / "sem_foto.png"
DEFAULT_SYSTEM_LOGO = IMAGES_DIR / "logo_sistema.png"

BACKUP_DIR = BASE_DIR / "backups"
PDF_DIR = BASE_DIR / "cupons"

APP_NAME = "Gestao Inteligente 3.0"
APP_VERSION = "3.0.5"
DEFAULT_MASTER_USERNAME = "admin"
DEFAULT_MASTER_PASSWORD = "admin123"

def _load_env_file(path: Path, overwrite: bool = False) -> None:
    """Carrega pares CHAVE=VALOR de um arquivo .env.

    Por padrao nao sobrescreve variaveis ja definidas; com overwrite=True, os valores
    do arquivo prevalecem (usado para o .env do usuario ter prioridade sobre o da instalacao).
    """
    if not path.exists():
        return
    try:
        lines = path.read_text(encoding="utf-8-sig").splitlines()
    except OSError:
        return
    for raw in lines:
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and (overwrite or key not in os.environ):
            os.environ[key] = value


# Ordem de prioridade: primeiro carrega o .env da instalacao (valores padrao),
# depois o .env da pasta de dados do usuario SOBRESCREVENDO (prioridade maior).
# Assim, para trocar a senha de e-mail basta editar %LOCALAPPDATA%\GestaoInteligente\.env,
# sem precisar recompilar/reinstalar o sistema.
_load_env_file(INSTALL_DIR / ".env")
_load_env_file(BASE_DIR / ".env", overwrite=True)

# Credenciais lidas do arquivo .env (EMAIL_REM / EMAIL_SENHA) ou das variaveis GI_SMTP_*.
SMTP_SENDER_EMAIL = (os.getenv("EMAIL_REM") or os.getenv("GI_SMTP_SENDER") or "").strip()
SMTP_SENDER_PASSWORD = (os.getenv("EMAIL_SENHA") or os.getenv("GI_SMTP_PASSWORD") or "").replace(" ", "")
SMTP_HOST = (os.getenv("EMAIL_SMTP_HOST") or "").strip()
SMTP_PORT = int(os.getenv("EMAIL_SMTP_PORT") or 0)


def ensure_directories() -> None:
    BASE_DIR.mkdir(parents=True, exist_ok=True)
    DATA_DIR.mkdir(exist_ok=True)
    BACKUP_DIR.mkdir(exist_ok=True)
    PDF_DIR.mkdir(exist_ok=True)
