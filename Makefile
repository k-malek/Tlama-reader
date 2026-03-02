.PHONY: ui export-excluded game promo best-deals

ui:
	@set -a && [ -f .env ] && . ./.env; set +a && uv run python main.py interface

export-excluded:
	@set -a && [ -f .env ] && . ./.env; set +a && uv run python main.py export-excluded

game:
	@if [ -z "$(URL)" ]; then echo "Usage: make game URL=\"https://www.tlamagames.com/...\""; exit 1; fi
	@set -a && [ -f .env ] && . ./.env; set +a && uv run python main.py game "$(URL)"

promo:
	@set -a && [ -f .env ] && . ./.env; set +a && uv run python main.py promo

best-deals:
	@set -a && [ -f .env ] && . ./.env; set +a && uv run python main.py best-deals
