from .abstract import AbstractMethod
from fastapi import Header
from fastapi.responses import JSONResponse
from typing import Optional


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
                return JSONResponse({"ok": False, "code": self.CODES.UNAUTHORIZED}, status_code=401)
            return JSONResponse({"ok": True, "code": self.CODES.OK})




