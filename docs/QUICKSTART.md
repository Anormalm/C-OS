# Quickstart (5 Minutes)

## Local Run

1. Install dependencies:
   - `pip install -e ".[dev]"`
2. Start API:
   - `uvicorn cos.app:app --reload`
3. Open:
   - API docs: `http://127.0.0.1:8000/docs`
   - UI workspace: `http://127.0.0.1:8000/`

## Docker Run

1. Copy env file:
   - `copy .env.example .env` (Windows)
2. Start stack:
   - `docker compose up --build`
3. Open:
   - UI workspace: `http://127.0.0.1:8000/`
   - Neo4j browser: `http://127.0.0.1:7474/`

## First Data Flow

1. In UI, use `Save A Thought`.
2. Ask a question in `Ask Memory`.
3. Open `Coach Mode` and request advice.

## Launch Demo Flow

1. Load sample dataset:
   - `python -m cos.experiments.load_sample_dataset`
2. Open quality dashboard in UI.
3. Run evaluation harness with Hit@3.

## One-Command Local Smoke Test

```powershell
powershell -ExecutionPolicy Bypass -File scripts/local_smoke_test.ps1
```

Optional flags:
- `-SkipInstall`
- `-SkipLint`
- `-SkipTests`
