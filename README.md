# COGNITIVE OS (C-OS)

C-OS is a persistent cognitive memory system that tracks how ideas evolve over time.

It is built to model:
- ideas
- knowledge
- time
- contradictions
- evolution of thought

## What It Provides

- Temporal reified graph memory (`valid_from`, `valid_to`, `ingestion_time`).
- Hybrid retrieval (vector candidates + graph context + dynamic re-ranking).
- Contradiction-aware versioning (conflicts are tracked, not deleted).
- Non-technical web UI with memory query and coach guidance.
- API-first architecture for integration into other products.

## 5-Minute Quickstart

### Local

```bash
pip install -e ".[dev]"
uvicorn cos.app:app --reload
```

Open:
- UI workspace: `http://127.0.0.1:8000/`
- API docs: `http://127.0.0.1:8000/docs`

### Docker

```bash
docker compose up --build
```

Open:
- UI workspace: `http://127.0.0.1:8000/`
- Neo4j browser: `http://127.0.0.1:7474/`

More setup detail: [QUICKSTART.md](docs/QUICKSTART.md)

## Architecture

See full diagram and layer breakdown in [ARCHITECTURE.md](docs/ARCHITECTURE.md).

Core model:
- `EntityNode`
- `StatementNode` (reified fact with provenance/confidence and bi-temporal fields)

## Non-Technical User Flow

At `http://127.0.0.1:8000/`:

1. `Save A Thought`
2. `Ask Memory`
3. `What Was True On Date`
4. `Coach Mode` for practical next-step advice

## API Highlights

- `POST /ingest/text`
- `POST /query/retrieve`
- `POST /query/temporal`
- `GET /insights/summary`
- `POST /coach/advice`
- `POST /coach/checkin`
- `GET /coach/personas`

## Evaluation And Benchmarks

Benchmark notes: [EVALUATION.md](docs/EVALUATION.md)

Run retrieval benchmark:

```bash
python -m cos.experiments.benchmark_retrieval
```

## Publishability Checklist Included

- MIT license
- security policy
- contributing guide
- code of conduct
- changelog
- CI (`ruff`, unit tests, API smoke tests)
- Dockerfile + docker-compose

## Repository Layout

```
/cos
  /ingestion
  /extraction
  /graph
  /vector
  /resolution
  /temporal
  /inference
  /ui
  /configs
  /experiments
```
