# AgenCart Customer Agent

This folder is a self-contained customer-agent service. It serves the web UI
and its API from one FastAPI process; no separate frontend HTTP server is
needed.

## Run

From this directory:

```powershell
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m app
```

Open http://127.0.0.1:8100/.

The service expects these values in `.env`:

```env
GROQ_API_KEY=...
MERCHANT_API_URL=http://localhost:8000
```

The browser login calls the merchant's existing `/auth/login` endpoint. The
customer-agent service keeps the returned JWT in a process-local session,
then repeats UCP profile discovery and authenticated MCP tool discovery for
each chat request. The JWT and Groq key are never sent to the browser.

Use `/health` for a simple evaluator readiness check.
