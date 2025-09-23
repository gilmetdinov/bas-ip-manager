from dataclasses import dataclass
from typing import Any, Dict, Optional

import logging
import time
import requests
from src.error_codes import PANEL_OPEN_FAILED, UNAUTHORIZED_PANEL, NETWORK_ERROR, PANEL_CONFIG_ERROR
from src.logging_setup import setup_logging


class BASIPError(Exception):
	"""Исключение SDK-клиента BAS-IP.

	Используется для единообразной обработки ошибок верхним уровнем.
	"""


@dataclass
class BASIPClient:
	"""Минимальный клиент BAS-IP для авторизации и открытия замка.

	Параметры и поведение максимально конфигурируемые, чтобы быстро
	подстроиться под конкретную прошивку/версию API.
	"""
	base_url: str
	username: str
	password: str
	auth_path: str = "/api/auth/login"
	open_path: str = "/api/door/open"
	open_url_template: str = ""
	lock_number: int = 1
	access_token: Optional[str] = None
	static_token: Optional[str] = None
	request_timeout_seconds: int = 10
	retries: int = 3
	backoff_seconds: float = 0.5

	def __post_init__(self) -> None:
		setup_logging("sdk")
		self._logger = logging.getLogger("sdk")

	def _auth_headers(self) -> Dict[str, str]:
		"""Вернуть заголовки авторизации (Bearer).

		Если задан статический токен, логин не выполняется.
		"""
		if self.static_token:
			return {"Authorization": f"Bearer {self.static_token}"}
		if not self.access_token:
			self.login()
		return {"Authorization": f"Bearer {self.access_token}"}

	def login(self) -> None:
		"""Выполнить авторизацию на панели BAS-IP.

		Примечание: пути эндпоинтов зависят от версии прошивки.
		"""
		url = f"{self.base_url.rstrip('/')}{self.auth_path}"
		resp = requests.post(url, json={"username": self.username, "password": self.password}, timeout=self.request_timeout_seconds)
		if resp.status_code >= 400:
			self._logger.warning("auth_failed url=%s status=%s code=%s", url, resp.status_code, UNAUTHORIZED_PANEL)
			raise BASIPError(f"Auth failed: {resp.status_code} {resp.text}")
		data = resp.json()
		self.access_token = data.get("access_token") or data.get("token")
		if not self.access_token:
			raise BASIPError("No access token in auth response")

	def open_lock(self, duration_seconds: int) -> None:
		"""Открыть замок.

		Предпочтительно используется GET-шаблон.
		Если он не задан — используется POST с полем duration.
		"""
		if self.open_url_template:
			# Документация допускает lock-number ∈ {0,1,2}
			if self.lock_number not in (0, 1, 2):
				self._logger.error("invalid_lock_number lock=%s code=%s", self.lock_number, PANEL_CONFIG_ERROR)
				raise BASIPError(f"Invalid lock_number: {self.lock_number}; allowed: 0,1,2")
			path = self.open_url_template.replace(":lock-number", str(self.lock_number)).replace("{lock}", str(self.lock_number))
			url = path if path.startswith("http") else f"{self.base_url.rstrip('/')}{path}"
			self._do_request_with_retries("GET", url, headers={"Accept": "application/json", **self._auth_headers()})
			return

		# Default: POST with duration
		url = f"{self.base_url.rstrip('/')}{self.open_path}"
		payload: Dict[str, Any] = {"duration": duration_seconds}
		self._do_request_with_retries("POST", url, json=payload, headers=self._auth_headers())

	def _do_request_with_retries(self, method: str, url: str, **kwargs: Any) -> requests.Response:
		"""Выполнить HTTP‑запрос с повторными попытками и экспоненциальным бэкоффом."""
		last_exc: Optional[Exception] = None
		for attempt in range(1, self.retries + 1):
			try:
				resp = requests.request(method, url, timeout=self.request_timeout_seconds, **kwargs)
				if resp.status_code >= 400:
					self._logger.warning("http_error method=%s url=%s status=%s code=%s", method, url, resp.status_code, PANEL_OPEN_FAILED)
					raise BASIPError(f"HTTP {method} {url} failed: {resp.status_code} {resp.text}")
				return resp
			except Exception as exc:  # noqa: BLE001
				last_exc = exc
				self._logger.error("request_exception method=%s url=%s attempt=%s code=%s err=%s", method, url, attempt, NETWORK_ERROR, str(exc))
				if attempt >= self.retries:
					break
				time.sleep(self.backoff_seconds * (2 ** (attempt - 1)))
		raise BASIPError(str(last_exc) if last_exc else "request failed")


