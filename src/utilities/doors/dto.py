from dataclasses import dataclass

@dataclass
class DoorDto:
    name: str
    url: str
    username: str | None = None
    password: str | None = None
    token: str | None = None  # Статичный токен
    
    def __post_init__(self):
        if not self.url:
            raise AttributeError(f'URL must be set for door {self.name}')
        if self.token is None and (self.username is None or self.password is None):
            raise AttributeError(f'Either static token or username and password must be provided for door {self.name}')

