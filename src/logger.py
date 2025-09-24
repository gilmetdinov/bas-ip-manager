import os
import logging
from logging.handlers import RotatingFileHandler


LOG_LEVEL_DEBUG = 'debug'
LOG_LEVEL_INFO = 'info'
LOG_LEVEL_WARNING = 'warning'
LOG_LEVEL_ERROR = 'error'
LOG_LEVELS = {
	LOG_LEVEL_DEBUG: logging.DEBUG,
	LOG_LEVEL_INFO: logging.INFO,
	LOG_LEVEL_WARNING: logging.WARNING,
	LOG_LEVEL_ERROR: logging.ERROR
}


def __get_log_level(alias: str) -> int:
	return LOG_LEVELS.get(alias, LOG_LEVEL_DEBUG)


def setup_logging(component: str, log_dir: str = 'logs', level_alias: str = LOG_LEVEL_DEBUG) -> None:
	os.makedirs(log_dir, exist_ok=True)
	level = __get_log_level(level_alias)
	log_path = os.path.join(log_dir, component)
	handler = RotatingFileHandler(log_path, maxBytes=10_000_000, backupCount=5, encoding="utf-8")
	formatter = logging.Formatter(
		fmt="%(asctime)s %(levelname)s %(name)s %(message)s",
		datefmt="%Y-%m-%d %H:%M:%S",
	)
	handler.setFormatter(formatter)
	root = logging.getLogger()
	root.setLevel(level)
	root.addHandler(handler)

	# Также выводим логи в консоль, чтобы видеть события в stdout
	console = logging.StreamHandler()
	console.setLevel(level)
	console.setFormatter(formatter)
	root.addHandler(console)
