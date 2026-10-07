# foodtask

Scrapes cafeteria menus (KHU, HUFS, KHU dorm) with Playwright, translates them with Gemini, generates dish images with Cloudflare AI, and stores them in Cloudflare D1.

## Setup

```sh
uv sync
uv run playwright install chromium
```

Environment variables (or a `.env` file): `GEMINI_API_KEY`, `CFACCOUNTID`, `CFDATABASEID`, `CFTOKEN` (D1), `CFAPITOKEN` (Workers AI), `STORAGE_URL`.

## Schedule

The scrapers run via GitHub Actions (`.github/workflows/crawl.yml`) every Friday at 23:05 KST, one at a time. Add the environment variables above as repository secrets. Trigger a manual run from the Actions tab with "Run workflow".

## Run locally

```sh
uv run crawler.py --source khu --campus seoul
uv run crawler.py --source hufs --student
uv run crawler.py --source dorm
```
