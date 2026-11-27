# API boundary

This package contains the production FastAPI boundary. The first slice exposes
operational endpoints without importing or initializing the existing RAG stack:

- `GET /healthz` reports whether the API process is alive.
- `GET /readyz` reports whether the current application dependencies are ready.
- `GET /api/v1/version` exposes stable application and API version metadata.
- `GET /docs` and `GET /openapi.json` expose generated API documentation.

Run the development server from the repository root:

```powershell
.\.venv\Scripts\python.exe -m uvicorn api.main:app --reload
```

The root Python modules remain the verified local CLI. Future API features will
adapt those modules behind explicit services rather than copying the CLI into a
second implementation. See [`../docs/ARCHITECTURE.md`](../docs/ARCHITECTURE.md).
