import nest_asyncio
from src.web.agent import run_app


nest_asyncio.apply()


CONFIG = 'agent.env'


if __name__ == '__main__':
    run_app(CONFIG)
