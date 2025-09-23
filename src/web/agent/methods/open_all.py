from .abstract import AbstractMethod
from fastapi import Depends, Header
from fastapi.responses import JSONResponse


class OpenAllMethod(AbstractMethod, route='/open/all'):
    def __verify_local_key(self, x_api_key: str = Header(default="")) -> None:
        if x_api_key != self._config.api_key:
            raise ValueError(self.CODES.INVALID_API_KEY)

    def set(self):
        @self._app.post(self._route)
        async def open_all(duration: int = 10, _: None = Depends(self.__verify_local_key)) -> JSONResponse:
            try:
                # manager.open_all_doors(duration_seconds=duration)  # TODO
                self._log_info(f"cmd=open_all_local duration={duration} code={self.CODES.OK}")
                return JSONResponse({"ok": True, "code": self.CODES.OK})
            except Exception as exc:  # noqa: BLE001
                self._log_error(f"cmd=open_all_local error={str(exc)} code={self.CODES.AGENT_INTERNAL_ERROR}", True)
                return JSONResponse({"ok": False, "error": str(exc), "code": self.CODES.AGENT_INTERNAL_ERROR}, status_code=500)