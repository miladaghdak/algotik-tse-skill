# Local SQLite history: snapshots, archives, event recording

Scope: the package's local persistence layer. TSETMC serves analytics only
for *now*; anything historical here is something **you recorded yourself**.
The library is explicit about that — every history API documents its
coverage window and refuses to claim backfill.

Store format is SQLite, one file per application. Two constants govern
compatibility: `MARKET_HISTORY_SCHEMA_VERSION` (currently 2) and
`MARKET_HISTORY_APPLICATION_ID` (1096045381). `check_market_history(path)`
verifies a file matches both before you read it — call it after package
upgrades.

## Snapshot save/load

```python
att.save_market_snapshot(path, snapshot=None, *, as_of=None)
frames = att.load_market_snapshots(path, start=None, end=None,
                                   symbol=None, *, limit=1000, offset=0)
```

`save_market_snapshot()` writes one `get_live_market()` observation —
omit `snapshot=` (the supported default: it fetches once) or pass a live-
market DataFrame you already hold. **Don't pass the raw `market_watch()`
dict as `snapshot=`** — its metadata nests the frames back into the
frame's own attrs and pandas' attrs deepcopy turns that into a
quadratic blow-up (verified: minutes for a full market, effectively a
hang). `as_of` backdates the record (use only for replays/testing).
`load_market_snapshots()` reads back rows with paging (`limit`/`offset`)
and the standard date/symbol filters.
The snapshot summary reader is `get_market_snapshot_summary_history()` — one
row per stored snapshot with freshness and size metrics.

## Live-view history

```python
att.get_live_market_history(path, start=None, end=None, symbol=None, *,
                             limit=1000, offset=0)
```

Replays the stored live-view rows (what `get_live_market()` would have
shown at each recorded moment). This is the right data source for
"intraday market evolution" studies built from your own recording schedule.

## Recording while watching

Two ways to persist, pick one per file:

1. **Event recording** — attach the store to a watcher:

```python
import algotik_tse as att

watcher = att.watch_market(interval=5.0, record_to="history.db",
                           record_heartbeats=False)
for event in watcher:
    handle(event)   # every event is also written to the store

# read back what the watcher saw
events = att.get_market_event_history("history.db", kind="update",
                                       limit=100)
```

`record_market_event(path, event)` does the same for a single event you hold
in code (e.g. from your own watcher callback or a custom loop).

2. **Row archiving from live APIs** — pass `archive_to=` to the analytics
calls themselves (`get_market_overview`, `get_market_breadth`,
`get_sector_flow`, `get_market_messages`,
`get_instrument_state_changes`): each fetched row/message page is appended
to the store before being returned to you.

## Independent archive records

```python
att.archive_market_records(path, kind, frame, *, source="tsetmc",
                           recorded_at=None)
```

Batch-appends any conforming DataFrame (`kind` selects the table) to the
store — for when you transform data first or import frames from another
process. `source` and `recorded_at` stamp provenance.

## History readers

```python
att.get_market_overview_history(path, start=None, end=None, flow=0, *,
                                source="tsetmc", limit=1000, offset=0)
att.get_market_breadth_history(path, start=None, end=None, symbol=None,
                               flow=None, sector=None, traded_only=False,
                               include_base_market=True,
                               instrument_types=None, *, limit=1000,
                               offset=0)
att.get_sector_flow_history(path, start=None, end=None, symbol=None,
                            flow=None, sector=None, traded_only=False,
                            include_base_market=True,
                            instrument_types=None, *, limit=1000, offset=0)
att.get_market_messages_history(path, start=None, end=None, flow=0,
                                since_id=None, *, source="tsetmc",
                                limit=1000, offset=0)
att.get_instrument_state_changes_history(path, start=None, end=None,
                                         symbol=None, since_id=None, *,
                                         inscode=None, source="tsetmc",
                                         limit=1000, offset=0)
att.get_market_event_history(path, start=None, end=None, kind=None, *,
                             session_id=None, limit=1000, offset=0)
```

All readers share the same contract: date filters, `limit`/`offset` paging,
and `df.attrs` carrying `Source`, `NoBackfill`, coverage bounds and counts.
`get_market_event_history`'s `kind` filter accepts a watcher event kind or
an iterable of kinds; `session_id` replays one watcher session via its
cursor.

## Integrity and gotchas

- `check_market_history(path)` returns a report dict — assert on it after
  upgrades rather than assuming a silent read.
- **Scale (live-verified):** `save_market_snapshot()` on a whole-market
  live frame (~3.7k rows × 163 columns) is dominated by pandas attrs
  deepcopy and effectively never finishes; on a filtered watchlist frame
  (tens of rows) it completes in seconds. Record what you monitor, not
  the whole board. The watcher has the same guidance — bound
  `record_max_records`/`record_retention_seconds` for long runs.
- Local history covers only what your schedule recorded. For server-side
  price/trades/order-book history use those APIs instead — they have their
  own contracts in `price-and-flow.md` and `live-market.md`.
- `save_option_snapshot` uses a lock file and `stale_lock_seconds` (see
  `options.md`); market-history writes are serialized per process — don't
  write the same file from two processes.
