# COGNITIVE OS (C-OS)

C-OS is a persistent, evolving cognitive memory system designed to model:
- ideas
- knowledge
- time
- contradictions
- evolution of thought

This repository provides a production-ready foundation with:
- modular pipeline layers (`ingestion`, `extraction`, `graph`, `vector`, `resolution`, `temporal`, `inference`, `ui`)
- reified, bi-temporal graph schema
- hybrid retrieval (vector + graph + dynamic re-ranking)
- contradiction-aware versioning (never delete conflicting facts)
- API surface for ingestion, temporal queries, retrieval, and analytics

## Architecture

```
Input -> Ingestion -> Extraction -> Resolution -> Graph/Vector Memory
      -> Temporal Reasoning -> Inference -> API/UI
```

Core data model:
- `EntityNode`
- `StatementNode` (reified facts with `valid_from`, `valid_to`, `ingestion_time`, `confidence`, `source`)

## Quick Start

1. Install:

```bash
pip install -e ".[dev]"
```

2. Run API:

```bash
uvicorn cos.app:app --reload
```

3. Open docs:
- http://127.0.0.1:8000/docs
- Non-technical workspace: http://127.0.0.1:8000/

## Non-Technical Usage

Open `http://127.0.0.1:8000/` and use:
- `Save A Thought`: paste notes in plain language
- `Ask Memory`: ask natural-language questions
- `What Was True On Date`: query memory at a specific time
- `Insight Panel`: see recurring themes and abandoned ideas
- `Coach Mode`: receive concrete next steps with priorities and evidence

## API Highlights

- `POST /ingest/text` ingest raw text with metadata
- `POST /query/retrieve` hybrid retrieval
- `POST /query/temporal` truth-at-time query
- `GET /insights/summary` cognitive analytics
- `POST /coach/advice` actionable personalized guidance from memory patterns
- `POST /coach/checkin` save reflection + return practical advice
- `GET /coach/personas` persona templates (student/founder/manager/creator/general)
- `GET /graph/entity/{entity_id}` local graph neighborhood

## Storage

Default runtime adapters:
- graph: in-memory (swap-ready for Neo4j)
- vector: in-memory (swap-ready for FAISS)

Production deployment should wire persistent adapters through environment settings.

## Repo Layout

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

## Notes

- Contradictions are preserved as versioned statements.
- Temporal reasoning is bi-temporal: valid time + ingestion time.
- Retrieval avoids pure cosine by combining vector score, graph context, and temporal relevance.
