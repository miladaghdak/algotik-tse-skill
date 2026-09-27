# Instrument identity, detail pages and the symbol universe

Scope: resolving a Persian ticker to an exact instrument, the reference
metadata APIs, and enumerating what trades on the boards. Read this before
writing any code that maps a user-typed symbol to data.

## resolve_instrument()

```python
ref = att.resolve_instrument(selector=None, *, ins_code=None,
                             asset_type="auto", snapshot=None,
                             require_active=True)
```

Returns an immutable `InstrumentRef` with the fields `ins_code`, `symbol`,
`name`, `asset_type`, `is_active`, `provenance` and `selector`. This is the
only supported way to turn ambiguous text into an exact instrument.

Behavior rules, all verified against live TSETMC:

- Exact match wins. If a selector matches multiple instruments with the same
  rank it raises `AmbiguousSymbolError` with the candidate list — the
  library never guesses. This is not theoretical: during verification
  `شتران` matched two active same-rank instruments for part of a session
  (a same-symbol newcomer alongside the refinery), so code that
  hard-codes `att.get_history("شتران")` can break depending on the day's
  snapshot.
- `asset_type` narrows the search: `auto, equity, index, industry, fund,
  bond, option` — **but see the status-window warning below before
  combining an explicit type with a symbol selector.**
- `ins_code=` short-circuits search entirely — deterministic, use in
  production.
- `require_active=False` allows delisted/expired instruments (useful for
  historical options and حق تقدم that expired).
- `snapshot=` accepts a previously fetched `market_watch()` snapshot so you
  can resolve offline against data you already hold.
- The resolver does not translate Persian/Arabic digits inside identifiers,
  and never fuzzy-joins by company name.

### Verified status-window behavior (live-tested, 1.8.0)

`resolve_instrument` consults the point `GetInstrumentInfo` record whenever
it must **verify a requested asset type or confirm an explicit InsCode**
outside a snapshot, and treats that record's status as authoritative. The
status is read from the record's `lastDate` field — and TSETMC serves
`lastDate: 0` for the whole market outside the finalized-snapshot state
(observed continuously from just after the 15:00 close through the
evening; pre-open mornings it served `1`). When the field reads 0 the
resolver maps it to `is_active=False` and rejects the selector:

```python
att.resolve_instrument("فولاد", asset_type="equity")
# StockNotFoundError: No active instrument matched 'فولاد'   (window)
att.get_history("فولاد", asset_type="equity")
# prints "Stock Not Found, Please try again ..." and returns None
```

The same window also affects `resolve_instrument(ins_code=...)` without a
snapshot. What is **unaffected**: `asset_type="auto"` resolution, and all
data calls that pass a symbol or `ins_code` with the default `auto`.

Robust patterns (all live-verified inside the broken window):

```python
ref = att.resolve_instrument("فولاد")                    # auto: always works
hist = att.get_history(ins_code=ref.ins_code)              # ins_code + auto

# typed resolution that survives the window:
snap = att.get_market_snapshot()
ref = att.resolve_instrument("فولاد", asset_type="equity", snapshot=snap)

# explicit opt-out when you don't need the activity gate:
ref = att.resolve_instrument("فولاد", asset_type="equity",
                              require_active=False)        # is_active=False reported
```

Rule of thumb: pin `ins_code` early, keep `asset_type` at `auto` for data
calls, and pass a snapshot when you need typed resolution. Treat
`symbol + explicit asset_type` as a fragile combination — fine in
interactive use against a finalized market, risky in anything that runs
on a clock.

```python
import algotik_tse as att

# robust resolution: auto, then pin the InsCode
ref = att.resolve_instrument("فولاد")
print(ref.ins_code, ref.name, ref.asset_type, ref.is_active)

INS_FOOLAD = "46348559193224090"  # فولاد مبارکه اصفهان
hist = att.get_history(ins_code=INS_FOOLAD, limit=30, progress=False)
```

## validate_ins_code() and normalize_instrument_text()

```python
att.validate_ins_code(value)          # -> canonical ASCII digit string
att.normalize_instrument_text(value)  # -> normalized Persian text
```

