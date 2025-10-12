from __future__ import annotations

from enum import StrEnum

from dataclasses import dataclass
from typing import Any, Dict, Optional

import logging
import time
import requests


from src.security.passwords import create_md5_hash


class BASIPClientError(Exception):
    pass


class BASIPv216Routes(StrEnum):
    """For API version v2.16.0"""
    login = '/login'
    # GET open via HTTP (access allowed event)
    open_door = '/access/general/lock/open/remote/accepted/{lock_number}'
    # POST start emergency and open for the specified time
    open_emergency = '/access/general/lock/open/emergency'


@dataclass
class BASIPClient:
    """Минимальный REST‑клиент BAS‑IP с поддержкой логина и открытия двери.

    Примечания:
    - Конкретные эндпоинты зависят от прошивки, поэтому пути настраиваемые
    - Поддерживается как динамический токен (через логин), так и статический
    """

    ROUTES = BASIPv216Routes
    
    door = None
    base_url: str
    # параметры открытия дверей
    lock_number: int = 0
    # Авторизация
    username: Optional[str] = None
    password: Optional[str] = None
    access_token: Optional[str] = None
    static_token: Optional[str] = None

    # Параметры HTTP‑клиента
    request_timeout_seconds: int = 10
    retries: int = 3
    backoff_seconds: float = 0.5

    def __post_init__(self) -> None:
        self._logger = logging.getLogger("basip-client")
        if self.static_token is None and (self.username is None or self.password is None):
            raise AttributeError("Для клиента необходимо заполнить или статичный токен или имя пользователя и пароль")

    # Публичные методы
    def login(self) -> None:
        """Аутентификация на устройстве BAS‑IP с сохранением access_token."""
        if self.static_token:
            # Если есть статический токен — логин не требуется
            self.access_token = self.static_token
            return True

        try:
            resp = requests.get(
                f"{self.base_url}{self.ROUTES.login}",
                params={"username": self.username, "password": create_md5_hash(self.password).capitalize()},
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

    def start_emergency_and_open(self, unlock_time_seconds: int) -> None:
        """Запустить аварийный режим и открыть замки на указанный период.
        unlock_time_seconds должен быть в диапазоне [1..604800].
        """
        if unlock_time_seconds < 1 or unlock_time_seconds > 604800:
            raise BASIPClientError("unlock_time_seconds вне диапазона [1..604800]")
        url = f"{self.base_url}{self.ROUTES.open_emergency}"
        payload = {"locks": [{"lock_number": int(self.lock_number), "unlock_time": int(unlock_time_seconds)}]}
        self._do_request_with_retries(
            "POST",
            url,
            json=payload,
            headers={"Content-Type": "application/json", "Accept": "application/json", **self._auth_headers()},
        )

    def remote_open(self) -> None:
        """Открыть замок через HTTP (access allowed event)."""
        if self.lock_number not in (1, 2):
            raise BASIPClientError("Недопустимый lock_number: разрешены 1,2")
        # В спецификации используется ":lock-number" как path param. В формате String.format применяем {lock_number}
        url = f"{self.base_url}{self.ROUTES.open_door.format(lock_number=self.lock_number)}"
        # GET без тела согласно спецификации. Только заголовки.
        self._do_request_with_retries(
            "GET",
            url,
            headers={"Accept": "application/json", **self._auth_headers()},
        )

    def open_lock(self, duration_seconds: int) -> None:
        """Удобный метод: стартует emergency и делает один импульс remote_open.
        Для длительного периода вызывающий код может сам повторять remote_open в цикле.
        """
        # Старт аварийного режима на требуемое время
        self.start_emergency_and_open(unlock_time_seconds=duration_seconds)
        # Сразу делаем один импульс открытия для генерации события "access allowed"
        self.remote_open()

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


