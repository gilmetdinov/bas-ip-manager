## BAS‑IP Emergency Control — руководство разработчика

Система для экстренного открытия всех дверей на объекте МЧС по нажатию кнопки. Архитектура модульная: центральный сервер (REST + WebSocket), локальный агент на площадке и SDK‑клиент BAS‑IP. Поддерживается два способа открытия: через GET‑шаблон URL (быстрый старт) и через авторизацию + POST (настраивается под прошивку).

### Основные сценарии
- Кнопка/веб‑клиент вызывает `POST /api/open_all/{site_id}` на центральном сервере.
- Сервер по постоянному WebSocket отправляет команду локальному агенту площадки `site_id`.
- Агент выполняет открытие всех дверей, обращаясь к домофонам BAS‑IP по локальной сети.

---

## Архитектура проекта
- `src/sdk/basip_client.py` — минимальный клиент BAS‑IP (авторизация, открытие замка). Поддерживает:
  - статический Bearer‑токен и GET‑шаблон URL (например, `/access/general/lock/open/remote/control/accepted/:lock-number`);
  - классическую схему: `auth_path` (POST логин) + `open_path` (POST открыть на `duration`).
- `src/panels.py` — абстракции `Panel` и `PanelManager` для работы с набором панелей.
- `src/server/app.py` — центральный сервер (FastAPI): REST триггер, WebSocket‑хаб для агентов, проверка ключей.
- `src/agent/runner.py` — локальный агент: держит WS‑соединение с сервером и открывает двери.
- `src/server/mock_basip.py` — локальный мок BAS‑IP для тестов на одном ПК.
- `src/cli.py` — простой CLI для локального открытия без сервера.
- `config.yaml` — конфигурация панелей/объектов.
- `main.py` — запуск CLI и агента.

Диаграмма взаимодействия (упрощённо):
```
Клиент (кнопка) → REST /api/open_all/{site_id} → Сервер
Сервер ⇄ WS ⇄ Агент на объекте → API панелей BAS‑IP → Открыть замки
```

---

## Требования
- Python 3.10+
- Доступ к LAN панелей с агента
- Для сервера — белый IP/домен или публикация через API‑шлюз

---

## Установка
```bash
py -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

---

## Конфигурация (`config.yaml`)
Пример с быстрым GET‑шаблоном (требуется Bearer‑токен). Согласно документации, путь: `/access/general/lock/open/remote/control/accepted/:lock-number`, где `lock-number ∈ {0,1,2}`:
```yaml
panels:
  - name: entrance-A
    base_url: "http://192.168.1.10"
    token: "PASTE_YOUR_TOKEN"
    open_url_template: "/access/general/lock/open/remote/control/accepted/:lock-number"
    lock_number: 1
  - name: entrance-B
    base_url: "http://192.168.1.11"
    token: "PASTE_YOUR_TOKEN"
    open_url_template: "/access/general/lock/open/remote/control/accepted/:lock-number"
    lock_number: 2
```

Вариант с авторизацией и POST:
```yaml
panels:
  - name: entrance-A
    base_url: "http://192.168.1.10"
    username: "admin"
    password: "secret"
    auth_path: "/api/auth/login"    # зависит от прошивки
    open_path: "/api/door/open"      # зависит от прошивки
```

Поля конфигурации панели:
- `base_url` — базовый URL панели (http/https)
- `token` — статический Bearer‑токен (если заполнен, логин не выполняется)
- `open_url_template` — GET‑шаблон URL для мгновенного открытия; поддерживает `{lock}` и `:lock-number`
- `lock_number` — номер замка для подстановки в шаблон
- `username`, `password`, `auth_path`, `open_path` — используются при варианте авторизации + POST

---

## Запуск (прямой, без сервера)
Открыть все двери непосредственно с этого компьютера:
```bash
python main.py open_all --duration 10 --config config.yaml
```
Примечание: при GET‑шаблоне `duration` игнорируется (поведение соответствует API панели).

---

## Сервер и агент
### Запуск сервера (публичный IP/порт)
```bash
uvicorn src.server.app:app --host 0.0.0.0 --port 8000
```

### Запуск агента на объекте (внутри LAN панелей)
```bash
python main.py agent --server ws://SERVER_IP:8000 --site SITE_001 --config config.yaml
```

### Локальное API на объекте (по требованию)
Запуск только REST‑API агента (без WS):
```bash
python main.py agent-api --config config.yaml --host 0.0.0.0 --port 8101
```
Вызов локально на объекте:
```bash
curl -X POST "http://AGENT_IP:8101/local/open_all?duration=10" -H "X-API-Key: CHANGE_ME_LOCAL_KEY"
```

### Вызов (кнопка/скрипт)
```bash
curl -X POST "http://SERVER_IP:8000/api/open_all/SITE_001?duration=10" -H "X-API-Key: CHANGE_ME_SERVER_KEY"
```

Пояснения:
- Сервер поддерживает WebSocket `/ws/agent/{site_id}`. Агент подключается с ключом `?key=CHANGE_ME_AGENT_KEY`.
- REST требует заголовок `X-API-Key`.

---

## Локальные тесты на одном ПК (с мок‑панелью)
1) Запустить мок BAS‑IP:
```bash
uvicorn src.server.mock_basip:mock_app --host 127.0.0.1 --port 8100
```
2) Конфиг для мока:
```yaml
panels:
  - name: mock
    base_url: "http://127.0.0.1:8100"
    token: "TEST"
    open_url_template: "/access/general/lock/open/remote/control/accepted/:lock-number"
    lock_number: 1
