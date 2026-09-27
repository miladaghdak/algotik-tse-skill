"""TGJU assets: currency, gold, coin price history.

Run:  python examples/10_tgju.py
"""

import algotik_tse as att


def main():
    assets = att.list_tgju_assets()
    print("TGJU series in catalog:", len(assets))
    by_cat = assets.groupby("Category", dropna=False).size()
    print(by_cat.to_string())

    usd = att.get_tgju_history("dollar", limit=30, progress=False)
    print("dollar rows:", len(usd))
    print(usd.tail(3).to_string())

    gold = att.get_currency("طلای ۱۸ عیار", limit=10, progress=False)
    print("gold rows:", len(gold))


if __name__ == "__main__":
    main()
