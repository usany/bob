# foodtask

Scrapes cafeteria menus (KHU, HUFS, KHU dorm) with Playwright, translates them with Gemini, generates dish images with Cloudflare AI, and stores them in Cloudflare D1.

## Setup

```sh
uv sync
uv run playwright install chromium
```

Environment variables (or a `.env` file): `GEMINI_API_KEY`, `CFACCOUNTID`, `CFDATABASEID`, `CFTOKEN` (D1), `CFAPITOKEN` (Workers AI), `STORAGE_URL`.

## Run

```sh
uv run scheduler.py                                # cron: every Friday 23:05–23:25 KST
uv run crawler.py --source khu --campus seoul      # one-off run
uv run crawler.py --source hufs --student
uv run crawler.py --source dorm
```
