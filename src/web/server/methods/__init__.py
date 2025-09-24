from .health import HealthMethod
from .socket import SocketMethod
from .auth import AuthMethod
from .open_all import OpenAllMethod

def init_methods(app, config, logger, manager):
    for method in [
        HealthMethod,
        SocketMethod,
        AuthMethod,
        OpenAllMethod,
    ]:
        method(app, config, logger, manager).set()
