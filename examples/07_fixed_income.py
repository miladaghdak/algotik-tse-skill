"""Fixed income: debt yields, treasury snapshot, curve, math.

Run:  python examples/07_fixed_income.py
"""

import algotik_tse as att


def main():
    debt = att.get_debt_yields()
    print("IFB reference yield rows:", len(debt))
    for dt in ("treasury", "erad", "gam"):
        rows = att.get_debt_yields(debt_type=dt)
        print(f"  {dt}: {len(rows)} rows")

    # Freshness: outside trade windows the fresh snapshot is empty on
    # purpose — fall back to the last traded state.
    yields = att.get_treasury_yields(include_stale=True)
    print("treasury yield rows (stale allowed):", len(yields))

    curve = att.get_yield_curve(include_stale=True)
    nodes = curve.nodes  # DataFrame, one row per curve instrument
    print("curve nodes:", len(nodes))
    cols = ["Symbol", "Tenor", "ContinuousZeroRate", "IsStale"]
    print(nodes[cols].to_string())

    # Pure math: اخزا-style yield and day counts need no network.
    maturity = att.parse_treasury_maturity("اخزا020322")
    print("اخزا020322 matures on:", maturity)


if __name__ == "__main__":
    main()
