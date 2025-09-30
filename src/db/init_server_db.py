import os
from dotenv import load_dotenv
from sqlalchemy import select
from sqlalchemy.orm import Session
from src.db import Base, get_postgres_engine, get_session_factory
from src.db.models import User
from src.security import hash_password
from src.config.env_keys import ADMIN_EMAIL, ADMIN_INIT_PASSWORD


def init_server_db(echo: bool = False, env_path: str | None = 'server.env') -> None:
    # Load env file if present
    if env_path:
        try:
            load_dotenv(env_path)
        except Exception:
            pass
    engine = get_postgres_engine(echo=echo)
    Base.metadata.create_all(engine)
    SessionLocal = get_session_factory(engine)

    admin_email = os.getenv(ADMIN_EMAIL, 'admin@example.com')
    admin_init_password = os.getenv(ADMIN_INIT_PASSWORD)

    if not admin_init_password:
        # nothing to seed
        return

    with SessionLocal() as session:
        session: Session
        existing = session.scalar(select(User).where(User.email == admin_email))
        if existing:
            return
        user = User(
            email=admin_email,
            password_hash=hash_password(admin_init_password),
            is_active=True,
            is_admin=True,
        )
        session.add(user)
        session.commit()


# if __name__ == '__main__':
#     init_server_db()


