from .health import HealthMethod
from .socket import SocketMethod
from .auth import AuthMethod

def init_methods(app, config, logger, manager):
    for method in [
        HealthMethod,
        SocketMethod,
        AuthMethod,
    ]:
        method(app, config, logger, manager).set()