`validate_ins_code` accepts a positive int or a 1–20 digit ASCII string
(outer whitespace is trimmed) and returns the canonical string; it
rejects floats, bools, zero, Persian/Arabic digits, signs and
**inner** whitespace (`"4 6"` fails). Identifiers are opaque provider
keys, not display text.
`normalize_instrument_text` unifies ي/ی and ك/ک, collapses spacing variants
and trims — use it to clean user input before resolving, not to join
datasets.

## get_detail(), get_info(), get_stats(), get_introduction()

```python
att.get_detail(symbol="", *, ins_code=None, asset_type="auto", **kwargs)
att.get_info(symbol="", *, ins_code=None, asset_type="auto", **kwargs)
att.get_stats(symbol="", *, ins_code=None, asset_type="auto", **kwargs)
att.get_introduction(symbol="", *, ins_code=None, asset_type="auto", **kwargs)
```

- `get_detail()` — the full TSETMC instrument detail page (company name,
  ISIN-ish identifiers, market/board, sector codes…). Frame of ~15 rows.
- `get_info()` — trading-relevant information: EPS estimates, sector P/E,
  PSR, price thresholds (upper/lower bands), base volume and similar
  per-instrument fields. Frame of ~46 rows.
- `get_stats()` — statistics and rankings for the instrument (rank by volume,
  value, trades, day range, 52-week context). Frame of ~88 rows.
- `get_introduction()` — **always raises `UnsupportedDataSourceError`**.
  Company introduction pages are a Codal product and Codal sits outside the
  package's source boundary. The name is kept importable so old code fails
  loudly instead of silently crossing providers.

Legacy names: `stockdetail()`, `stock_information()`, `stock_statistics()`,
`stock_introduction()`.

## get_symbols()

```python
att.get_symbols(bourse=True, farabourse=True, payeh=True,
                haghe_taqadom=False, sandogh=False, bonds=False,
                options=False, mortgage=False, commodity=False,
                energy=False, payeh_color=None, output="dataframe",
                progress=True, **kwargs)
```

The board-level symbol list. Board switches: `bourse` (بورس), `farabourse`
(فرابورس), `payeh` (بازار پایه), `haghe_taqadom` (حق تقدم), `sandogh`
(صندوق‌ها), `bonds` (اوراق), `options` (اختیار معامله), `mortgage`
(اوراق رهن), `commodity` (گواهی سپرده کالا), `energy` (اوراق بورس انرژی).
`payeh_color` filters پایه by tier: `'زرد'`, `'نارنجی'`, `'قرمز'`.
`output` is `'dataframe'` or `'list'`. Legacy name: `stocklist()`.

The result is a snapshot of boards, not a reference table — for exact
identifiers use `get_instrument_master()`.

## get_instrument_master() and get_instrument_changes()

```python
master = att.get_instrument_master(active=None, market=None,
                                   asset_type=None, progress=True)
diff = att.get_instrument_changes(previous, current=None, progress=True)
```

`get_instrument_master()` returns the full reference table (13k+ rows live)
with `InsCode`, ISIN-like identifiers, symbol, name, market and asset type.
Pass `active=True/False` to filter by listing state, `market=` to filter
boards. Keep this frame around: it is the cheapest way to enumerate
instruments and their canonical IDs.

`get_instrument_changes()` diffs two master snapshots (or the master against
a live fetch when `current=None`) and reports added, removed and changed
instruments — the right way to detect new listings and symbol changes
between sessions.

```python
master = att.get_instrument_master(progress=False)
snapshot_a = master  # keep a copy per session
# next session:
changes = att.get_instrument_changes(snapshot_a, progress=False)
```

## Which API for which "list symbols" question

- "What trades on بورس?" → `get_symbols(bourse=True, ...)`
- "Give me every instrument ID ever" → `get_instrument_master()`
- "What changed since yesterday?" → `get_instrument_changes(previous)`
- "Resolve this ticker exactly" → `resolve_instrument()`
- ETFs / funds / bonds specifically → use the dedicated lists in
  `funds-etfs-bonds.md`, not `get_symbols`.
