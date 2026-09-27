# Market stream: watcher, messages, state, overview, breadth, sector flow

Scope: streaming/incremental market watching, the supervisor's message
board, instrument state changes, and the market-level analytics computed from
one live snapshot (overview, breadth, sector flow). The persisted-history
counterparts live in `local-history.md`.

## watch_market() / MarketWatcher / MarketEvent

```python
for event in att.watch_market(interval=2.0, max_updates=5):
    if event.kind == "update":
        print(event.sequence, event.changed_inscodes[:5])
```

`watch_market()` creates a synchronous `MarketWatcher` — an iterator yielding
`MarketEvent` objects. Constructor parameters worth knowing:

- `symbol` — restrict the watcher to one instrument (default: whole market).
- `interval` — polling period in seconds (default 1.0).
- `max_updates` — stop after N events (otherwise runs forever).
- `include_initial` — emit one event immediately with the current state.
- `emit_heartbeats` — yield `kind="heartbeat"` events when nothing changed.
- `notifications` — `("messages", "state")` by default; supervisor messages
  and instrument state changes are attached to matching events.
- `notification_top` — cap on messages per event (default 50).
- `error_policy` — `'retry'` (default, with backoff up to `max_backoff=30.0`
  and `jitter`), `'raise'` or `'stop'`.
- `callback_error_policy` / `storage_error_policy` — how errors inside your
  callback or the SQLite recorder surface (`'raise'` or `'ignore'`).
- `record_to="history.db"` — persist every event to your local SQLite store
- `record_to="history.db"` — persist every event to your local SQLite store
  while watching (see `local-history.md`); `record_heartbeats=False` skips
  empty beats, `checkpoint_interval`/`record_max_records`/
  `record_retention_seconds` bound the store.

**Live-verified incompatibility (1.8.0, observed live):** the watcher
boots against `old.tsetmc.com/tsev2/data/MarketWatchInit.aspx`, whose
fast-view section TSETMC now also serves in an **extended 17-field
variant** (1.8.0's parser accepts only 3 or 16 fields). When your request
lands on such a backend the watcher fails immediately with
`DataParsingError: fast-view section has 17 fields` — retries can hit a
different variant and succeed, so treat a watcher start as retryable. The
bulk snapshot APIs (`get_market_snapshot`, `get_live_market`) use a
different MarketWatchPlus endpoint and are unaffected. Watch for a fixed
package release if you depend on the watcher in production.

`MarketEvent` is a dataclass. The fields that matter for consumers:
`kind` (`"initial"`, `"update"`, `"heartbeat"`), `sequence`, `fetched_at`,
`trade_date`, `snapshot`, `changed_inscodes`, `changed_order_levels`,
`market_state_changed`, `messages`, `state_changes`, `notification_tokens`,
`retry_count`, `retry_error`, `persistence_status`, `persistence_error`.
Sequences are strictly increasing per session — use them as a cursor.

```python
import algotik_tse as att

watcher = att.watch_market(interval=2.0, max_updates=5)
for event in watcher:
    if event.kind == "update":
        print(event.sequence, event.changed_inscodes[:5])
```

## get_market_messages()

```python
msgs = att.get_market_messages(flow=0, top=20, since_id=None, *,
                               archive_to=None)
```

Supervisor (ناظر) messages for one market `flow` (0 = بورس, 1 = فرابورس;
integer board code). `since_id` resumes from a message id. `archive_to`
writes each fetched page into your SQLite store as it runs. Recent history of
archived messages is read back with `get_market_messages_history()`.

## get_instrument_state_changes()

```python
changes = att.get_instrument_state_changes(top=20, since_id=None, *,
                                            archive_to=None)
```

Most recent instrument state transitions (halt/آزاد/توقف, and similar state
flags), newest first, optionally resumed by `since_id` and archived on the
fly. Historical reads: `get_instrument_state_changes_history()`.

## get_market_overview()

```python
overview = att.get_market_overview(flow=0, *, archive_to=None)
```

The official one-row market summary for a board: index value and change,
breadth counts, total value/volume/trade counts, and session metadata.
`archive_to` persists the row (see `local-history.md`). This is the canonical
source for "how did the market do today" — don't rebuild it by summing
instruments, because the official numbers exclude some instruments.

## get_market_breadth()

```python
breadth = att.get_market_breadth(symbol=None, flow=None, sector=None,
                                 traded_only=False,
                                 include_base_market=True,
                                 instrument_types=None)
```

Advancers/decliners/unchanged, A/D line, and positive/negative counts —
one row. Filters let you scope breadth to a `flow` (market board), a
`sector`, specific `instrument_types` (e.g. `(300, 303, 309)` for equities),
`traded_only=True` to count only instruments that printed a trade, and
`include_base_market=False` to drop بازار پایه names that usually distort
breadth.

## get_sector_flow()

```python
flow = att.get_sector_flow(symbol=None, flow=None, sector=None,
                           traded_only=False, include_base_market=True,
                           instrument_types=None)
```

Per-industry breadth plus net حقیقی/حقوقی flow aggregates: one row per
sector with index change, advance/decline counts and estimated net
individual flow (value-based). Same filter vocabulary as
`get_market_breadth()`. Use it for "which industries is the money flowing
into" questions; the memberships of industries overlap, so sector rows are
not additive to a market total.

## Live vs history parity

| Data | Live API | History API |
|---|---|---|
| market summary | `get_market_overview()` | `get_market_overview_history()` |
| breadth | `get_market_breadth()` | `get_market_breadth_history()` |
| sector flow | `get_sector_flow()` | `get_sector_flow_history()` |
| messages | `get_market_messages()` | `get_market_messages_history()` |
| state changes | `get_instrument_state_changes()` | `get_instrument_state_changes_history()` |
| live view | `get_live_market()` | `get_live_market_history()` |

The history column exists **only for what you or the library archived** —
there is no server-side history for these analytics. Recording starts when
you start recording; no backfill is claimed. Check the `NoBackfill` /
coverage flags in `df.attrs` when reading history back.
