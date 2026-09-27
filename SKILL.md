---
name: algotik-tse
version: 1.0.0
description: Use the algotik_tse Python package (v1.8.0) for Tehran Stock Exchange (TSETMC), Iran Fara Bourse, Iran Energy Exchange and IME commodity data, plus TGJU currency/coin/gold prices. Triggers on Persian ticker symbols (فولاد, شتران, خودرو, اهرم), historical OHLCV and adjusted prices, حقیقی/حقوقی client-type flow, intraday ticks and candles, trades, order book and صف (queue), market snapshots and watcher streams, breadth/sector flow/regime/market map, trading calendar, industry indices and membership analytics, major shareholders and ownership network, options chains with Black-Scholes math, اخزا treasury bills and yield curves, اراد/گام debt yields, ETFs, funds, bonds, energy auctions, futures curves, cash-and-carry. Do not use for non-Iranian markets.
---

# AlgoTik TSE (algotik_tse 1.8.0)

A TSETMC market-data package for Python. Everything here was verified against
`algotik-tse==1.8.0` (installed from PyPI, cross-checked against
github.com/mohsenalipour/algotik_tse at the 1.8.0 tag) and against live
TSETMC/TGJU/IME endpoints. The package author is Mohsen Alipour; it is
GPL-3.0 licensed.

## Package facts

- PyPI name: `algotik-tse` — import as `import algotik_tse as att`
- Version documented here: **1.8.0** (check `att.__version__` at runtime)
- Python 3.8+
- Dependencies: `requests`, `pandas`, `numpy`, `persiantools`, `urllib3`,
  `lxml`, `openpyxl`. Optional `plotly>=5.0` (extras `[visualization]`) only
  for `plot_market_map()`.
- 167 exported names in `att.__all__`: 150 functions, 11 classes, settings
  object, and a few constants.

```bash
pip install --upgrade algotik-tse
```

## Ten contracts to respect before writing code

These are the rules the package actually enforces. Skipping them is what
produces broken or silently wrong code.

**1. Identity is InsCode, not the Persian ticker.** Symbols collide —
حق تقدم, options, funds and even two same-named instruments can share a
ticker (during verification `شتران` itself matched two same-rank
instruments for part of the day). Resolve once, then pass `ins_code=`
everywhere:

```python
ref = att.resolve_instrument("فولاد")
# InstrumentRef(ins_code='46348559193224090', symbol='فولاد',
#               name='فولاد مباركه اصفهان', asset_type='unknown'|'equity',
#               is_active=True, provenance='tsetmc_search_exact', ...)
hist = att.get_history(ins_code=ref.ins_code, limit=30, progress=False)
row = att.get_live_symbol(ins_code=ref.ins_code)
```

`resolve_instrument()` raises `AmbiguousSymbolError` instead of guessing; catch
it and ask the user or pass `ins_code` directly. Valid `asset_type` values:
`auto, equity, index, industry, fund, bond, option`.

**Live-verified gotcha (1.8.0):** combining a **symbol** with an explicit
`asset_type` (e.g. `resolve_instrument("فولاد", asset_type="equity")` or
`get_history("فولاد", asset_type="equity")`) consults the point
`GetInstrumentInfo` record, whose `lastDate` status field TSETMC serves as
`0` outside the finalized-snapshot state — from just after the 15:00 close
through the evening (pre-open mornings it reads `1`). In that window those
calls fail (`StockNotFoundError` / legacy APIs print "Stock Not Found" and
return `None`) even for actively trading names. Robust everywhere: resolve
with `auto`, pin `ins_code`, and keep data calls on the default
`asset_type`; for typed resolution pass a snapshot —
`resolve_instrument(sel, asset_type=..., snapshot=att.get_market_snapshot())`
— or opt out with `require_active=False`. Full matrix in
`references/instrument-identity.md`.

`validate_ins_code()` accepts a positive int or a 1–20 digit ASCII string
and returns the canonical string. `normalize_instrument_text()` fixes ي/ی
and ك/ک and spacing variants, but performs **no fuzzy joins**.

**2. Dates are inclusive Jalali or Gregorian strings.** `start`/`end` accept
`1403-05-01` or `2024-07-22`. Output date format via `date_format=`:
`'jalali'` (default), `'gregorian'`, or `'both'`.

