# Ownership: shareholders, capital increases, price adjustments, symbol events

Scope: who holds the instruments — current and historical major
shareholders (سهامداران عمده), the five-day change board, ownership
networks and concentration — plus capital increases (افزایش سرمایه), price
adjustment events (تعدیل قیمت) and the per-symbol event timeline.

## get_shareholders()

```python
holders = att.get_shareholders(symbol="", date=None, include_id=False, *,
                               ins_code=None, asset_type="auto", **kwargs)
```

The current major-shareholder list (typically 20 rows): holder name,
shares, percent, change vs previous snapshot. `date=` returns the
shareholder table *as recorded on a trading day* — TSETMC keeps a rolling
window of dated snapshots. `include_id=True` adds the holder's registry id
where published. Legacy name: `shareholders()`.

## get_shareholder_history()

```python
hist = att.get_shareholder_history(symbol="", start=None, end=None,
                                   frequency="daily", max_requests=60,
                                   include_id=False, progress=True, *,
                                   ins_code=None, asset_type="auto")
```

Per-instrument shareholder **snapshots on their effective dates** — the
dated series behind `get_shareholders(date=...)`. **`start` and `end` are
required** (there is no "latest N" overload; omitting them raises
`InvalidParameterError`). `frequency` is `'daily'`, `'weekly'` or
`'monthly'` (publication frequency of the underlying snapshots),
`max_requests` bounds the fetch (default 60). This is the point-in-time
source: each row is the table *as effective from* that date, not
interpolated.

## The five-day change board family

```python
snaps = att.get_major_shareholder_snapshots(date=None, days=5, symbol=None, *,
                                            ins_code=None, holder=None,
                                            enrich_identity=True,
                                            progress=True)
changes = att.get_major_shareholder_changes(date=None, days=5, symbol=None, *,
                                            ins_code=None, holder=None,
                                            direction="both",
                                            enrich_identity=True,
                                            progress=True)
active = att.get_active_shareholders(symbol=None, days=5, *,
                                     ins_code=None, holder=None,
                                     enrich_identity=True, progress=True)
```

These mirror the official "recent changes" board that TSETMC publishes for
the last few sessions (hence `days` is an integer between 1 and 5):

- `get_major_shareholder_snapshots()` — the raw published snapshots.
- `get_major_shareholder_changes()` — holdings deltas between consecutive
  snapshots; `direction` filters `'both'`/`'increase'`/`'decrease'`/
  `'unchanged'`.
- `get_active_shareholders()` — an entry/exit summary of who was active in
  the window.

`holder=` filters by holder name across instruments; `symbol=`/`ins_code=`
restrict to one instrument. `enrich_identity=True` merges holder registry
identity where published. Live-verified: with no filters these return
1000+ rows across the market.

## rank_shareholder_accumulation()

```python
rank = att.rank_shareholder_accumulation(days=5, symbol=None, *,
                                         ins_code=None, holder=None,
                                         direction="both", metric="percent",
                                         top=20, enrich_identity=True,
                                         progress=True)
```

Ranks holder/instrument accumulation pairs over the recent window.
`metric` picks how accumulation is measured — `'percent'` (share-of-float
change) normalizes across instruments with very different share counts,
which is why raw share counts are not summed across symbols. `top` caps
rows; `days` is again bounded to 1–5 (the published window).

## get_shareholder_network() and get_ownership_concentration()

```python
edges = att.get_shareholder_network(date=None, symbol=None, *,
                                    ins_code=None, holder=None,
                                    min_holdings=0, enrich_identity=True,
                                    progress=True)

conc = att.get_ownership_concentration(symbol="", date=None, *,
                                       ins_code=None, asset_type="auto",
                                       top_n=5, progress=True)
```

- `get_shareholder_network()` — a bipartite edge list (holder ↔ instrument)
  from the latest published snapshot: the input graph for "which holders
  appear across several companies" analyses. `min_holdings` drops
  dust-level positions.
- `get_ownership_concentration()` — concentration of the *disclosed*
  major holders of one instrument: top-`top_n` weight, HHI-style sums.
  It measures the disclosed list only — undisclosed free float is not
  inferred.

## get_capital_increase()

```python
cap = att.get_capital_increase(symbol="", *, ins_code=None,
                               asset_type="auto", **kwargs)
```

Capital increase history (افزایش سرمایه) for an instrument: dates,
ratios (from reserves, cash, revaluation) and the resulting share counts.
Legacy name: `stock_capital_increase()`.

## get_price_adjustments() and get_latest_price_adjustment()

```python
adj = att.get_price_adjustments(symbol=None, *, ins_code=None,
                                start=None, end=None, progress=True)
latest = att.get_latest_price_adjustment(symbol=None, *, ins_code=None,
                                         start=None, end=None,
                                         progress=True)
```

Published price-adjustment events (تعدیل قیمت ناشی از افزایش سرمایه و
سود نقدی) with dates and the reference prices around them. These need an
exact instrument — on an ambiguous selector they raise
`AmbiguousSymbolError` (live-verified with `شتران`); pass `ins_code=`.

TSETMC does **not** publish a definitive DPS for adjustment events. The
gap between adjusted and unadjusted prices is not a dividend proxy, and
the package refuses to infer one.

## get_symbol_events()

```python
events = att.get_symbol_events(symbol=None, start=None, end=None,
                               kinds=("messages", "capital_changes",
                                      "price_adjustments"),
                               limit=100, ascending=False, progress=True, *,
                               ins_code=None, max_requests=3)
```

The TSETMC-native per-symbol timeline, joining three event kinds:
supervisor messages on the symbol, capital changes, and price
adjustments. `kinds` accepts any subset of `"messages"`,
`"capital_changes"`, `"price_adjustments"` (string or iterable of
strings — passing anything else raises `InvalidParameterError`).
`max_requests=3` bounds the per-kind fetches. One call replaces three
separate queries when you need "everything that happened to this symbol
in this window".
