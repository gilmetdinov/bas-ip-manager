from .abstract import AbstractMethod
from fastapi import Body
from fastapi.responses import JSONResponse
from ..ws_manager import ConnectionManager


class OpenAllMethod(AbstractMethod, route='/open/all'):
    """REST‑эндпоинт для инициирования открытия дверей у агентов через WS.

    Тело запроса:
    {
      "duration": 3,
      "doors": [
        {"base_url": "http://localhost:8855", "static_token": "TEST_TOKEN", "lock_number": 1,
         "open_url_template": "/access/general/lock/open/remote/control/accepted/{lock}"}
      ]
    }
    """

    def __init__(self, app, config, logger, ws_manager: ConnectionManager, *args, **kwargs):
        super().__init__(app, config, logger, *args, **kwargs)
        self._ws_manager = ws_manager

    def set(self):
        @self._app.post(self._route)
        async def open_all(payload: dict = Body(default={})) -> JSONResponse:
            try:
                duration = int(payload.get("duration", 3))
                agent_id = payload.get("agent_id")  # если задан — шлём только одному агенту
                command = {"type": "open_doors", "duration": duration}
                if agent_id:
                    await self._ws_manager.send_command(agent_id, command)
                    self._log_info(f"cmd=open_all sent to agent_id={agent_id} duration={duration}")
                else:
                    await self._ws_manager.broadcast_command(command)
                    self._log_info(f"cmd=open_all broadcasted count={len(self._ws_manager.active_connections)} duration={duration}")
                return JSONResponse({"ok": True, "code": self.CODES.OK})
            except Exception as exc:  # noqa: BLE001
                self._log_error(f"cmd=open_all error={str(exc)} code={self.CODES.SERVER_INTERNAL_ERROR}", True)
                return JSONResponse({"ok": False, "error": str(exc), "code": self.CODES.SERVER_INTERNAL_ERROR}, status_code=500)


