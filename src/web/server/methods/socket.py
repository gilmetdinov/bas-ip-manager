from .abstract import AbstractMethod
from fastapi import WebSocket, WebSocketDisconnect
from ..ws_manager import ConnectionManager
import json


class SocketMethod(AbstractMethod, route='/ws/1'):
    def __init__(self, app, config, logger, ws_manager: ConnectionManager, *args, **kwargs):
        super().__init__(app, config, logger, *args, **kwargs)
        self._ws_manager = ws_manager

    def set(self):
        @self._app.websocket(self._route)
        async def ws_endpoint(websocket: WebSocket):
            await self._ws_manager.connect(websocket)
            try:
                while True:
                    data = await websocket.receive_text()
                    response = json.loads(data)
                    self._logger.info(f"[КОНТРОЛЛЕР] Ответ от сервера: {response}")
            except WebSocketDisconnect:
                self._ws_manager.disconnect()
            except Exception as e:
                self._logger.error(f"[КОНТРОЛЛЕР] Ошибка веб-сокета : {e}")
                self._ws_manager.disconnect()