import nest_asyncio
from src.web.agent import run_app, read_args_opts


nest_asyncio.apply()


CONFIG = 'agent.env'


if __name__ == '__main__':
    run_app(CONFIG, read_args_opts())
