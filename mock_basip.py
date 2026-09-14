from fastapi import FastAPI, Header
from fastapi.responses import JSONResponse
import uvicorn


# Мок (mock) — это упрощённый тестовый сервер, имитирующий ответы
# реального BAS‑IP устройства. Он позволяет локально проверить
# наш REST‑клиент без доступа к настоящей панели.

app = FastAPI(title="Mock BAS-IP")


@app.get("/login")
async def login() -> JSONResponse:
    """Имитация логина на BAS‑IP: возвращаем фейковый токен."""
    return JSONResponse({"access_token": "TEST_TOKEN"})


@app.get("/access/general/lock/open/remote/accepted/{lock}")
async def open_lock_get(lock: int, authorization: str = Header(default="")) -> JSONResponse:
    """Имитация открытия замка по GET‑шаблону пути.

    Требует заголовок Authorization: Bearer <TOKEN>.
    """
    if not authorization.startswith("Bearer "):
        return JSONResponse({"ok": False, "error": "unauthorized"}, status_code=401)
    return JSONResponse({"ok": True, "lock": lock, "event": "Lock is opened by API call (GET)"})


@app.post("/access/general/lock/open/emergency")
async def open_lock_post(authorization: str = Header(default="")) -> JSONResponse:
    """Имитация открытия замка по POST (альтернативный вариант)."""
    if not authorization.startswith("Bearer "):
        return JSONResponse({"ok": False, "error": "unauthorized"}, status_code=401)
    return JSONResponse({"ok": True, "event": "Lock is opened by API call (POST)"})


if __name__ == "__main__":
    # По умолчанию поднимаем мок на 8855
    uvicorn.run(app, host="0.0.0.0", port=8855)


