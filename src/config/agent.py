from dataclasses import dataclass
import os
from .abstract import AbstractConfig
from src.logger import LOG_LEVEL_DEBUG
from .env_keys import *
from src.utilities.doors import DoorDto


@dataclass
class AgentConfig(AbstractConfig):
    log_dir: str
    log_level: str
    title: str
    port: int
    api_key: str
    api_server: str
    ws_server: str
    agent_id: str
    doors: list[DoorDto]

    def __init__(self, config_path = '.env'):
        super().__init__(config_path)
        self.log_dir = os.getenv(LOG_DIR, 'logs')
        self.log_level = os.getenv(LOG_LEVEL, LOG_LEVEL_DEBUG)
        self.title = os.getenv(TITLE, "Local Agent API")
        self.port = int(os.getenv(PORT, 8843))
        self.api_key = os.getenv(API_KEY)
        self.api_server = os.getenv(API_SERVER)
        self.ws_server = os.getenv(WS_SERVER)
        self.agent_id = os.getenv(AGENT_ID, 'default-agent')
        self.doors = []
