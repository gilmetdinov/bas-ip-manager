from .health import HealthMethod
from .open_all import OpenAllMethod


def init_methods(app, config, logger):
    for method in [
        HealthMethod,
        OpenAllMethod
    ]:
        method(app, config, logger).set()
