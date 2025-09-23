import asyncio
import logging
from contextlib import asynccontextmanager
from .ws_manager import ConnectionManager


async def periodic_command_sender(manager: ConnectionManager):
    """Фоновая задача для периодической отправки команд"""
    while True:
        await asyncio.sleep(15)  # Каждые 15 секунд
        if manager.active_connections:
            command = {
                'type': 'health_check',
                'timestamp': asyncio.get_event_loop().time(),
                'message': 'Как дела, братишки?'
            }
            await manager.broadcast_command(command)


def create_lifespan(logger: logging.Logger, ws_manager: ConnectionManager):
    @asynccontextmanager
    async def lifespan(app):
        # Запуск фоновой задачи для периодической отправки команд
        task = asyncio.create_task(periodic_command_sender(ws_manager))
        logger.info("[КОНТРОЛЛЕР] Фоновая задача запущена")
        yield
        # Завершение
        task.cancel()
        logger.info("[КОНТРОЛЛЕР] Фоновая задача остановлена")
    
    return lifespan
