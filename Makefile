.PHONY: ui

ui:
	@set -a && [ -f .env ] && . ./.env; set +a && uv run python main.py interface
