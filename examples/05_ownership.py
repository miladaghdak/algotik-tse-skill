"""Ownership: shareholders, history, network, concentration.

Run:  python examples/05_ownership.py
"""

import algotik_tse as att


def main():
    ref = att.resolve_instrument("فولاد")

    holders = att.get_shareholders(ins_code=ref.ins_code)
    print("current major holders:\n", holders.to_string())

    # Dated snapshots on effective dates — start/end are required here.
    hist = att.get_shareholder_history(ins_code=ref.ins_code,
                                       start="1405-06-01",
                                       end="1405-07-01",
                                       frequency="daily",
                                       max_requests=20, progress=False)
    print("shareholder snapshot dates:", len(hist))

    # Market-wide recent changes board (last 5 sessions by default).
    changes = att.get_major_shareholder_changes(days=5, progress=False)
    print("recent change rows:", len(changes))

    network = att.get_shareholder_network(progress=False)
    print("network edges:", len(network))

    conc = att.get_ownership_concentration(ins_code=ref.ins_code,
                                           progress=False)
    print("concentration:\n", conc.to_string())


if __name__ == "__main__":
    main()
