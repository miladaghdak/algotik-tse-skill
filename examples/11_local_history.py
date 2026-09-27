"""Local SQLite history: record a watchlist view, read it back, check the file.

Run:  python examples/11_local_history.py

Two live-tested scale notes (1.8.0), baked into this example:

1. save_market_snapshot() on the *whole* live market (~3.7k rows x 163
   columns) is dominated by pandas attrs deepcopy and effectively hangs;
   it finishes in seconds on a filtered watchlist frame. Record what you
   actually monitor, not the entire market.
2. watch_market() can fail to boot with
   ``DataParsingError: fast-view section has 17 fields`` when TSETMC's
   MarketWatchInit lands you on an extended payload variant; retrying
   can succeed. The example tolerates both outcomes.
"""

import tempfile
import time
from pathlib import Path

import algotik_tse as att


def main():
    store = Path(tempfile.mkdtemp(prefix="att_history_")) / "history.db"

    live = att.get_live_market()
    watchlist = live.nlargest(30, "Value")  # top names by traded value
    print("recording a", len(watchlist), "name watchlist")

    t0 = time.time()
    att.save_market_snapshot(str(store), snapshot=watchlist)
    print("saved in %.1fs -> %s" % (time.time() - t0, store))

    # Structural health check of the store (returns a report dict).
    report = att.check_market_history(str(store))
    print("history check ok:", bool(report))

    rows = att.load_market_snapshots(str(store), limit=5)
    print("loaded rows:", len(rows))

    summary = att.get_market_snapshot_summary_history(str(store), limit=5)
    print("snapshot summary rows:", len(summary))

    # Watcher-based recording: tolerate the 17-field fast-view variant.
    try:
        watcher = att.watch_market(interval=1.0, max_updates=2,
                                   record_to=str(store),
                                   record_heartbeats=False)
        for event in watcher:
            print("watcher event:", event.kind, "| seq", event.sequence,
                  "| persisted:", event.persistence_status)
    except att.DataParsingError as exc:
        print("watcher could not boot (known 1.8.0 payload variant):", exc)
        return

    events = att.get_market_event_history(str(store), limit=5)
    print("recorded events:", len(events))


if __name__ == "__main__":
    main()