```
3) Запустить сервер и агента:
```bash
uvicorn src.server.app:app --host 127.0.0.1 --port 8000
python main.py agent --server ws://127.0.0.1:8000 --site TEST --config config.yaml
```
4) Триггер:
```bash
curl -X POST "http://127.0.0.1:8000/api/open_all/TEST?duration=5" -H "X-API-Key: CHANGE_ME_SERVER_KEY"
```

В ответ мок вернёт JSON: `{ "ok": true, "lock": 1, "event": "Lock is opened by API call" }`.

---

## Безопасность (минимум для запуска)
- Замените значения `CHANGE_ME_SERVER_KEY` и `CHANGE_ME_AGENT_KEY`. Храните их в переменных окружения или в хранилище секретов.
- Для локального API агента используйте `CHANGE_ME_LOCAL_KEY`.
- Используйте HTTPS на сервере (TLS). Для агента — исходящее соединение к серверу через защищённый канал (WSS).
- Разместите агента на подсети панели, ограничьте доступ ACL/VLAN, запретите входящие соединения на узел агента.
- Для реальных панелей храните `username/password/token` вне YAML (env/secret store). В логах не выводите секреты.
- Ограничьте IP‑списки на API‑шлюзе, поставьте rate‑limit и аудит запросов.
- Логи храните централизованно, применяйте ротацию и контроль доступа.

---

## Кастомизация под прошивку BAS‑IP
Если на портале BAS‑IP указаны другие пути/поля:
- Укажите `auth_path` и `open_path` в `config.yaml` (например, `/api/v1/auth`, `/api/v1/door/unlock`).
- Если требуется другое имя параметра длительности, поправьте `BASIPClient.open_lock` (параметр в payload).
- Если применяется только GET‑вызов, задайте `open_url_template` и при необходимости `lock_number`.

SDK‑клиент содержит подробные комментарии; изменения локальны и просты.

---

## Структура кода
- `src/sdk/basip_client.py` — единая точка интеграции с API панели.
- `src/panels.py` — агрегация панелей, безопасное массовое открытие (не прерывает поток из‑за одной ошибки).
- `src/server/app.py` — REST/WS, проверка ключей, минимальная обработка ошибок.
- `src/agent/runner.py` — устойчивое переподключение (бэкофф 3 сек.), приёма команд, подтверждение выполнения.
- `main.py` — сабкоманды `open_all` и `agent`.

---

## Коды ошибок
Единые коды используются в логах и ответах API.

| Код | Описание |
|-----|----------|
| `OK` | Операция выполнена успешно |
| `E100` | Неверный ключ доступа (REST/WS/LOCAL) |
| `E101` | Панель отклонила авторизацию |
| `E200` | Ошибка сети при запросе |
| `E201` | Агент не подключён к серверу |
| `E300` | Не удалось открыть замок (HTTP >= 400) |
| `E301` | Ошибка конфигурации панели |
| `E400` | Внутренняя ошибка сервера |
| `E401` | Внутренняя ошибка агента |
| `E500` | Неверные параметры запроса |
| `E000` | Неизвестная ошибка |

Ответы API включают поле `code`, а в логах фиксируются `code`, параметры вызова и текст ошибки.

---

## Частые проблемы и решения
- 401/403 при GET: проверьте `token` и заголовок `Authorization: Bearer ...`.
- 404 при GET: уточните `open_url_template` и `base_url` (включая префиксы API и номер замка).
- Таймауты: проверьте доступность панели из сети агента, брандмауэр, NAT, прокси.
- Агент не подключается к серверу: проверьте `--server` URL, порт, общий ключ `?key=...`, наличие TLS, сетевые правила.
- REST возвращает 400: сервер не видит агента (`Agent not connected`) — проверьте, что агент онлайн и `site_id` совпадает.

---

## Чек‑лист вывода в эксплуатацию
- [ ] Уникальные, ротационные ключи для REST (`X-API-Key`) и WS агента
- [ ] HTTPS/WSS и корректные сертификаты
- [ ] Секреты в vault/env, не в YAML
- [ ] Ограничения IP + rate limiting на периметре
- [ ] Мониторинг доступности агента и панелей
- [ ] Логирование событий (кто и когда открыл)
- [ ] Резервная схема ручного доступа при отказе связи

---

## Команды для разработчика (шпаргалка)
- Локальный запуск CLI (без сервера):
```bash
python main.py open_all --duration 10 --config config.yaml
```
- Сервер:
```bash
uvicorn src.server.app:app --host 0.0.0.0 --port 8000
```
- Агент:
```bash
python main.py agent --server ws://SERVER_IP:8000 --site SITE_001 --config config.yaml
```
- Мок BAS‑IP:
```bash
uvicorn src.server.mock_basip:mock_app --host 127.0.0.1 --port 8100
```

---

## Лицензия и ответственность
Исходники предоставляются «как есть». Перед интеграцией на реальных объектах убедитесь, что все требования ИБ и локальные регламенты соблюдены, а сценарии аварийного доступа проверены совместно с ответственными лицами.
Made by GDE team
## BAS-IP Emergency Door Control 

Quick utility to open all configured BAS-IP panel doors for a specified duration.

### Install

```bash
py -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

