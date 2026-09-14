import logging
from fastapi import Depends, FastAPI, Header
from fastapi.responses import JSONResponse
from src.error_codes import OK, INVALID_API_KEY, AGENT_INTERNAL_ERROR
from src.logging_setup import setup_logging

from src.config import load_config
from src.panels import PanelManager


def verify_local_key(x_api_key: str = Header(default="")) -> None:
	if x_api_key != "CHANGE_ME_LOCAL_KEY":
		raise ValueError(INVALID_API_KEY)


def create_local_agent_app(config_path: str) -> FastAPI:
	setup_logging("agent")
	logger = logging.getLogger("agent")
	app = FastAPI(title="Local Agent API")
	config = load_config(config_path)
	manager = PanelManager.from_config(config)

	@app.get("/health")
	async def health() -> JSONResponse:
		return JSONResponse({"ok": True, "code": OK})

	@app.post("/local/open_all")
	async def open_all(duration: int = 10, _: None = Depends(verify_local_key)) -> JSONResponse:
		try:
			manager.open_all_doors(duration_seconds=duration)
			logger.info("cmd=open_all_local duration=%s code=%s", duration, OK)
			return JSONResponse({"ok": True, "code": OK})
		except Exception as exc:  # noqa: BLE001
			logger.exception("cmd=open_all_local error=%s code=%s", str(exc), AGENT_INTERNAL_ERROR)
			return JSONResponse({"ok": False, "error": str(exc), "code": AGENT_INTERNAL_ERROR}, status_code=500)

	return app


