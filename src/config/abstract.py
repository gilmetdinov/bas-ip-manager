from abc import ABC, abstractmethod
from dotenv import load_dotenv


class AbstractConfig(ABC):
    @abstractmethod
    def __init__(self, config_path = '.env'):
        try:
            load_dotenv(config_path)
        except Exception:
            pass  # TODO: log
