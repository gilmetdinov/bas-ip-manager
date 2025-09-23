from dataclasses import dataclass
import os
from .abstract import AbstractConfig
from src.logger import LOG_LEVEL_DEBUG
from .env_keys import *


@dataclass
class ServerConfig(AbstractConfig):
    log_dir: str
    log_level: str
    title: str
    port: int
    api_key: str

    def __init__(self, config_path = '.env'):
        super().__init__(config_path)
        self.log_dir = os.getenv(LOG_DIR, 'logs')
        self.log_level = os.getenv(LOG_LEVEL, LOG_LEVEL_DEBUG)
        self.title = os.getenv(TITLE, "Local Agent API")
        self.port = int(os.getenv(PORT, 8843))
        self.api_key = os.getenv(API_KEY)
