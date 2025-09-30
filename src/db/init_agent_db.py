import os
from dotenv import load_dotenv
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column
from src.db import Base, get_sqlite_engine, get_session_factory
from cryptography.fernet import Fernet
from src.config.env_keys import SQLITE_PATH


class KV(Base):
    __tablename__ = 'kv_secure'
    key: Mapped[str] = mapped_column(String(255), primary_key=True)
    value_enc: Mapped[str] = mapped_column(String)


def _get_or_create_secret(path: str) -> bytes:
    key_path = f"{path}.key"
    if os.path.exists(key_path):
        with open(key_path, 'rb') as f:
            return f.read()
    secret = Fernet.generate_key()
    with open(key_path, 'wb') as f:
        f.write(secret)
    return secret


def init_agent_db(echo: bool = False, env_path: str | None = 'agent.env') -> None:
    if env_path:
        try:
            load_dotenv(env_path)
        except Exception:
            pass
    engine = get_sqlite_engine(echo=echo)
    Base.metadata.create_all(engine)
    # Ensure encryption key exists
    path = os.getenv(SQLITE_PATH, './agent.db')
    _get_or_create_secret(path)


# if __name__ == '__main__':
#     init_agent_db()


