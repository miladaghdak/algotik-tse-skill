"""Quickstart: identity, history, client-type flow.

Run:  python examples/01_quickstart.py
"""

import algotik_tse as att


def main():
    # Resolve the exact instrument once, then reuse the InsCode.
    # (auto resolution is the robust pattern — see SKILL.md contract 1)
    ref = att.resolve_instrument("فولاد")
    print("resolved:", ref.symbol, "|", ref.name, "|", ref.ins_code)

    # Adjusted daily history, last 30 sessions.
    hist = att.get_history(ins_code=ref.ins_code, limit=30, progress=False)
    print("history rows:", len(hist))
    print(hist.tail(3).to_string())

    # Retail vs institutional flow for the same window.
    flow = att.get_client_type(ins_code=ref.ins_code, limit=30,
                               progress=False)
    print("client-type rows:", len(flow))
    print(flow.tail(3).to_string())


if __name__ == "__main__":
    main()
