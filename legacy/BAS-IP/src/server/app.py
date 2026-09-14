from typing import Dict
import logging

from fastapi import Depends, FastAPI, Header, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from src.error_codes import OK, INVALID_API_KEY, WS_AGENT_NOT_CONNECTED, SERVER_INTERNAL_ERROR
from src.logging_setup import setup_logging



# Центральный сервер.
# Задачи:
# - REST-эндпоинт для запуска открытия дверей по объекту (site_id)
# - WebSocket-хаб: поддерживает постоянное соединение с локальными агентами на площадках


class AgentHub:
	def __init__(self) -> None:
		self._agents: Dict[str, WebSocket] = {}

	async def register(self, site_id: str, ws: WebSocket) -> None:
		await ws.accept()
		self._agents[site_id] = ws

	def unregister(self, site_id: str) -> None:
		self._agents.pop(site_id, None)

	async def send_open_all(self, site_id: str, duration: int) -> None:
		ws = self._agents.get(site_id)
		if not ws:
			raise RuntimeError("Agent not connected")
		await ws.send_json({"type": "open_all", "duration": duration})


setup_logging("server")
logger = logging.getLogger("server")
hub = AgentHub()
app = FastAPI(title="BAS-IP Emergency Server")


# Простейшая проверка API-ключа для REST-запросов.
# Ключ передаётся в заголовке X-API-Key. Рекомендуется хранить в переменных окружения
# и проксировать через API Gateway.
def verify_api_key(x_api_key: str = Header(default="")) -> None:
	# В реальном окружении сравнивайте с секретом из env/хранилища секретов
	EXPECTED = "CHANGE_ME_SERVER_KEY"
	if x_api_key != EXPECTED:
		raise ValueError(INVALID_API_KEY)


@app.post("/api/open_all/{site_id}")
async def open_all(site_id: str, duration: int = 10, _: None = Depends(verify_api_key)) -> JSONResponse:
	try:
		await hub.send_open_all(site_id, duration)
		logger.info("cmd=open_all site=%s duration=%s code=%s", site_id, duration, OK)
		return JSONResponse({"ok": True, "code": OK})
	except RuntimeError as exc:
		logger.warning("cmd=open_all site=%s error=%s code=%s", site_id, str(exc), WS_AGENT_NOT_CONNECTED)
		return JSONResponse({"ok": False, "error": str(exc), "code": WS_AGENT_NOT_CONNECTED}, status_code=400)
	except Exception as exc:  # noqa: BLE001
		logger.exception("cmd=open_all site=%s error=%s code=%s", site_id, str(exc), SERVER_INTERNAL_ERROR)
		return JSONResponse({"ok": False, "error": str(exc), "code": SERVER_INTERNAL_ERROR}, status_code=500)


@app.get("/health")
async def health() -> JSONResponse:
	return JSONResponse({"ok": True})


@app.websocket("/ws/agent/{site_id}")
async def agent_ws(ws: WebSocket, site_id: str) -> None:
	# Для WS ключ передаётся параметром ?key=... при подключении агента
	# (можно также использовать заголовки cookie/authorization).
	key = ws.query_params.get("key", "")
	if key != "CHANGE_ME_AGENT_KEY":
		await ws.close(code=4401)
		return
	try:
		await hub.register(site_id, ws)
		while True:
			# keep-alive; receive pings/acks optionally
			await ws.receive_text()
	except WebSocketDisconnect:
		hub.unregister(site_id)


