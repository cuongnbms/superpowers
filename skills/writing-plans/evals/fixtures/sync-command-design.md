# `harness sync` Command Design

**Date:** 2026-09-26
**Status:** Approved

## Goal

Add a `harness sync` subcommand to the Go CLI (cobra) that pulls the
registry of harnesses from a remote JSON endpoint, merges it with the local
cache, and reports what changed, so `harness list` stops depending on the
hard-coded rows in `fetch.go`.

## Requirements

- `harness sync` fetches `GET <base-url>/v1/harnesses` and expects a JSON
  array of objects with keys `name`, `status`, `updated_at` (RFC 3339).
- Base URL comes from `HARNESS_REGISTRY_URL`; missing or empty means exit
  code 2 with `registry url not set` on stderr.
- Local cache lives at `$XDG_CACHE_HOME/harness/registry.json` (fallback
  `~/.cache/harness/registry.json`), same JSON shape as the endpoint.
- Merge rule: a remote row wins when its `updated_at` is newer than the
  cached row of the same `name`; a cached row with no remote counterpart is
  kept and marked `status: "orphaned"`; a remote row with no cached
  counterpart is added.
- After merging, print one line per changed row in the form
  `<verb> <name> (<old-status> -> <new-status>)` where verb is one of
  `added`, `updated`, `orphaned`; print `up to date` when nothing changed.
- `--dry-run` prints the same report but does not write the cache.
- HTTP errors: retry 5xx up to 3 times with 200ms, 400ms, 800ms backoff;
  any 4xx is a hard failure with exit code 1 and the status code on stderr.
  Timeout per request is 5 seconds.
- `harness list` reads rows from the cache when it exists and falls back to
  the current in-memory rows when it does not; its output and filtering do
  not change.

## Constraints

- Go 1.22, cobra, testify. Standard library `net/http` and
  `net/http/httptest` only; no new dependencies.
- No network in tests; inject the base URL and a clock.
- No sleeping in tests: backoff durations are injected.
- Existing `Row` struct and `newListCmd(out, fetch)` signature stay as they
  are; `list` gains a data source, not a new flag.

## Architecture

- `cmd/harness/registry.go`: `type Client struct` with
  `Fetch(ctx context.Context) ([]Row, error)` doing the GET, retry, and
  decode; constructor `NewClient(baseURL string, http *http.Client, sleep func(time.Duration)) *Client`.
- `cmd/harness/cache.go`: `LoadCache(path string) ([]Row, error)` and
  `SaveCache(path string, rows []Row) error`; `CachePath() (string, error)`
  resolves the XDG path.
- `cmd/harness/merge.go`: `Merge(cached, remote []Row) (merged []Row, changes []Change)`
  with `type Change struct { Verb, Name, Old, New string }`.
- `cmd/harness/sync.go`: `newSyncCmd(out, errOut io.Writer, client *Client, cachePath string) *cobra.Command`
  wiring flag, merge, report, and write.
- `cmd/harness/main.go`: register `sync`, make `list` read the cache first.

## Out of Scope

- Authentication, pagination, deleting orphaned rows, a `--json` flag on
  `sync`.
