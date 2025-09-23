from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional

from src.config import PanelConfig
from src.sdk.basip_client import BASIPClient


@dataclass
class Panel:
	"""Абстракция панели/домофона BAS-IP в системе.

	Содержит готовый клиент для выполнения операций.
	"""

	name: str
	client: BASIPClient

	def open_door(self, duration_seconds: int) -> None:
		"""Открыть дверь на указанное время.

		Реальная длительность зависит от того, используем ли GET-шаблон или POST.
		"""
		self.client.open_lock(duration_seconds)


class PanelManager:
	def __init__(self, panels: List[Panel]) -> None:
		self._panels = panels

	@classmethod
	def from_config(cls, config: Dict[str, Any]) -> "PanelManager":
		"""Создать менеджер панелей из словаря конфигурации (YAML).

		Поддерживает смешанные способы открытия (GET/POST) и статические токены.
		"""
		panels: List[Panel] = []
		for p in config.get("panels", []):
			panel_cfg = PanelConfig(
				name=p["name"], base_url=p["base_url"], username=p.get("username", ""), password=p.get("password", ""),
				auth_path=p.get("auth_path", "/api/auth/login"),
				open_path=p.get("open_path", "/api/door/open"),
				token=p.get("token", ""),
				open_url_template=p.get("open_url_template", ""),
				lock_number=int(p.get("lock_number", 1)),
			)
			client = BASIPClient(
				base_url=panel_cfg.base_url,
				username=panel_cfg.username,
				password=panel_cfg.password,
				auth_path=panel_cfg.auth_path,
				open_path=panel_cfg.open_path,
				open_url_template=panel_cfg.open_url_template,
				lock_number=panel_cfg.lock_number,
			)
			if panel_cfg.token:
				client.static_token = panel_cfg.token
			panels.append(Panel(name=panel_cfg.name, client=client))
		return cls(panels)

	def open_all_doors(self, duration_seconds: int) -> None:
		"""Открыть все двери на площадке.

		Ошибки по отдельным панелям логируются и не прерывают общий процесс.
		"""
		for panel in self._panels:
			try:
				panel.open_door(duration_seconds)
			except Exception as exc:  # noqa: BLE001
				print(f"Failed to open door on {panel.name}: {exc}")


