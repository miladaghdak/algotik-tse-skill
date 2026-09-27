"""Live market: snapshot, live rows, order book, queue, trades.

Run:  python examples/02_live_market.py
"""

import algotik_tse as att


def main():
    snap = att.get_market_snapshot()
    print("fresh:", snap["is_realtime_fresh"], "| age:",
          snap["snapshot_age_seconds"], "s")
    print("stocks in snapshot:", len(snap["stocks"]))

    live = att.get_live_market("فولاد")
    print("live columns:", len(live.columns))

    book = att.get_order_book("فولاد")
    print("order-book levels:\n", book.to_string())

    queue = att.get_queue("فولاد", side="both", strict=False)
    print("queue rows:", len(queue))

    trades = att.get_live_trades("فولاد", progress=False)
    print("today's trades:", len(trades))


if __name__ == "__main__":
    main()
