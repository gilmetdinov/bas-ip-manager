import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path


def setup_logging(component: str, log_dir: str = "logs", level: int = logging.INFO) -> None:
	Path(log_dir).mkdir(parents=True, exist_ok=True)
	log_path = Path(log_dir) / f"{component}.log"
	handler = RotatingFileHandler(log_path, maxBytes=2_000_000, backupCount=5, encoding="utf-8")
	formatter = logging.Formatter(
		fmt="%(asctime)s %(levelname)s %(name)s %(message)s",
		datefmt="%Y-%m-%d %H:%M:%S",
	)
	handler.setFormatter(formatter)
	root = logging.getLogger()
	root.setLevel(level)
	root.addHandler(handler)


