import websockets
import logging
from src.config import AgentConfig
import asyncio
import json
from contextlib import asynccontextmanager
import aiohttp
from src.clients import BASIPClient
from src.utilities.doors import DoorDto
from typing import Callable, Optional

class WebSocketClient:
    def __init__(self, config: AgentConfig, logger: logging.Logger, client_factory: Optional[Callable[..., BASIPClient]] = None):
        # Добавляем agent_id в query, чтобы сервер различал подключения
        self.controller_url = f'{config.ws_server}/ws/agent?agent_id={config.agent_id}'
        self.websocket = None
        self.reconnect_interval = 5
        self.running = True
        self.logger = logger
        # Фабрика BAS-IP клиента (можно заменить на мок/другую реализацию)
        self.client_factory: Callable[..., BASIPClient] = client_factory or BASIPClient
        self.__config = config

    async def connect_to_controller(self):
        """Подключение к контроллеру с автопереподключением"""
        while self.running:
            try:
                self.logger.info(f"Подключаюсь к контроллеру...")

                async with websockets.connect(self.controller_url) as websocket:
                    self.websocket = websocket
                    self.logger.info(f"Успешно подключился к контроллеру!")

                    # Слушаем команды от контроллера
                    async for message in websocket:
                        await self.handle_command(message)

            except websockets.exceptions.ConnectionClosed:
                self.logger.warning(f"Соединение закрыто контроллером")
            except Exception as e:
                self.logger.error(f"Ошибка подключения: {e}")

        if self.running:
            self.logger.info(f"Переподключение через {self.reconnect_interval} секунд...")
            await asyncio.sleep(self.reconnect_interval)

    async def auth_management(self, api_key: str, api_server: str):
        """Неблокирующая попытка аутентификации на management сервере.

        Отправляет POST /auth/agent с заголовком x-api-key. Лишь логируем результат.
        """
        url = f"{api_server}/auth/agent"
        try:
            timeout = aiohttp.ClientTimeout(total=5)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(url, headers={'x-api-key': api_key}) as resp:
                    ok = resp.status < 400
                    self.logger.info(f"Аутентификация агента: status={resp.status} ok={ok}")
        except Exception as e:  # noqa: BLE001
            self.logger.warning(f"Аутентификация агента не удалась: {e}")

    async def handle_command(self, message):
        """Обработка команды от контроллера"""
        try:
            command = json.loads(message)
            command_type = command.get('type')

            self.logger.info(f"Получил команду: {command}")

            # Обрабатываем разные типы команд
            if command_type == 'health_check':
                result = await self.handle_health_check(command)
            elif command_type == 'restart_service':
                result = await self.handle_restart_service(command)
            elif command_type == 'deploy':
                result = await self.handle_deploy(command)
            elif command_type == 'open_doors':
                result = await self.handle_open_doors(command)
            else:
                result = await self.handle_unknown_command(command)

            # Отправляем результат обратно контроллеру
            response = {
            'type': 'command_result',
            'original_command': command,
            'result': result,
            'timestamp': asyncio.get_event_loop().time()
            }

            if self.websocket:
                await self.websocket.send(json.dumps(response))

        except json.JSONDecodeError:
            self.logger.error(f"Нечитаемая команда: {message}")
        except Exception as e:
            self.logger.error(f"Ошибка обработки команды: {e}")

    async def handle_health_check(self, command):
        """Обработка health check команды"""
        return {
        'status': 'healthy',
        'message': f'Health check successful!',
        'uptime': asyncio.get_event_loop().time()
        }

    async def handle_open_doors(self, command):
        """Открытие всех переданных дверей через BASIPClient.

        Формат команды:
        {
          "type": "open_doors",
          "duration": 3
        }
        """
        duration = int(command.get('duration', 3))
        
        loop = asyncio.get_event_loop()
        results = []

        def _open_one(dto: DoorDto) -> dict:
            try:
                client = self.client_factory(
                    base_url=dto.url,
                    lock_number=dto.lock_number,
                    username=dto.username,
                    password=dto.password,
                    # auth_path=door_cfg.get('auth_path', '/api/auth/login'),
                    # open_path=door_cfg.get('open_path', '/api/door/open'),
                    # open_url_template=door_cfg.get('open_url_template', ''),
                    # lock_number=int(door_cfg.get('lock_number', 1)),
                    static_token=dto.token,
                )
                client.open_lock(duration)
                return {"ok": True, "base_url": client.base_url}
            except Exception as exc:  # noqa: BLE001
                return {"ok": False, "error": str(exc), "base_url": dto.url}

        # Выполняем запросы в пуле потоков, чтобы не блокировать event loop
        tasks = [loop.run_in_executor(None, _open_one, door) for door in self.__config.doors]
        if tasks:
            done = await asyncio.gather(*tasks, return_exceptions=False)
            results.extend(done)

        success_count = len([r for r in results if r.get('ok')])
        fail = [r for r in results if not r.get('ok')]
        if fail:
            self.logger.warning(f"Открытие дверей: успехов={success_count} ошибок={len(fail)} детали={fail}")
        else:
            self.logger.info(f"Открытие дверей: успехов={success_count} ошибок=0")

        return {"status": "completed", "success": success_count, "failed": fail}

    async def handle_unknown_command(self, command):
        """Обработка неизвестной команды"""
        return {
        'status': 'error',
        'message': f'Unknown command: {command.get("type", "unknown")}'
        }

    def stop(self):
        """Остановка клиента"""
        self.running = False

def create_lifespan(config: AgentConfig, logger: logging.Logger, client_factory=None):
    @asynccontextmanager
    async def lifespan(app):
        ws_client = WebSocketClient(config, logger, client_factory)
        # Запуск веб-сокет клиента при старте приложения
        # 1) Пытаемся аутентифицироваться на management (не блокируем старт)
        if config.api_key and config.api_server:
            asyncio.create_task(ws_client.auth_management(config.api_key, config.api_server))
        # 2) Запускаем веб‑сокет клиент
        task = asyncio.create_task(ws_client.connect_to_controller())
        logger.info(f"WebSocket клиент запущен")
        yield
        # Остановка при завершении
        ws_client.stop()
        task.cancel()
        logger.info(f"WebSocket клиент остановлен")
    
    return lifespan
        
