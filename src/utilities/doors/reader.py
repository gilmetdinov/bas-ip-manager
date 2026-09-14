import os
import logging
from yaml import safe_load
from .dto import DoorDto


class DoorReadException(Exception):
    pass


class FileNotFound(DoorReadException):
    pass


class FileReadError(DoorReadException):
    pass


class EmptyConfigError(DoorReadException):
    pass


class BadConfigError(DoorReadException):
    pass


def __read_file(path: str):
    if not path or not os.path.exists(path):
        raise FileNotFound(f'Bad path provided for config file: {path}')
    try:
        data = safe_load(open(path, 'r'))
    except Exception as err:
        raise FileReadError(f'Failed to read config file: {err}')
    return data


def read_config(path: str, raw_data: dict = None) -> list[DoorDto]:
    data = raw_data if raw_data is not None and isinstance(raw_data, dict) else __read_file(path)
    panels = data.get('panels', {})
    if raw_data is None:
        del data
    if not panels:
        raise EmptyConfigError('Panel configuration not found in config file')
    elif not isinstance(panels, dict):
        raise BadConfigError(f'Bad type of panel configuration found. Expected: dict; found: {type(panels)}')
    doors = []
    for name, config in panels.items():
        try:
            if not isinstance(config, dict):
                raise TypeError('Config must be dict')
            dto = DoorDto(name, url=config.get('url'), lock_number=config.get('lock_number'), username=config.get('username'), password=config.get('password'), token=config.get('token'))
        except Exception as err:
            raise err  # more complex door reading scenarios (error only if no door processed at all? or at any door reading error?)
            continue
        doors.append(dto)
    return doors
    