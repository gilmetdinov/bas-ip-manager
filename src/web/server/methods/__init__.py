from .health import HealthMethod
from .socket import SocketMethod
from .auth import AuthMethod
from .open_all import OpenAllMethod
from .main_page import MainPageMethod

def init_methods(app, config, logger, manager):
    for method in [
        HealthMethod,
        SocketMethod,
        AuthMethod,
        OpenAllMethod,
        MainPageMethod
    ]:
        method(app, config, logger, manager).set()
