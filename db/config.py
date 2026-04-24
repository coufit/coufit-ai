import os
from pathlib import Path
from urllib.parse import quote_plus

BASE_DIR = Path(__file__).resolve().parent.parent
ENV_FILE = BASE_DIR / ".env"


def _load_env_file() -> None:
    if not ENV_FILE.exists():
        return

    for raw_line in ENV_FILE.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()

        if value and value[0] == value[-1] and value[0] in {"'", '"'}:
            value = value[1:-1]

        os.environ.setdefault(key, value)


def _get_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


_load_env_file()


def get_db_settings() -> dict:
    return {
        "host": os.getenv("DB_HOST", "localhost"),
        "port": int(os.getenv("DB_PORT", "3306")),
        "user": os.getenv("DB_USER", "root"),
        "password": os.getenv("DB_PASSWORD", "1234"),
        "database": os.getenv("DB_NAME", "coufit"),
        "charset": os.getenv("DB_CHARSET", "utf8mb4"),
        "autocommit": _get_bool("DB_AUTOCOMMIT", True),
        "local_infile": _get_bool("DB_LOCAL_INFILE", True),
    }


def get_sqlalchemy_url() -> str:
    settings = get_db_settings()
    user = quote_plus(settings["user"])
    password = quote_plus(settings["password"])
    host = settings["host"]
    port = settings["port"]
    database = settings["database"]
    charset = settings["charset"]
    return f"mysql+pymysql://{user}:{password}@{host}:{port}/{database}?charset={charset}"


def get_pymysql_connection_kwargs() -> dict:
    settings = get_db_settings()
    return {
        "host": settings["host"],
        "port": settings["port"],
        "user": settings["user"],
        "password": settings["password"],
        "db": settings["database"],
        "charset": settings["charset"],
        "autocommit": settings["autocommit"],
        "local_infile": settings["local_infile"],
    }
