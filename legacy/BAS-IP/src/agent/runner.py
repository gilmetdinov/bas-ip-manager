import asyncio
import json
from typing import Any, Dict

import websockets

from src.config import load_config
from src.panels import PanelManager


async def run_agent(server_ws_url: str, site_id: str, config_path: str, ws_key: str = "CHANGE_ME_AGENT_KEY") -> None:
	config: Dict[str, Any] = load_config(config_path)
	manager = PanelManager.from_config(config)
	while True:
		try:
			# Безопасность: агент передаёт ключ доступа при установлении WS.
			async with websockets.connect(f"{server_ws_url}/ws/agent/{site_id}?key={ws_key}") as ws:
				while True:
					msg = await ws.recv()
					data = json.loads(msg)
					if data.get("type") == "open_all":
						duration = int(data.get("duration", 10))
						manager.open_all_doors(duration_seconds=duration)
						await ws.send(json.dumps({"ok": True}))
		except Exception:
			await asyncio.sleep(3)


