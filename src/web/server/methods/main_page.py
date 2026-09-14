from .abstract import AbstractMethod
from fastapi import FastAPI, Request, Form, Body, HTTPException
from fastapi.responses import JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sqlalchemy import select
from sqlalchemy.orm import Session
import aiohttp
from src.db import get_postgres_engine, get_session_factory, models
from src.security import verify_password


class MainPageMethod(AbstractMethod, route='/panel'):
    MAIN_PAGE_TEMPLATE = 'main-page.html.j2'
    
    def __init__(self, app, config, logger, *args, **kwargs):
        super().__init__(app, config, logger, *args, **kwargs)
        self.__templates = Jinja2Templates(directory=self._config.templates_dir)
    
    def __find_user(self, email: str):
        with get_session_factory(get_postgres_engine())() as session:
            session: Session
            user = session.scalar(select(models.User).where(models.User.is_active == True, models.User.email == email))
            return user
    
    def set(self):
        @self._app.get(self._route)
        async def get_form(request: Request):
            return self.__templates.TemplateResponse(self.MAIN_PAGE_TEMPLATE, {"request": request, 'title': self._config.title})
        
        @self._app.post('/ajax/process')
        async def process(request: Request, data: dict = Body(default={})):
            if request.headers.get('X-Requested-With') != 'XMLHttpRequest':
                raise HTTPException(400, 'Only AJAX requests allowed')
            email = data.get('email')
            password = data.get('password')
            if not email or not password:
                raise HTTPException(400, 'Логин и пароль обязательны для заполнения')
            user = self.__find_user(email)
            if not user or not verify_password(password, user.password_hash):
                raise HTTPException(403, "Некорректные данные")
            # продолжаем отсюда
            try:
                async with aiohttp.ClientSession(f'http://localhost:{self._config.port}', headers={'x-api-key': user.api_key}) as session:
                    async with session.post('/open/all', timeout=aiohttp.ClientTimeout(10)) as response:
                        response.raise_for_status()
                        result = await response.json()
                        if result.get('ok'):
                            self._log_info(f"User {user.email} [{user.id}] successfully initiated door opening")
                            return JSONResponse({"sucess": True, "message": "Команда успешно отправлена!"})
                        else:
                            self._log_error(f'Failed to initiate door opening for user {user.email} [{user.id}]: {result.get("error", "Unkonwn error")}')
            except aiohttp.ClientResponseError as e:
                self._log_error(f"HTTP error while opening doors for user {user.email} [{user.id}]: {e.status}")
                return JSONResponse({"success": False, "message": f"Ошибка сервера: {e.status}"})
            except aiohttp.ClientError as e:
                self._log_error(f"Connection error opening doors for user {user.email} [{user.id}]: {str(e)}")
                return JSONResponse({"success": False, "message": f"Ошибка соединения: {str(e)}"})
            except Exception as e:
                self._log_error(f"Unexpected error opening doors for user {user.email} [{user.id}]: {str(e)}")
                return JSONResponse({"success": False, "message": f"Непредвиденная ошибка: {str(e)}"})