**3. `include_today` is opt-in and never fabricates a row.** With
`include_today=False` (default) no extra live request happens. With
`include_today=True` today's valid observation is appended; a stale snapshot
may be accepted but `attrs` will flag it. A halted symbol or a failed live
fetch never produces a fake today-row — history comes back with the reason in
`attrs`/warnings.

**4. Not everything is a DataFrame.**

| Family | Return |
|---|---|
| history, client-type, trades, order book, fundamentals, lists | `pandas.DataFrame` (legacy APIs may return `None` on error) |
| `market_watch()` / `get_market_snapshot()` | `dict` (`stocks`, `order_book`, freshness flags, timestamps) |
| `get_options_chain()` | `dict` with `calls` and `puts` |
| `resolve_instrument()` | immutable `InstrumentRef` |
| `watch_market()` / `MarketWatcher` | iterator of `MarketEvent` |
| `get_yield_curve()` / `build_yield_curve()` | `YieldCurve` object |
| Black–Scholes helpers | scalar / tuple / dict depending on function |

Empty DataFrames keep the same columns and dtypes as non-empty ones.

**5. Metadata lives in `df.attrs`.** Source, freshness, coverage, partial
flags, request budgets — always read `df.attrs` before trusting a result:

```python
df = att.get_live_market("فولاد")
print(df.attrs)  # trade_date, fetched_at, is_realtime_fresh, is_partial, ...
```

**6. `Close` means different things in different feeds.** Live: `Last` is the
last trade, `Close` is the TSETMC closing (پایانی) price. History: `Close` is
the day's last trade; the closing price is `Final`, visible with
`output_type="full"`. With `auto_adjust=True` (default) OHLC and `Final` are
split/dividend-adjusted; with `auto_adjust=False` they are raw and an
`Adj Close` column is added. Never join live and history by column name
alone — with `include_today=True` live `Last` maps to history `Close`.

**7. Freshness filters can legitimately return zero rows.** Bulk endpoints
that screen "only today's published data" (e.g. `get_market_fundamentals()`,
`get_treasury_yields()`) return an empty frame when TSETMC hasn't published a
fresh snapshot for the current session. Pass `allow_stale=True` /
`include_stale=True` to get the last published snapshot. Similarly, industry
membership (`get_industry_snapshot`, `get_industry_members`) reads
`ClosingPrice/GetIndexCompany`, which TSETMC empties outside publication
windows (pre-market, evenings); use `include_empty=True` and inspect
`df.attrs['empty_industries']` instead of assuming an error.

**8. One HTTP client, rate-limited, GET-only, source-bounded.** All requests
go through `safe_get()`: `settings.rate_limit_delay` (default 0.3s) spaces
request starts globally, retries are GET-only with backoff on 429/5xx, and
every URL is validated against an allow-list — TSETMC, IFB (`ifb.ir`), TGJU
and IME hosts only. **Codal is outside the boundary and raises
`UnsupportedDataSourceError`** — that is why `get_introduction()` /
`stock_introduction()` always raise. Same-origin redirects only, cross-origin
redirects are rejected. Don't bypass this with raw `requests`.

**9. Errors are typed.** Catch these, not bare `Exception`:

```text
AlgotikTSEError
├── AmbiguousSymbolError      # selector matched >1 instrument → pass ins_code
├── ConnectionError           # provider unreachable after retries
├── DataParsingError          # provider schema changed
├── InvalidParameterError     # your arguments are wrong
├── StockNotFoundError        # selector matched nothing
└── UnsupportedDataSourceError# outside the supported source boundary
```

Legacy functions may return `None` plus a console message instead of raising —
each function's reference notes this.

**10. Standard names win.** Use `get_*` names in new code. The legacy aliases
are kept for backward compatibility only:

| Legacy | Canonical |
|---|---|
| `stock()` | `get_history()` |
| `stock_RI()` | `get_client_type()` |
| `stock_RL()` | `get_client_type()` (same family, live variant) |
| `stock_capital_increase()` | `get_capital_increase()` |
| `stock_intraday()` | `get_intraday()` |
| `stockdetail()` | `get_detail()` |
| `stock_information()` | `get_info()` |
| `stock_statistics()` | `get_stats()` |
| `stock_introduction()` | `get_introduction()` (always raises) |
| `stocklist()` | `get_symbols()` |
| `shareholders()` | `get_shareholders()` |
| `currency_coin()` | `get_currency()` / `get_tgju_history()` |
| `market_watch()` | `get_market_snapshot()` |
| `market_client_type()` | `get_market_client_type()` |
| `market_data()` | deprecated, redirects to `market_watch()` |

