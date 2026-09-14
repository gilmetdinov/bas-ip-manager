from typing import Any, Dict

from src.config import load_config
from src.panels import PanelManager


def run_cli(action: str, config_path: str, duration: int) -> None:
	"""Простой CLI-обработчик.

	Поддерживает действие open_all для локального теста без сервера.
	"""
	config: Dict[str, Any] = load_config(config_path)
	manager = PanelManager.from_config(config)

	if action == "open_all":
		manager.open_all_doors(duration_seconds=duration)
	else:
		raise ValueError(f"Unknown action: {action}")


