"""Symbol universe: board lists, instrument master, changes, ambiguity.

Run:  python examples/12_symbol_universe.py
"""

import algotik_tse as att


def main():
    bourse = att.get_symbols(bourse=True, farabourse=False, payeh=False,
                             progress=False)
    print("bourse symbols:", len(bourse))

    options = att.get_symbols(bourse=False, farabourse=False, payeh=False,
                              options=True, progress=False)
    print("option symbols on boards:", len(options))

    master = att.get_instrument_master(progress=False)
    print("instrument master rows:", len(master))

    # Ambiguity is real: a ticker can match more than one instrument.
    try:
        ref = att.resolve_instrument("شتران")
        print("unique match:", ref.ins_code, ref.name)
    except att.AmbiguousSymbolError as exc:
        print("ambiguous ticker caught — pass ins_code. Detail:", str(exc)[:120])

    # Text hygiene before resolving user input.
    cleaned = att.normalize_instrument_text("فولاد\u200cمبارکه")
    print("normalized:", cleaned)


if __name__ == "__main__":
    main()
