"""Funds, ETFs and bonds: the three fund universes and the debt board.

Run:  python examples/08_funds_etfs_bonds.py
"""

import algotik_tse as att


def main():
    registry = att.list_funds(progress=False)
    print("registry funds:", len(registry))

    equity = att.list_funds(fund_type="equity", progress=False)
    print("equity funds:", len(equity))

    listed = att.list_listed_funds(progress=False)
    print("listed funds:", len(listed))

    etfs = att.list_etfs(progress=False)
    print("ETFs:", len(etfs))
    if "NAV_Discount" in etfs.columns:
        # NAV_Discount is percent: negative = discount, positive = premium
        worst = etfs.nsmallest(3, "NAV_Discount")
        print("deepest discounts:\n", worst.to_string())

    debt = att.list_debt_instruments(active_only=True, progress=False)
    print("active debt instruments:", len(debt))


if __name__ == "__main__":
    main()
