from .abstract import AbstractMethod
from fastapi import Request, Body, HTTPException, Header
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from ..ws_manager import ConnectionManager
from src.db import get_postgres_engine, get_session_factory, models


class OpenAllMethod(AbstractMethod, route='/open/all'):
    """
    REST‑эндпоинт для инициирования открытия дверей у агентов через WS.
    Тело запроса:
    ```{ "duration": 600 }
    """

    def __init__(self, app, config, logger, ws_manager: ConnectionManager, *args, **kwargs):
        super().__init__(app, config, logger, *args, **kwargs)
        self._ws_manager = ws_manager
    
    def __check_api_key(self, api_key: str) -> models.User | None:
        # TODO: check api key from users
        with get_session_factory(get_postgres_engine())() as session:
            session: Session
            return session.query(models.User).filter(models.User.is_active == True, models.User.api_key == api_key).first()

    def set(self):
        @self._app.post(self._route)
        async def open_all(payload: dict = Body(default={}), x_api_key: str | None = Header(default=None, alias='x-api-key')) -> JSONResponse:
            if not x_api_key:
                raise HTTPException(401, "Missing api key")
            user = self.__check_api_key(x_api_key)
            if user is None:
                raise HTTPException(401, "Bad api key") 
            try:
                duration = int(payload.get("duration", 600))
                agent_id = payload.get("agent_id")  # если задан — шлём только одному агенту
                command = {"type": "open_doors", "duration": duration}
                if agent_id:
                    await self._ws_manager.send_command(agent_id, command)
                    self._log_info(f"cmd=open_all sent to agent_id={agent_id} duration={duration} | initiated by {user.email} [{user.id}]")
                else:
                    await self._ws_manager.broadcast_command(command)
                    self._log_info(f"cmd=open_all broadcasted count={len(self._ws_manager.active_connections)} duration={duration} | initiated by {user.email} [{user.id}]")
                return JSONResponse({"ok": True, "code": self.CODES.OK})
            except Exception as exc:  # noqa: BLE001
                self._log_error(f"cmd=open_all error={str(exc)} code={self.CODES.SERVER_INTERNAL_ERROR} | initiated by {user.email} [{user.id}]", True)
                return JSONResponse({"ok": False, "error": str(exc), "code": self.CODES.SERVER_INTERNAL_ERROR}, status_code=500)


