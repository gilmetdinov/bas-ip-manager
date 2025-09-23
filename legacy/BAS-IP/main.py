import argparse
from pathlib import Path

from src.cli import run_cli


def main() -> None:
	parser = argparse.ArgumentParser(description="BAS-IP emergency door control")
	sub = parser.add_subparsers(dest="cmd", required=True)

	open_cmd = sub.add_parser("open_all", help="Open all doors for duration")
	open_cmd.add_argument("--config", dest="config_path", default=str(Path("config.yaml")), help="Path to config file")
	open_cmd.add_argument("--duration", dest="duration", type=int, default=10, help="Open duration in seconds")

	agent_cmd = sub.add_parser("agent", help="Run local agent with WS")
	agent_cmd.add_argument("--server", required=True, help="Server base WS url, e.g. ws://SERVER:8000")
	agent_cmd.add_argument("--site", required=True, help="Site identifier")
	agent_cmd.add_argument("--config", dest="config_path", default=str(Path("config.yaml")), help="Path to config file")

	lapi_cmd = sub.add_parser("agent-api", help="Run local agent REST API only")
	lapi_cmd.add_argument("--config", dest="config_path", default=str(Path("config.yaml")), help="Path to config file")
	lapi_cmd.add_argument("--host", default="0.0.0.0")
	lapi_cmd.add_argument("--port", type=int, default=8101)

	args = parser.parse_args()

	if args.cmd == "open_all":
		run_cli(action="open_all", config_path=args.config_path, duration=args.duration)
	elif args.cmd == "agent":
		from src.agent.runner import run_agent
		import asyncio
		asyncio.run(run_agent(server_ws_url=args.server, site_id=args.site, config_path=args.config_path))
	elif args.cmd == "agent-api":
		import uvicorn
		from src.agent.api import create_local_agent_app
		uvicorn.run(create_local_agent_app(args.config_path), host=args.host, port=args.port)
	else:
		raise SystemExit(2)


if __name__ == "__main__":
	main()

