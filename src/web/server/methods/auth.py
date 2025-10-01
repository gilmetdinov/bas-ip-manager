from .abstract import AbstractMethod
from fastapi import Header, Body
from fastapi.responses import JSONResponse
from typing import Optional
from sqlalchemy import select
from sqlalchemy.orm import Session
from src.db import get_postgres_engine, get_session_factory
from src.db.models import User
from src.security import verify_password


class AuthMethod(AbstractMethod, route='/auth/agent'):
    """Простой эндпоинт аутентификации агента по API‑ключу.

    Ключ передается в заголовке `x-api-key` или в query/body (на усмотрение клиента).
    Для упрощения — используем только заголовок.
    """

    def set(self):
        @self._app.post(self._route)
        async def auth(x_api_key: Optional[str] = Header(default=None, alias='x-api-key')) -> JSONResponse:
            # Проверяем совпадение с ключом на сервере
            if not x_api_key or x_api_key != self._config.api_key:
                return JSONResponse({"ok": False, "code": self.CODES.UNAUTHORIZED_PANEL}, status_code=401)
            return JSONResponse({"ok": True, "code": self.CODES.OK})

        @self._app.post('/auth/login')
        async def login(payload: dict = Body(...)) -> JSONResponse:
            email = (payload.get('email') or '').strip().lower()
            password = payload.get('password') or ''
            if not email or not password:
                return JSONResponse({"ok": False, "code": self.CODES.BAD_REQUEST}, status_code=400)
            engine = get_postgres_engine()
            session_factory = get_session_factory(engine)
            with session_factory() as session:
                session: Session
                user = session.scalar(select(User).where(User.email == email))
                if not user or not verify_password(password, user.password_hash) or not user.is_active:
                    return JSONResponse({"ok": False, "code": self.CODES.UNAUTHORIZED_PANEL}, status_code=401)
                return JSONResponse({"ok": True, "user": {"email": user.email, "is_admin": user.is_admin}, "code": self.CODES.OK})





