import os
from cryptography.fernet import Fernet
from sqlalchemy import select
from src.db.init_agent_db import KV, _get_or_create_secret
from src.db import get_sqlite_engine, get_session_factory


class SecureKVStore:
    def __init__(self):
        engine = get_sqlite_engine()
        self._Session = get_session_factory(engine)
        path = os.getenv('SQLITE_PATH', './agent.db')
        self._fernet = Fernet(_get_or_create_secret(path))

    def set(self, key: str, value: str) -> None:
        token = self._fernet.encrypt(value.encode('utf-8')).decode('utf-8')
        with self._Session() as session:
            row = session.get(KV, key)
            if row is None:
                row = KV(key=key, value_enc=token)
                session.add(row)
            else:
                row.value_enc = token
            session.commit()

    def get(self, key: str) -> str | None:
        with self._Session() as session:
            row = session.get(KV, key)
            if not row:
                return None
            try:
                return self._fernet.decrypt(row.value_enc.encode('utf-8')).decode('utf-8')
            except Exception:
                return None


