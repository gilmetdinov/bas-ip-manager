from abc import ABC, abstractmethod
from fastapi import FastAPI
from src.web import Codes
from src.config import AgentConfig
import logging


class AbstractMethod(ABC):
    CODES = Codes

    def __init_subclass__(cls, **kwargs):
        cls._route: str = kwargs.get('route')
        if not cls._route:
            raise AttributeError(f"Route must be set for Method class {cls.__name__}")
        return super().__init_subclass__()

    def __init__(self, app: FastAPI, config: AgentConfig, logger: logging.Logger):
        self._app = app
        self._config = config
        self._logger = logger
        super().__init__()
    
    def _log_info(self, msg: str):
        self._logger.info(msg)
    
    def _log_warn(self, msg: str):
        self._logger.warning(msg)
    
    def _log_error(self, msg: str, as_exception=False):
        self._logger.exception(msg) if as_exception else self._logger.error(msg)
    
    def _log_debug(self, msg: str):
        self._logger.debug(msg)
    
    @abstractmethod
    def set(self):
        pass
