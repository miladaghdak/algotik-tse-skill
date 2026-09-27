# Live market: snapshots, live rows, order book and صف

Scope: the current-session data plane. One bulk request serves the whole
market; individual APIs slice it. Everything here reflects *one atomic
observation* of the market with explicit freshness flags.

## get_market_snapshot() / market_watch()

```python
snap = att.get_market_snapshot()   # == att.market_watch()
```

One request, the whole market. Returns a **dict**, not a DataFrame. Keys
verified live:

- `stocks` — DataFrame, one row per instrument, ~40 columns (price, change,
  volume, value, counts, EPS-related fields, sector, thresholds…).
- `order_book` — best-bid/ask levels aggregated across instruments.
- `trade_date`, `market_time`, `exchange_time`, `fetched_at` — identity of
  the observation.
- `index_value` — main index at snapshot time.
- `market_state` — session state string.
- `snapshot_age_seconds`, `is_realtime_fresh`, `is_stale`, `is_partial`,
  `is_today_trade_date`, `is_previous_trade_date`, `is_history_eligible`,
  `migration` — **read these before analyzing**. `is_realtime_fresh=False`
  means you are looking at a delayed/previous-day picture; `is_partial=True`
  means some instruments are missing.

```python
snap = att.get_market_snapshot()
if not snap["is_realtime_fresh"]:
    print("stale feed, fetched", snap["fetched_at"])
stocks = snap["stocks"]          # DataFrame
book = snap["order_book"]
```

`market_data()` is a deprecated alias that redirects here.

## get_market_client_type() / market_client_type()

```python
client = att.get_market_client_type()
```

Bulk حقیقی/حقوقی for every instrument in one call — the same columns you get
from `get_client_type()` history, but for the current session. One row per
instrument, keyed by `InsCode`. This is the cheap way to screen the whole
market for individual-buyer power without 2000 per-symbol requests.

## get_live_market() and get_live_symbol()

```python
live = att.get_live_market(symbol=None, *, strict=False)
row = att.get_live_symbol(symbol=None, *, ins_code=None, fallback="none")
```

`get_live_market()` returns the merged analytical view: one row per
instrument with ~160 columns — price fields, حقیقی/حقوقی aggregates,
participation ratios, five-level order-book aggregates, liquidity and
individual-flow estimates (`EstimatedNetIndividualFlow`, `IndividualPower`,
`L5Imbalance`, `LegalBuyParticipation`, …). Pass a symbol or list to filter.
Every analytical column the market-wide APIs use is derivable from this
frame, which is why it is the backbone for screeners.

**Verified pre-market gotcha:** `get_live_market()` merges the bulk
حقیقی/حقوقی feed (`old.tsetmc.com/tsev2/data/ClientTypeAll.aspx`), and
TSETMC **empties that endpoint outside its publication windows**. When
it is empty the call raises `DataParsingError: Empty response from
client type endpoint` — retry during trading hours, or fall back to
`get_market_snapshot()["stocks"]` (a different feed) for pre-market
price context. Same class of upstream behavior as the industry
membership emptiness: it is the provider's schedule, not a package bug.

`get_live_symbol()` returns exactly one row (a 1-row DataFrame) for an
instrument:

- `fallback="none"` (default) — reads MarketWatch only; a symbol absent from
  the snapshot raises/returns nothing, preserving the historical contract.
- `fallback="point"` — resolves identity and falls back to the official
  `ClosingPriceInfo` endpoint when the instrument is missing from the
  snapshot; the row records its `Source` and the absence reason in attrs.
  Use this for instruments that don't appear in the bulk feed (halted, thin
  پایه names).

`strict=True` on `get_live_market` turns partial snapshots into errors
instead of returning what's available.

## get_order_book() and get_queue()

```python
book = att.get_order_book(symbol=None, *, selector_strict=False)
queue = att.get_queue(symbol=None, side="both", strict=True, *,
                      selector_strict=False)
```

- `get_order_book()` — five levels of bid/ask rows for one instrument
  (level, price, volume, count). `selector_strict=True` demands a resolvable
  selector; default tolerates near-matches.
- `get_queue()` — صف (buy/sell queue) metrics: queued volume, queue value,
  counts and derived ratios. `side` is `'both'`, `'buy'` or `'sell'`;
  `strict=True` means "no trade today / halted is an error".

## Historical order book and queue

```python
att.get_order_book_history(symbol="", start=None, end=None, limit=0, raw=False,
                           output_type="standard", date_format="jalali",
                           progress=True, save_to_file=False, dropna=True,
                           ascending=True, save_path=None,
                           include_today=False, complete_only=False, *,
                           max_requests=None, **kwargs)

att.get_queue_history(symbol="", start=None, end=None, limit=0,
                      date_format="jalali", progress=True, save_to_file=False,
                      dropna=True, ascending=True, save_path=None,
                      include_today=False, complete_only=False,
                      side="both", strict=True, *, max_requests=None,
                      **kwargs)
```

`get_orderbook_history()` is the alternate spelling of the same API. These
reconstruct per-session five-level order book and صف history server-side.
`complete_only=True` keeps only sessions with a complete record.
`max_requests` bounds the paging budget (default
`settings.order_book_max_requests = 250`).

## Live trades

```python
tape = att.get_live_trades(symbol, *, ins_code=None, include_canceled=False,
                           max_requests=None, raw=False, progress=True)
```

Today's individual trades for one instrument — the same shape as
`get_trades()` (see `price-and-flow.md`), without the date paging.

## Patterns

```python
import algotik_tse as att

# Market-wide individual-power screen from one request
live = att.get_live_market()
screen = live[live["IndividualPower"] > 1.2]   # column present in 1.8.0

# Queue-focused watch for one name
q = att.get_queue("شبندن", side="buy", strict=False)
```

Column names above are examples of the 1.8.0 schema — print
`list(live.columns)` before you rely on any specific name, and treat
`df.attrs` as the source of truth for freshness.
