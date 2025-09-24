from fastapi import FastAPI
from src.logger import setup_logging
from src.config import AgentConfig
import logging
from .methods import init_methods
import uvicorn
from . import create_lifespan
from src.clients import BASIPClient


COMPONENT_NAME = 'agent'


def run_app(config_path: str = '.env'):
	config = AgentConfig(config_path)
	setup_logging(COMPONENT_NAME, config.log_dir, config.log_level)
	logger = logging.getLogger(COMPONENT_NAME)
	# Передаём фабрику BASIPClient внутрь lifespan → WebSocketClient
	app = FastAPI(title=config.title, lifespan=create_lifespan(config, logger, BASIPClient))
	# TODO: reading doors config
	# config = load_config(config_path)
	# manager = PanelManager.from_config(config)
	init_methods(app, config, logger)
	uvicorn.run(app, host='0.0.0.0', port=config.port)