### Configure

Edit `config.yaml` and list all panels (base URL must be reachable from host running the script).

### Usage (direct CLI)

```bash
python main.py open_all --duration 10 --config config.yaml
```

### Server + Agent (for remote button)

Start server (public IP):
```bash
uvicorn src.server.app:app --host 0.0.0.0 --port 8000
```

Run local agent on site (inside LAN with panels):
```bash
python -m src.agent.runner --server ws://SERVER_IP:8000 --site SITE_ID --config config.yaml
```

Trigger from button/web client:
```bash
curl -X POST "http://SERVER_IP:8000/api/open_all/SITE_ID?duration=10" -H "X-API-Key: CHANGE_ME_SERVER_KEY"
```

### Notes

- Endpoints in `src/sdk/basip_client.py` are placeholders matching common BAS-IP Android API patterns. Update paths if your firmware differs.
- Add new features (voice/text alert) by extending the client and CLI.

### Local single-machine testing

Mock BAS-IP API:
```bash
uvicorn src.server.mock_basip:mock_app --host 127.0.0.1 --port 8100
```

Sample config for mock:
```yaml
panels:
  - name: mock
    base_url: "http://127.0.0.1:8100"
    token: "TEST"
    open_url_template: "/access/general/lock/open/remote/accepted/{lock}"
    lock_number: 1
```

Run agent and trigger:
```bash
uvicorn src.server.app:app --host 127.0.0.1 --port 8000
python main.py agent --server ws://127.0.0.1:8000 --site TEST --config config.yaml
curl -X POST "http://127.0.0.1:8000/api/open_all/TEST?duration=5" -H "X-API-Key: CHANGE_ME_SERVER_KEY"
```

### Security
- Protect server REST with `X-API-Key` (rotate and store in secrets manager).
- Protect agent WS with a pre-shared key (`?key=...`). Place agent behind outbound-only firewall rules.
- Use HTTPS for both server and panel connections; for LAN panels, restrict by VLAN/ACL.
- Avoid storing real credentials in plain YAML for production — use env vars or vault.


---

## Для балбесов(GDE team): сделай по шагам и всё заработает

1) Установи Python и зависимости
```bash
py -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

2) Открой файл `config.yaml` и вставь такой пример (локальный тест с мок‑панелью):
```yaml
panels:
  - name: mock
    base_url: "http://127.0.0.1:8100"
    token: "TEST"
    open_url_template: "/access/general/lock/open/remote/control/accepted/:lock-number"
    lock_number: 1
```

3) Запусти мок‑панель (эмулятор панели):
```bash
uvicorn src.server.mock_basip:mock_app --host 127.0.0.1 --port 8100
```

4) В другом окне запусти сервер:
```bash
uvicorn src.server.app:app --host 127.0.0.1 --port 8000
```

5) В третьем окне запусти агента (если не нужен агент — шаг пропусти):
```bash
python main.py agent --server ws://127.0.0.1:8000 --site TEST --config config.yaml
```

6) Нажми «кнопку» командой (это просто HTTP‑запрос):
```bash
Invoke-RestMethod -Method Post -Uri "http://127.0.0.1:8000/api/open_all/TEST?duration=5" -Headers @{ "X-API-Key" = "CHANGE_ME_SERVER_KEY" }
```
Если видишь `{ "ok": true }` — всё работает.

7) Самый простой способ без сервера и агента — напрямую открыть все двери по конфигу:
```bash
python main.py open_all --duration 10 --config config.yaml
```

8) Для боевого запуска на объекте:
- запусти агента на мини‑сервере в сети панелей;
- укажи реальные адреса панелей в `config.yaml`;
- поменяй ключи `CHANGE_ME_*` на свои и храни их в секретах;
- делай запросы на твой центральный сервер `POST /api/open_all/{site_id}`.

Помни: если что‑то не работает — читай логи в папке `logs/`. Там обычно написано, что именно не так и какой код ошибки.

