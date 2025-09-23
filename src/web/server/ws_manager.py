from fastapi import WebSocket
import logging
import json


class ConnectionManager:
    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.active_connections: dict[str, WebSocket] = {}
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections['1'] = websocket
        self.logger.info(f"[КОНТРОЛЛЕР] Сервак подключился! Всего: {len(self.active_connections)}")
    
    def disconnect(self):
        if '1' in self.active_connections:
            del self.active_connections['1']
            self.logger.info(f"[КОНТРОЛЛЕР] Сервак отвалился! Осталось: {len(self.active_connections)}")
    
    async def send_command(self, command: dict):
        if '1' in self.active_connections:
            try:
                await self.active_connections['1'].send_text(json.dumps(command))
                self.logger.info(f"[КОНТРОЛЛЕР] Команда отправлена: {command}")
                return True
            except Exception as e:
                self.logger.error(f"[КОНТРОЛЛЕР] Ошибка отправки команды: {e}")
                self.disconnect()
                return False
        return False
    
    async def broadcast_command(self, command: dict):
        """Шлем команду всем подключенным серверам"""
        disconnected = []
        for server_id, websocket in self.active_connections.items():
            try:
                await websocket.send_text(json.dumps(command))
                self.logger.info(f"[КОНТРОЛЛЕР] Команда отправлена: {command}")
            except Exception as e:
                self.logger.error(f"[КОНТРОЛЛЕР] Ошибка отправки команды: {e}")
                disconnected.append(server_id)
        
        # Чистим отваливающиеся подключения
        if disconnected:
            self.disconnect()
