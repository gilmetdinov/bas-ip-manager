from dataclasses import dataclass
from typing import Any, Dict, List

import yaml


@dataclass
class PanelConfig:
	name: str
	base_url: str
	username: str
	password: str
	auth_path: str = "/api/auth/login"
	open_path: str = "/api/door/open"
	# Optional: direct Bearer token (skips login if provided)
	token: str = ""
	# Optional: GET URL template to open lock (overrides open_path). Use {lock}
	open_url_template: str = ""
	# Optional: lock number placeholder value
	lock_number: int = 1
	# Optional panel-specific settings can be extended here


@dataclass
class AppConfig:
	panels: List[PanelConfig]


def load_config(path: str) -> Dict[str, Any]:
	with open(path, "r", encoding="utf-8") as f:
		return yaml.safe_load(f)


