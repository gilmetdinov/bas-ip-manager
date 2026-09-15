# BAS-IP Manager

An IoT control system for managing BAS-IP intercom / door panels over their
HTTP API. A two-component architecture: a lightweight **agent** deployed on-site
next to the panels, and a central **management server** that orchestrates agents
and exposes a REST API to end users.

## Architecture

```
┌──────────────┐          WebSocket           ┌──────────────────┐
│   agent      │ ◄──────────────────────────► │  management      │
│  (on-site)   │   auth + heartbeat + cmds    │  server          │
│              │                              │  (central)       │
│  BAS-IP REST │──► panels (unlock, status)   │  REST API ◄─ user│
└──────────────┘                              └──────────────────┘
```

- **agent** — a FastAPI web app running inside the network that can reach the
  BAS-IP panels directly. It reads panel state and can issue timed door-unlock
  commands. Connects to the management server over a stable WebSocket.
- **management server** — authenticates agents, maintains WebSocket connections,
  and broadcasts open/unlock commands to all (or selected) agents. End users talk
  to it through a REST API.
- **BAS-IP REST client** (`src/clients/basip.py`) — login, unlock and other panel
  methods.

## Stack

- Python 3.11+, FastAPI, Uvicorn, WebSocket
- PostgreSQL (server) + SQLite (agent), SQLAlchemy
- Docker Compose

## Configuration

The agent requires a path to a doors-config file describing the panels within
its network:

```yaml
panels:
  front-door:
    address: 192.168.5.6
    username: user
    password: pass
```

Copy `agent.env.example` → `.env` and `server.env.example` → `.env` and fill in
the values (all placeholders are `change-me`).

## Run

```bash
docker compose up --build
```

Or manually: `agent.py` (on-site) and `server.py` (management). A local
`mock_basip.py` FastAPI server emulates a real BAS-IP panel for development.

## Structure

```
src/
  clients/      BAS-IP REST API client
  config/       env-driven settings (agent / server)
  db/           SQLAlchemy models + init scripts (SQLite agent, Postgres server)
  security/     password hashing, local key-value store
  utilities/    doors DTO
  web/          FastAPI apps (agent, server)
agent.py        agent entry point
server.py       management entry point
mock_basip.py   mock BAS-IP panel for local dev
```

> This was a working tool for a specific deployment that didn't take off; it has
> been scrubbed of deployment specifics and credentials. Some parts (SQLite store,
> migrations) are still on the roadmap.
