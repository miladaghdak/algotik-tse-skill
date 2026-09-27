# Industry indices and analytics

Scope: the 45 official TSETMC industry indices (شاخص صنعت), their exact
members, and the analytics built on them. Industry APIs are the package's
richest family — one bulk index request serves the list, then membership
drives everything else.

Core identities: each industry has a Persian name (e.g. `فلزات اساسی`),
an English name (`Basic Metals`) and an `IndexInsCode` (the long numeric
id). Most functions accept the Persian name or the code.

## The quick path

```python
import algotik_tse as att

indices = att.list_industry_indices()            # 45 rows, one request
members = att.get_industry_members("فلزات اساسی", include_live=True)
snapshot = att.get_industry_snapshot(["فلزات اساسی", "بانک"])
ranking = att.rank_industries(metric="IndexChangePct")
```

## list_industry_indices()

```python
idx = att.list_industry_indices(progress=True, include_member_count=False,
                               refresh=False, max_workers=6)
```

All 45 industry indices with current value, change and percent change.
`include_member_count=True` adds member counts (costs extra membership
requests). `refresh=True` bypasses the membership cache
(`settings.industry_membership_cache_ttl`, default 3600s).

## get_industry_members()

```python
members = att.get_industry_members(industry, include_live=True,
                                   include_client_type=False,
                                   include_orderbook=False, progress=True,
                                   refresh=False)
```

The official, exact membership list — `industry` must be a Persian name or
an `IndexInsCode`. `include_live=True` joins each member's current live
row (price, value, volume…); `include_client_type=True` adds حقیقی/حقوقی
aggregates; `include_orderbook=True` adds five-level order book metrics.
This is the only supported membership source — never guess industry
membership from the sector code on instrument rows.

## get_industry_snapshot()

```python
snap = att.get_industry_snapshot(industries=None, include_client_type=True,
                                 include_orderbook=False,
                                 include_empty=False, progress=True,
                                 refresh=False, max_workers=6)
```

One analytical row per industry: index value/change, breadth
(advance/decline), trades, حقیقی/حقوقی flow estimates and صف aggregates.
`industries=None` means all 45.

**Verified gotcha:** membership comes from TSETMC's
`ClosingPrice/GetIndexCompany` endpoint, which TSETMC **empties outside
publication windows** (pre-market mornings, evenings). When the payload is
empty the function drops those industries from the result instead of
failing. `include_empty=True` keeps them, and
`df.attrs["empty_industries"]` lists which were empty. If a snapshot
comes back with fewer rows than you asked for, check attrs first — it is
usually the publication window, not a bug. The same applies when
`get_industry_members()` returns zero rows: verify the raw endpoint
state before assuming your industry name is wrong.

Memberships overlap across industries and rows must not be summed to a
market total; the attrs flag `memberships_may_overlap` says this too.

## get_industry_history() and get_industry_members_history()

```python
hist = att.get_industry_history(industry, start=None, end=None, limit=0,
                                ascending=True, progress=True)
members_hist = att.get_industry_members_history(industry, days=30,
                                                ascending=True,
                                                progress=True, refresh=False)
```

`get_industry_history()` — the official daily history of the industry
index itself (value, change; **no fabricated volume** — industry indices
have no volume). `get_industry_members_history()` — short multi-day history
of every current member in long form (symbol × date rows). Note the second
one fetches history for the *current* membership, so point-in-time
membership questions need `get_industry_membership_events()` instead.

## get_industry_intraday()

```python
intra = att.get_industry_intraday(industry, interval="1min",
                                  progress=True)
```

Raw intraday observations or resampled candles for the industry index.
`interval` accepts `'raw'`, `'1min'`, `'5min'`, `'15min'`, `'30min'`,
`'60min'` or `'1h'` — the two hour spellings are equivalent.

## compare_industries() and relatives

```python
cmp = att.compare_industries(industries, start=None, end=None, limit=0,
                             metric="close", ascending=True, progress=True,
                             max_workers=6)
rs = att.get_industry_relative_strength(industries, benchmark, start=None,
                                        end=None, limit=0, metric="close",
                                        ascending=True, progress=True,
                                        max_workers=6)
corr = att.get_industry_correlation(industries, start=None, end=None,
                                    limit=0, ascending=True, progress=True,
                                    max_workers=6)
near = att.get_industry_correlation_neighborhood(industry, industries=None,
                                                top=5, min_correlation=0.0,
                                                by_absolute=False, start=None,
                                                end=None, limit=0,
                                                ascending=False, progress=True,
                                                max_workers=6)
```

- `compare_industries()` — aligned time series of several industry indices;
  `metric` is `'close'`, `'change_pct'` or `'log_return'`.
- `get_industry_relative_strength()` — cumulative relative return vs a
  benchmark industry.
- `get_industry_correlation()` — daily-return correlation matrix.
- `get_industry_correlation_neighborhood()` — the `top` most-correlated
  industries for one target; `by_absolute=True` ranks by |ρ|,
  `min_correlation` filters.

`max_workers` (1–16) parallelizes history fetches.

## Membership events, overlap, churn

```python
overlap = att.get_industry_membership_overlap(industries, progress=True,
                                              refresh=False, max_workers=6)
events = att.get_industry_membership_events(industries, days=30,
                                            progress=True, refresh=False,
                                            max_workers=6)
churn = att.get_industry_membership_churn(industries, days=0, progress=True,
                                          refresh=False, max_workers=6)
```

- `get_industry_membership_overlap()` — pairwise shared members across the
  official lists (companies often sit in more than one index).
- `get_industry_membership_events()` — official `added`/`dropped` events,
  the point-in-time membership source. `days` must be within 1–30.
- `get_industry_membership_churn()` — how much the membership lists changed
  over the last `days` sessions (`days=0` = just the latest change set).

## Composition and health

```python
conc = att.get_industry_concentration(industries, top_n=10,
                                      include_weights_by_market_value=True,
                                      progress=True, refresh=False,
                                      max_workers=6)
mom = att.get_industry_momentum_profile(industries, windows=(5, 20, 60),
                                        start=None, end=None, progress=True,
                                        max_workers=6)
health = att.get_industry_health_score(industries=None, start=None,
                                       end=None, top_concentration=10,
                                       momentum_windows=(20, 60),
                                       progress=True, refresh=False,
                                       max_workers=6)
rank = att.rank_industries(metric="IndexChangePct", top=None,
                           ascending=False, include_client_type=True,
                           include_orderbook=False, progress=True,
                           refresh=False, max_workers=6)
```

- `get_industry_concentration()` — HHI, weight of the top-N members and
  their market-value shares.
- `get_industry_momentum_profile()` — multi-window momentum (5/20/60 by
  default) per industry; every window must be ≥ 2.
- `get_industry_health_score()` — combined breadth + momentum +
  concentration score; tune `top_concentration` and `momentum_windows`.
- `rank_industries()` — one-row-per-industry ranking table; `metric` is
  one of `IndexChangePct`, `EqualWeightReturn`, … (the metric names are
  the ranking frame's columns — see `att.rank_industries.__doc__` for the
  current list). Pass `top=` to cap rows.

## Legacy index APIs

```python
indices = att.list_indices(progress=True)
companies = att.get_index_companies(index_name, progress=True)
```

The pre-1.2 index API. `list_indices()` returns every index row (the
industry indices plus the market-level ones like شاخص کل);
`get_index_companies()` returns the members of an index by name. For
industry work prefer the dedicated family above; `get_index_companies`
shares the same `GetIndexCompany` endpoint and the same empty-payload
behavior outside publication windows.
