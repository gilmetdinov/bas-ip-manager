from fastapi import WebSocket
import logging
import json


class ConnectionManager:
    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.active_connections: dict[str, WebSocket] = {}
    
    async def connect(self, websocket: WebSocket, agent_id: str = 'unknown'):
        await websocket.accept()
        self.active_connections[agent_id] = websocket
        self.logger.info(f"[КОНТРОЛЛЕР] Агент {agent_id} подключился! Всего: {len(self.active_connections)}")
    
    def disconnect(self, agent_id: str | None = None):
        if agent_id:
            if agent_id in self.active_connections:
                del self.active_connections[agent_id]
        else:
            # Удаляем все зависшие соединения
            self.active_connections = {k: v for k, v in self.active_connections.items() if v.client_state.name == 'CONNECTED'}
        self.logger.info(f"[КОНТРОЛЛЕР] Отключение. Активных: {len(self.active_connections)}")
    
    async def send_command(self, agent_id: str, command: dict) -> bool:
        ws = self.active_connections.get(agent_id)
        if not ws:
            self.logger.warning(f"[КОНТРОЛЛЕР] Агент {agent_id} не найден")
            return False
        try:
            await ws.send_text(json.dumps(command))
            self.logger.info(f"[КОНТРОЛЛЕР] Команда отправлена агенту {agent_id}: {command}")
            return True
        except Exception as e:
            self.logger.error(f"[КОНТРОЛЛЕР] Ошибка отправки агенту {agent_id}: {e}")
            self.disconnect(agent_id)
            return False
    
    async def broadcast_command(self, command: dict):
        """Шлем команду всем подключенным агентам"""
        disconnected: list[str] = []
        for agent_id, websocket in self.active_connections.items():
            try:
                await websocket.send_text(json.dumps(command))
                self.logger.info(f"[КОНТРОЛЛЕР] Команда отправлена агенту {agent_id}: {command}")
            except Exception as e:
                self.logger.error(f"[КОНТРОЛЛЕР] Ошибка отправки агенту {agent_id}: {e}")
                disconnected.append(agent_id)
        if disconnected:
            for a in disconnected:
                self.disconnect(a)
