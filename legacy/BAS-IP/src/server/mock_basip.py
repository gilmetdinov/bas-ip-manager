from fastapi import FastAPI, Header
from fastapi.responses import JSONResponse


# Локальный мок BAS-IP API для отладки на одном ПК.
# Эмулирует актуальный путь из документации:
# - GET /access/general/lock/open/remote/control/accepted/{lock}

mock_app = FastAPI(title="Mock BAS-IP")


@mock_app.get("/access/general/lock/open/remote/control/accepted/{lock}")
async def open_lock(lock: int, authorization: str = Header(default="")) -> JSONResponse:
	if not authorization.startswith("Bearer "):
		return JSONResponse({"ok": False, "error": "unauthorized"}, status_code=401)
	return JSONResponse({"ok": True, "lock": lock, "event": "Lock is opened by API call"})


