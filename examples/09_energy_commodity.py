"""Energy exchange and IME commodity markets.

Run:  python examples/09_energy_commodity.py
"""

import algotik_tse as att


def main():
    auctions = att.get_energy_auctions(status="all", board="all")
    print("energy auction notices:", len(auctions))

    overview = att.get_energy_market_overview(market="all")
    print("energy overview rows:", len(overview))

    power = att.list_power_instruments(market="all")
    print("power contracts:", len(power))

    board = att.get_commodity_market(kind="all")
    print("IME board rows:", len(board))
    if "ValueUnit" in board.columns:
        print("value unit column present:",
              board["ValueUnit"].dropna().unique()[:3])


if __name__ == "__main__":
    main()
