import sys
import logging
from fastapi import FastAPI
import uvicorn
from src.logger import setup_logging
from src.config import AgentConfig
from src.clients import BASIPClient
from src.utilities.doors import read_config
from .methods import init_methods
from . import create_lifespan


COMPONENT_NAME = 'agent'
PANEL_CONFIG_KEY = 'panel_config'


def read_args_opts():
    args = sys.argv[1:]
    if len(args) < 1:
        raise ValueError('Необходимо заполнить путь до конфигурации дверных панелей')
    panel_config = args[0]
    if not panel_config:
        raise ValueError('Необходимо заполнить путь до конфигурации дверных панелей')
    return {
		PANEL_CONFIG_KEY: panel_config
	}

def run_app(config_path: str = '.env', args_opts: dict = {}):    
    # конфигурация + логгирование
	config = AgentConfig(config_path)
	setup_logging(COMPONENT_NAME, config.log_dir, config.log_level)
	logger = logging.getLogger(COMPONENT_NAME)
 
	# чтение конфигурации дверных панелей
	config.doors = read_config(args_opts.get(PANEL_CONFIG_KEY))
	# Передаём фабрику BASIPClient внутрь lifespan → WebSocketClient
	app = FastAPI(title=config.title, lifespan=create_lifespan(config, logger, BASIPClient))
	init_methods(app, config, logger)
	uvicorn.run(app, host='0.0.0.0', port=config.port)