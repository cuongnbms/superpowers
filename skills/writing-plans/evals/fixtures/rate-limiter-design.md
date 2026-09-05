# API Rate Limiter Design

**Date:** 2026-08-20
**Status:** Approved

## Goal

Add per-client rate limiting to the `notesd` HTTP service so a single API key
cannot exceed its quota and starve other clients.

## Requirements

- Token-bucket algorithm, one bucket per API key.
- Default quota: 120 requests per minute, burst 20. Both values configurable
  via `RATE_LIMIT_PER_MINUTE` and `RATE_LIMIT_BURST` environment variables.
- Rejected requests return HTTP 429 with JSON body `{"error": "rate_limited", "retry_after_seconds": <int>}`.
- Every response (allowed or rejected) carries headers `X-RateLimit-Limit`,
  `X-RateLimit-Remaining`, and `X-RateLimit-Reset` (unix seconds).
- Requests without an API key are rejected with 401 before limiting applies.
- Buckets live in process memory; no Redis or external store in this phase.
- Idle buckets are evicted after 10 minutes so memory stays bounded.

## Constraints

- Python 3.11+, FastAPI 0.110+. No new runtime dependencies.
- Tests use pytest with `httpx.AsyncClient`; no sleeping in tests, inject a
  clock instead.
- Existing middleware order in `notesd/app.py` must not change; the limiter
  is added after `AuthMiddleware`.

## Architecture

- `notesd/ratelimit/bucket.py`: `TokenBucket` class with `try_consume(now: float) -> tuple[bool, int]` returning (allowed, retry_after_seconds).
- `notesd/ratelimit/registry.py`: `BucketRegistry` mapping api_key -> TokenBucket with eviction.
- `notesd/ratelimit/middleware.py`: FastAPI middleware wiring registry, headers, and 429 response.
- `notesd/app.py`: register middleware, read env config.

## Out of Scope

- Distributed limiting, per-endpoint quotas, admin overrides.
