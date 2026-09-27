"""Market analytics: overview, breadth, sector flow, regime, calendar.

Run:  python examples/03_market_analytics.py
"""

import algotik_tse as att


def main():
    overview = att.get_market_overview()
    print("overview:\n", overview.to_string())

    breadth = att.get_market_breadth(traded_only=True)
    print("breadth:\n", breadth.to_string())

    sector = att.get_sector_flow(traded_only=True)
    print("sector rows:", len(sector))

    calendar = att.get_trading_calendar(limit=10)
    print("next sessions:", len(calendar))

    # Explainable regime from five components; empty live data is fine —
    # the regime call reports which components were available.
    regime = att.get_market_regime(progress=False)
    print("regime:", regime.to_string())


if __name__ == "__main__":
    main()
