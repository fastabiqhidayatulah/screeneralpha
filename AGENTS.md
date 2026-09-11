# AGENTS.md

## What this is
Streamlit-based Indonesian stock screener. Two Python files:
- `app_v2_realdata.py` — single-file UI + scoring logic (the entrypoint)
- `stockbit_client.py` — MCP client wrapper with file-based JSON cache

## Run
```
python -m streamlit run app_v2_realdata.py
```
Or use `run.bat` (Windows, note: hardcoded Python path `C:\Users\PMP04\AppData\Local\Python\bin\python.exe`).

## Dependencies & runtime requirements
- `pip install -r requirements.txt` (streamlit, pandas, numpy, requests, yfinance, mcp)
- **Node.js >= 22 + npx required at runtime** — `stockbit_client.py` launches `npx -y stockbit-mcp` as a subprocess via MCP stdio protocol. `stockbit-mcp@1.x` requires Node >= 22, but Streamlit Cloud's base image only ships older Node via apt. Handled by `_ensure_node()` in `stockbit_client.py`, which downloads official Node `v22.14.0` binaries into `.node-extra/` (gitignored) on first run — do not remove/replace it. First scan after cold start is slower (one-time download)
- Yahoo Finance rate limits: app adds `time.sleep(0.3)` between yfinance calls; don't remove this

## Caching
- **Streamlit cache**: `get_index_quotes` (5 min TTL), `fetch_credible_news` (15 min TTL) — use `@st.cache_data`
- **File cache**: `cache/` dir holds MD5-hashed JSON keyed by `{type}_{symbol}_{date}` — auto-created by `StockbitClient`, gitignored
- Deleting `cache/` is safe; it rebuilds on next scan

## Gotchas
- `.streamlit/secrets.toml` is gitignored — if Streamlit secrets are needed, they must be created locally
- Bare `except:` blocks throughout `app_v2_realdata.py` — errors are silently swallowed
- Stock tickers use `.JK` suffix (Yahoo Finance convention for Indonesia/IDX)
- `sys.path.insert` `app_v2_realdata.py:19` adds script dir to path for local import of `stockbit_client`
