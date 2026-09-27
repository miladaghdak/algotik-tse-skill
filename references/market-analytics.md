# Market analytics: calendar, activity, TOP, comparisons, regime, map, fundamentals

Scope: market-level reference and analytics — official TSETMC aggregates,
the pre-open service, multi-symbol comparison, liquidity, regime
classification, market map, and the EPS/P/E screen.

## get_trading_calendar()

```python
cal = att.get_trading_calendar(start=None, end=None, market="all",
                               include_closed=False, limit=90)
```

Published trading sessions for بورس and فرابورس — the authoritative way to
know which days the market was/is open. `market` accepts `"all"`, `"tse"`
(or `"bourse"`/`"بورس"`) and `"ifb"` (or `"farabourse"`/`"فرابورس"`).
`include_closed=True` adds non-trading days flagged as closed. Defaults to
the next/last 90 days when no range is given. Use it to build backtest
calendars and to distinguish "no data" from "market closed".

## get_market_activity() and get_market_value_history()

```python
act = att.get_market_activity(start=None, end=None, market="all",
                              max_requests=30, progress=True)
val = att.get_market_value_history(start=None, end=None, market="all",
                                   limit=90)
```

`get_market_activity()` — daily aggregates per board: instrument count,
trades, volume, value. `max_requests` bounds the paging (default 30).
`get_market_value_history()` — the official daily market value series with
day-over-day change (this is the official number; don't rebuild it from
per-symbol market caps).

## get_index_impact()

```python
impact = att.get_index_impact(date=None, market="all", top=10,
                              direction="both")
```

Which symbols moved the main index on a given session — official TSETMC
attribution, not a re-implementation. `direction` filters
`'both'` / `'positive'` / `'negative'`, `top` caps rows.

## get_market_trades()

```python
trades = att.get_market_trades(date=None, market="all", progress=True)
```

The **bulk daily per-instrument summary** (one row per instrument for a
date) — not the fine-grained tape. For individual trades use
`get_trades()`/`get_live_trades()`.

## get_theoretical_opening_price() and get_preopen_imbalance()

```python
top = att.get_theoretical_opening_price(*, username=None, password=None,
                                        market="all", timeout=None,
                                        progress=True)
imb = att.get_preopen_imbalance(top_data=None, *, username=None,
                                password=None, market="all",
                                timeout=None, progress=True)
```

The official TOP (Theoretical Opening Price) service is **subscription
gated**: both functions require TSETMC webservice `username`/`password`.
Without credentials they raise `InvalidParameterError` before any request.
`get_preopen_imbalance()` adds transparent buy/sell imbalance metrics on
top of a TOP frame — either fetched live (credentials) or passed in as
`top_data=` (a TOP DataFrame you already hold). These are the pre-open
(پیش‌گشایش) APIs.

## compare_symbols()

```python
cmp = att.compare_symbols(symbols, start=None, end=None, benchmark=None,
                          align="inner", annualization=240,
                          min_observations=20, include_client_type=True,
                          progress=True, history_data=None,
                          client_data=None, strict=False)
```

Multi-symbol comparison: per-symbol return, risk (annualized vol),
drawdown, liquidity and حقیقی/حقوقی flow metrics, plus benchmark-relative
columns when `benchmark=` is given. `align` is `'inner'`/`'outer'` for date
intersection. `annualization=240` matches the Iranian trading year.
Pass pre-fetched frames via `history_data=`/`client_data=` to avoid
re-downloading. `strict=True` fails on any unresolvable symbol instead of
continuing with the rest.

## get_liquidity_metrics()

```python
liq = att.get_liquidity_metrics(symbols=None, start=None, end=None,
                                window=20, annualization=240,
                                include_live=True, progress=True,
                                history_data=None, live_data=None,
                                strict=False)
```

Amihud illiquidity, turnover, spread and depth measures per symbol from
history plus the current live snapshot (`include_live=True` appends a
today row). Same pre-fetch injection (`history_data`, `live_data`) and
`strict` semantics as `compare_symbols`.

## get_market_regime()

```python
regime = att.get_market_regime(benchmark="شاخص کل", start=None, end=None,
                              lookback=60, liquidity_window=20,
                              annualization=240, weights=None,
                              progress=True, max_requests=30,
                              live_data=None, benchmark_history=None,
                              activity_history=None)
```

An explainable `risk_on` / `neutral` / `risk_off` classification from five
observable components, default weights:

```python
{"trend": 0.30, "breadth": 0.25, "flow": 0.20,
 "liquidity": 0.15, "queue": 0.10}
```

Weights must be non-negative with at least one positive; renormalized
internally. The result reports each component's value and contribution —
never treat the label as a black box. Inject pre-fetched frames with
`live_data`, `benchmark_history`, `activity_history`.

## get_market_map() and plot_market_map()

```python
data = att.get_market_map(group_by="symbol", size="value",
                          color="return", top=100, flow=None,
                          instrument_types=None, data=None)

fig = att.plot_market_map(map_data=None, output_path=None, show=False,
                          title=None)
```

Renderer-independent market-map table from one live snapshot:

- `group_by` — `'symbol'` | `'sector'` | `'flow'` | `'instrument_type'`
- `size` — `'value'` | `'volume'` | `'market_cap'` | `'queue_value'`
- `color` — `'return'` | `'net_individual_flow'` | `'individual_power'` |
  `'order_imbalance'`
- `data=` — analyze a previously fetched live frame instead of refetching.

`plot_market_map()` renders the table as a Plotly treemap (needs the
`[visualization]` extra, `plotly>=5.0`); `output_path` saves an HTML file,
`show=True` opens a browser. Rows with non-positive size are dropped — the
map only shows what had activity.

## get_market_fundamentals() and its history

```python
fund = att.get_market_fundamentals(symbols=None, *, pe_min=None,
                                   pe_max=None, positive_pe=True,
                                   instrument_types=(300, 303, 309),
                                   strict=False, allow_stale=False,
                                   archive_to=None, max_requests=1,
                                   progress=True)

hist = att.get_market_fundamentals_history(path, start=None, end=None,
                                          symbols=None, *, pe_min=None,
                                          pe_max=None, positive_pe=True,
                                          instrument_types=(300, 303, 309),
                                          strict=False, allow_stale=True,
                                          limit=1000, offset=0)
```

Bulk EPS and calculated P/E screen from one MarketWatch request.
`instrument_types=(300, 303, 309)` is the equity set. `pe_min`/`pe_max`
are inclusive; `positive_pe=True` keeps only finite positive P/E rows —
set it to `False` to retain undefined ones with a `PEStatus` flag.
**No Codal or per-symbol instrument-info calls are made** — EPS comes from
the bulk snapshot.

Freshness gotcha (verified live): with the default `allow_stale=False`
this returns an **empty frame whenever TSETMC's current-session EPS
snapshot is not fresh** — outside publication windows that is the normal
case, not an error. Pass `allow_stale=True` to screen the last published
snapshot. The history reader (your archive) defaults to
`allow_stale=True` because recorded rows are inherently historical;
look-ahead-safe backtesting should filter by recorded timestamp, not by
`as_of` tricks.

```python
fund = att.get_market_fundamentals(allow_stale=True, progress=False)
cheap = fund[(fund["PE"] > 0) & (fund["PE"] < 5)]
```
