import nest_asyncio
from src.web.agent import run_app, read_args_opts
from src.db.init_agent_db import init_agent_db


nest_asyncio.apply()


CONFIG = 'agent.env'


if __name__ == '__main__':
    # Инициализация локальной SQLite БД агента из того же env
    init_agent_db(env_path=CONFIG)
    run_app(CONFIG, read_args_opts())
