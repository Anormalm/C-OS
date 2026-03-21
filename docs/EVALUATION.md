# Evaluation

## Objective

Measure whether C-OS hybrid retrieval and coaching produce better context-aware outcomes than simple vector-only lookup.

## Offline Benchmark

Run:

```bash
python -m cos.experiments.benchmark_retrieval
```

Current metric:
- `Hit@3` for expected facts.

Track over time:
- hybrid `Hit@3`
- vector-only `Hit@3`
- relative gain (%)

## Online Product Metrics

- Activation rate: users who ingest and query in first session.
- Advice usefulness: `% useful` feedback.
- Retention: weekly active users.
- Retrieval p95 latency.

## Release Gate Suggestions

- `Hit@3` hybrid >= vector-only baseline.
- API smoke tests pass.
- p95 retrieval < 500ms on representative local dataset.
