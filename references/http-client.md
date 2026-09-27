# HTTP client, settings and the source boundary

Scope: the transport layer every API call goes through — read this when
debugging connectivity, tuning throughput, or wondering why a request was
refused. Direct use of `requests` against provider endpoints (instead of
the package) re-implements all of this badly; don't.

## safe_get() — the only door out

```python
from algotik_tse.http_client import safe_get

response = safe_get(url, **kwargs)
```

Contract (all enforced before any I/O):

1. **URL validation first.** `url` must be HTTP(S) and its host must be
   inside the supported providers: TSETMC (`tsetmc.com`), Iran Fara Bourse
   (`ifb.ir`), TGJU (`api.tgju.org`) and IME (`ime.co.ir`). Anything else —
   including **Codal, even proxied under a TSETMC hostname** — raises
   `UnsupportedDataSourceError` before rate limiting, session creation or
   any network I/O. Userinfo in the URL is rejected. Percent-encoded paths
   are decoded a bounded number of times and ambiguous or nested
   encodings, control characters, backslash separators and RFC dot
   segments are normalized or rejected — reverse-proxy decoding tricks
   don't slip past the host allow-list.
2. **Rate limiting.** A process-wide scheduler enforces a minimum
   start-to-start spacing of `settings.rate_limit_delay` (default 0.3s)
   across all package calls. The slot is reserved under the same lock as
   the request itself, so concurrent threads can't crowd in.
3. **Retries.** GET-only, with backoff on 429/500/502/503/504
   (`settings.max_retries`, `settings.retry_backoff_factor`). The retry
   strategy is built per urllib3 API (`allowed_methods`, falling back to
   `method_whitelist`) so old adapters don't silently lose retries.
4. **Redirects.** The underlying request never follows redirects
   automatically. `safe_get` resolves each hop itself, re-validates the
   URL, and allows **same-origin only** (scheme, host, effective port).
   Cross-origin redirects raise `UnsupportedDataSourceError`; loops and
   overruns raise `TooManyRedirects`. Caller `params` apply only to the
   first request; headers survive same-origin hops.
5. **Defaults.** `headers`, `timeout` and `verify` come from
   `settings` unless the caller overrides them.

`safe_get` does **not** call `raise_for_status()` — consuming APIs convert
4xx/5xx to their typed errors themselves. `allow_redirects=False` and
`max_redirects=N` (wrapper-level parameters) are available for callers that
need manual redirect handling; wrong types raise `TypeError`/`ValueError`.

## reset_session()

```python
from algotik_tse.http_client import reset_session

att.settings.max_retries = 5
reset_session()   # rebuild the shared Session with new retry settings
```

`ssl_verify`, `timeout` and `rate_limit_delay` apply immediately; retry
settings need `reset_session()`. Reset preserves in-flight rate-limit
reservations, so it's safe to call mid-run.

## The settings singleton

```python
from algotik_tse import settings
```

| Attribute | Default | Meaning |
|---|---|---|
| `ssl_verify` | `True` | TLS verification; opt out only with a broken CA, per-request |
| `timeout` | `10` | request timeout, seconds |
| `max_retries` | `3` | transport retries |
| `retry_backoff_factor` | `0.3` | backoff factor |
| `rate_limit_delay` | `0.3` | minimum spacing between request starts |
| `market_snapshot_freshness_seconds` | `120.0` | how old a snapshot may be to count as realtime-fresh |
| `market_clock_skew_tolerance_seconds` | `5.0` | tolerated provider clock skew |
| `client_volume_consistency_tolerance` | `0.05` | حقیقی+حقوقی vs total consistency check tolerance |
| `industry_membership_cache_ttl` | `3600.0` | membership cache lifetime |
| `order_book_max_requests` | `250` | default order-book history paging budget |
| `trade_max_requests` | `250` | default trades paging budget |
| `headers` | browser-like UA | request headers |
| `payeh_market_color_num` | `{'زرد': [0, 1], 'نارنجی': [1, 2], 'قرمز': [2, 4]}` | بازار پایه tier mapping |

Settings are plain attributes on a singleton — assign before the first
request in long-lived processes. Don't mutate `settings.headers` into a
shared mutable mess across threads; replace it wholesale.

## Exceptions

`RateLimitError` exists in `algotik_tse.exceptions` for internal
compatibility but is **not** exported at package level. The public
hierarchy (exported and documented):

```text
AlgotikTSEError
├── AmbiguousSymbolError
├── ConnectionError          # shadows builtins.ConnectionError inside the package namespace
├── DataParsingError
├── InvalidParameterError
├── StockNotFoundError
└── UnsupportedDataSourceError
```

When you `except algotik_tse.ConnectionError`, you're catching the package
one — the builtin with the same name is a different class. Prefer the
explicit prefix in mixed code.

## Troubleshooting map

| Symptom | Likely cause | Fix |
|---|---|---|
| `UnsupportedDataSourceError: ... outside algotik-tse's supported providers` | URL host outside the boundary | use the package API for that data; Codal has no path through this package |
| `ConnectionError` after retries | provider down / network / VPN | the package's own tests say "turn off VPN" for some endpoints; retry later |
| Empty frames from freshness-sensitive APIs | session not published yet | `allow_stale=True` / `include_stale=True` / `include_empty=True` |
| `TooManyRedirects: cross-origin` | a provider endpoint started redirecting off-host | nothing you can do from user code; report upstream |
| Everything slow | rate limit + retries | raise `rate_limit_delay` only if you accept the provider's throttling risk |
| `AmbiguousSymbolError` | duplicate tickers | pass `ins_code=` (see `instrument-identity.md`) |