## Settings

Singleton at `att.settings` — tune before first request:

```python
att.settings.ssl_verify = True      # default; opt out only with a broken CA
att.settings.timeout = 10            # seconds
att.settings.max_retries = 3
att.settings.retry_backoff_factor = 0.3
att.settings.rate_limit_delay = 0.3  # minimum spacing between request starts
att.settings.market_snapshot_freshness_seconds = 120.0
att.settings.industry_membership_cache_ttl = 3600.0
att.settings.order_book_max_requests = 250
att.settings.trade_max_requests = 250
```

Changing retry settings needs `reset_session()` (from
`algotik_tse.http_client`); timeout/verify/delay take effect immediately.

## API map — where to read more

`references/` carries the deep material, one file per domain. Read the file
that matches the task, not all of them.

| When the task involves… | Read |
|---|---|
| OHLCV history, adjusted prices, returns, حقیقی/حقوقی, intraday, trades | `references/price-and-flow.md` |
| Symbol resolution, detail/info/stats, instrument master, `get_symbols` filters | `references/instrument-identity.md` |
| Live snapshots, live symbol/market, order book, صف, trade feeds | `references/live-market.md` |
| Watcher streams, supervisor messages, overview/breadth/sector flow | `references/market-stream.md` |
| Local SQLite history, snapshot archiving, event recording | `references/local-history.md` |
| Calendar, activity, index impact, TOP/pre-open, comparisons, regime, market map, fundamentals | `references/market-analytics.md` |
| Industry indices, membership, correlation, concentration, rankings | `references/industries.md` |
| Shareholders, ownership network, capital increases, price adjustments | `references/ownership.md` |
| Options chains, option market, Black–Scholes, IV, PCR | `references/options.md` |
| اخزا / اراد / گام, bond math, yield curves, IFB tables | `references/fixed-income.md` |
| ETFs, funds (registry + listed), bonds, debt instruments | `references/funds-etfs-bonds.md` |
| Energy exchange auctions, power market, IME commodity board, futures curves | `references/energy-commodity.md` |
| Dollar, euro, gold, silver, coin prices from TGJU | `references/tgju-assets.md` |
| HTTP client internals, safe_get contract, rate limiting, source boundary | `references/http-client.md` |

## Core usage patterns

```python
import algotik_tse as att

# Identity first, then data
ref = att.resolve_instrument("شتران", asset_type="equity")

# Adjusted daily history, last 30 sessions
hist = att.get_history(ins_code=ref.ins_code, asset_type="equity",
                       limit=30, progress=False)

# Retail vs institutional flow (حقیقی/حقوقی)
flow = att.get_client_type(ins_code=ref.ins_code, limit=30, progress=False)

# Whole market in one request
snap = att.get_market_snapshot()   # dict: snap["stocks"], snap["order_book"], ...
live = att.get_live_market()       # one row per instrument, 160+ columns
```

Batch/multi-symbol calls accept lists; `progress=False` keeps logs clean in
scripts and notebooks. In production, prefer `ins_code=` over symbol strings.
`save_to_file=True` writes CSVs — `save_path` is a **folder**, the filename
is derived from the symbol.

## Behavioral rules

- Never invent column names or return keys. When unsure of a schema, print
  `list(df.columns)` or `df.attrs` and work from the real output.
- Preserve the user's naming convention (Persian vs English symbol) and their
  exact date range; don't silently widen or shift windows.
- Don't re-implement rate limiting, retries, or HTTP around the package —
  everything already goes through one bounded client.
- Don't chase Codal (company publisher) data through this package; it is
  deliberately outside the source boundary.
- For long histories, use `limit`/`start`/`end` rather than fetching
  everything and slicing locally.
- Freshness-sensitive screens (`get_market_fundamentals`,
  `get_treasury_yields`, industry membership) should be wrapped with an
  `allow_stale`/`include_empty` fallback and an explanation to the user when
  the fresh snapshot is empty.

## Verification

This skill ships with a test suite. `pytest` (offline checks: API inventory
one-to-one coverage, snippet compilation, deterministic math) and
`pytest -m online` (live TSETMC/TGJU/IME smoke). See `README.md` for the
verified results and `AUDIT.md` for the audit this skill was built from.
