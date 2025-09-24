from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional

import logging
import time
import requests


class BASIPClientError(Exception):
    pass


@dataclass
class BASIPClient:
    """Минимальный REST‑клиент BAS‑IP с поддержкой логина и открытия двери.

    Примечания:
    - Конкретные эндпоинты зависят от прошивки, поэтому пути настраиваемые
    - Поддерживается как динамический токен (через логин), так и статический
    """

    base_url: str
    username: str
    password: str

    # Настраиваемые пути API (зависят от версии прошивки)
    auth_path: str = "/api/auth/login"
    open_path: str = "/api/door/open"
    open_url_template: str = ""  # например: "/api/door/:lock-number/open"
    lock_number: int = 1

    # Авторизация
    access_token: Optional[str] = None
    static_token: Optional[str] = None

    # Параметры HTTP‑клиента
    request_timeout_seconds: int = 10
    retries: int = 3
    backoff_seconds: float = 0.5

    def __post_init__(self) -> None:
        self._logger = logging.getLogger("basip-client")

    # Публичные методы
    def login(self) -> None:
        """Аутентификация на устройстве BAS‑IP с сохранением access_token."""
        if self.static_token:
            # Если есть статический токен — логин не требуется
            self.access_token = self.static_token
            return

        url = f"{self.base_url.rstrip('/')}{self.auth_path}"
        try:
            resp = requests.post(
                url,
                json={"username": self.username, "password": self.password},
                timeout=self.request_timeout_seconds,
            )
        except Exception as exc:  # noqa: BLE001
            raise BASIPClientError(f"Ошибка запроса аутентификации: {exc}")

        if resp.status_code >= 400:
            raise BASIPClientError(f"Ошибка аутентификации: {resp.status_code} {resp.text}")

        data = resp.json()
        token = data.get("access_token") or data.get("token")
        if not token:
            raise BASIPClientError("В ответе отсутствует access token")
        self.access_token = token

    def open_lock(self, duration_seconds: int) -> None:
        """Открыть замок/дверь на указанное количество секунд.

        Если задан шаблон GET‑URL — используем его, иначе POST с полем duration.
        """
        if self.open_url_template:
            if self.lock_number not in (0, 1, 2):
                raise BASIPClientError("Недопустимый lock_number: разрешены 0,1,2")
            path = (
                self.open_url_template
                .replace(":lock-number", str(self.lock_number))
                .replace("{lock}", str(self.lock_number))
            )
            url = path if path.startswith("http") else f"{self.base_url.rstrip('/')}{path}"
            self._do_request_with_retries("GET", url, headers={"Accept": "application/json", **self._auth_headers()})
            return

        # Вариант по умолчанию — POST с длительностью
        url = f"{self.base_url.rstrip('/')}{self.open_path}"
        payload: Dict[str, Any] = {"duration": duration_seconds}
        self._do_request_with_retries("POST", url, json=payload, headers=self._auth_headers())

    # Внутренние помощники
    def _auth_headers(self) -> Dict[str, str]:
        if self.static_token and not self.access_token:
            self.access_token = self.static_token
        if not self.access_token:
            self.login()
        return {"Authorization": f"Bearer {self.access_token}"}

    def _do_request_with_retries(self, method: str, url: str, **kwargs: Any) -> requests.Response:
        last_exc: Optional[Exception] = None
        for attempt in range(1, self.retries + 1):
            try:
                resp = requests.request(method, url, timeout=self.request_timeout_seconds, **kwargs)
                if resp.status_code >= 400:
                    raise BASIPClientError(f"HTTP {method} {url} завершился ошибкой: {resp.status_code} {resp.text}")
                return resp
            except Exception as exc:  # noqa: BLE001
                last_exc = exc
                if attempt >= self.retries:
                    break
                time.sleep(self.backoff_seconds * (2 ** (attempt - 1)))
        raise BASIPClientError(str(last_exc) if last_exc else "запрос не выполнен")


