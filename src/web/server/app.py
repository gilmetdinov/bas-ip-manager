import uvicorn
from fastapi import FastAPI
from src.config import ServerConfig
from src.logger import setup_logging
import logging
from .methods import init_methods
from .ws_manager import ConnectionManager
from . import create_lifespan


COMPONENT_NAME = 'server'


def run_app(config_path: str = '.env'):
    config = ServerConfig(config_path)
    setup_logging(COMPONENT_NAME, config.log_dir, config.log_level)
    logger = logging.getLogger(COMPONENT_NAME)
    manager = ConnectionManager(logger)
    app = FastAPI(title=config.title, lifespan=create_lifespan(logger, manager))
    init_methods(app, config, logger, manager)
    uvicorn.run(app, host='0.0.0.0', port=config.port)
