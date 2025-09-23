import nest_asyncio
from src.web.server import run_app


nest_asyncio.apply()


CONFIG = 'server.env'


if __name__ == '__main__':
    run_app(CONFIG)
