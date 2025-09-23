from .health import HealthMethod
from .socket import SocketMethod

def init_methods(app, config, logger, manager):
    for method in [
        HealthMethod,
        SocketMethod
    ]:
        method(app, config, logger, manager).set()
