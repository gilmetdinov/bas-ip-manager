import nest_asyncio
from src.web.server import run_app
from src.db.init_server_db import init_server_db


nest_asyncio.apply()


CONFIG = 'server.env'


if __name__ == '__main__':
    # Инициализация БД и сид админа из того же env
    init_server_db(env_path=CONFIG)
    run_app(CONFIG)
