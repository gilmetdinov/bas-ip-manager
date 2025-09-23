from .abstract import AbstractMethod
from fastapi.responses import JSONResponse


class HealthMethod(AbstractMethod, route='/health'):
    def set(self):
        @self._app.get(self._route)
        async def health() -> JSONResponse:
            return JSONResponse({"ok": True, "code": self.CODES.OK})