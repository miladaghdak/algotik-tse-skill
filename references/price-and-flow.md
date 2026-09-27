# Price history, client-type flow, intraday and trades

Scope: daily OHLCV (adjusted and raw), حقیقی/حقوقی (retail vs institutional)
history, intraday ticks and candles, and per-trade data — the workhorse APIs
of the package. Live variants of trades/order book are in
`live-market.md`.

All functions in this family return a `pandas.DataFrame` (or `None` for some
legacy paths on failure). History is server-side TSETMC data; `start`/`end`
are inclusive and accept Jalali (`1403-05-01`) or Gregorian (`2024-07-22`)
strings.

## get_history()

```python
att.get_history(symbol="", start=None, end=None, limit=0, raw=False,
               auto_adjust=True, output_type="standard", date_format="jalali",
               progress=True, save_to_file=False, dropna=True,
               adjust_volume=False, return_type=None, ascending=True,
               save_path=None, include_today=False, *,
               ins_code=None, asset_type="auto", **kwargs)
```

Historical OHLCV for one symbol, a list of symbols, or an `ins_code`. Legacy
name: `stock()`.

Key parameters:

- `symbol` — Persian ticker or list. With `ins_code=` you can omit it.
- `start`/`end` — inclusive dates, Jalali or Gregorian strings.
- `limit` — last N sessions; used when `start`/`end` are `None`.
- `auto_adjust=True` (default) — OHLC (and `Final` when present) are adjusted
  for splits and dividends. `raw=True` is the unmodified TSETMC closing-price
  series with an added adjustment-factor column.
- `adjust_volume` — additionally adjust volume.
- `output_type` — `"standard"` (open/high/low/close/volume) or `"full"`
  (adds `Final` = official closing price and more).
- `return_type` — request specific derived output (e.g. percentage returns);
  leave as `None` unless you know the value.
- `dropna`, `ascending`, `date_format` — row hygiene; `date_format` accepts
  `'jalali'`, `'gregorian'`, `'both'`.
- `include_today` — opt-in live observation for today (see SKILL.md §3).
- `save_to_file=True` + `save_path="exports"` — CSV per symbol;
  **`save_path` is a folder**, filename is derived from the symbol.

Column semantics: `Close` is the last trade of the day; the official closing
price (پایانی) is `Final` and only appears with `output_type="full"`. Don't
treat the adjusted/unadjusted price gap as a cash dividend — TSETMC does not
publish a reliable DPS for adjustment events and the package never infers
one.

Multi-symbol input returns a dict of DataFrames keyed by symbol.

```python
import algotik_tse as att

hist = att.get_history("فولاد", start="1403-01-01", end="1403-06-31",
                       progress=False)
wide = att.get_history(["فولاد", "شتران"], limit=90, progress=False)
raw = att.get_history("خودرو", raw=True, auto_adjust=False, limit=10,
                      progress=False)
```

## get_client_type()

```python
att.get_client_type(symbol="", start=None, end=None, limit=0, raw=False,
                    output_type="standard", date_format="jalali",
                    progress=True, save_to_file=False, dropna=True,
                    ascending=True, save_path=None, include_today=False, *,
                    ins_code=None, asset_type="auto", **kwargs)
```

Daily retail (حقیقی) vs institutional (حقوقی) buy/sell volumes, counts and
values per symbol. Legacy names: `stock_RI()` and `stock_RL()` — same
underlying data, `stock_RL` is kept for compatibility. With no date bounds,
the legacy `values` kwarg (e.g. `values=100`) limits to the last N days; pass
`limit` instead in new code.

Columns (12, live-verified): `N_buy_retail`, `N_buy_institutional`,
`N_sell_retail`, `N_sell_institutional`, `Vol_buy_retail`,
`Vol_buy_institutional`, `Vol_sell_retail`, `Vol_sell_institutional`,
`Val_buy_retail`, `Val_buy_institutional`, `Val_sell_retail`,
`Val_sell_institutional`, indexed by `J-Date`. Buyer-power style ratios
are not precomputed — derive what you need, e.g. individual buy value
divided by individual sell value.

```python
flow = att.get_client_type("فولاد", limit=30, progress=False)
power = flow["Val_buy_retail"] / flow["Val_sell_retail"]
```

## get_intraday()

```python
att.get_intraday(symbol="شتران", interval="1min", start=None, end=None,
                 progress=True, **kwargs)
```

Intraday ticks or resampled candles for one trading day (default: the latest
available session). Legacy name: `stock_intraday()`.

- `interval` — `'tick'`, `'1min'`, `'5min'`, `'15min'`, `'30min'`, `'1h'`,
  `'4h'`, `'12h'`. Anything else raises `InvalidParameterError`.
- `start`/`end` — a single day each (Jalali or Gregorian); TSETMC serves
  intraday per session, not ranges.

```python
ticks = att.get_intraday("شتران", interval="tick", progress=False)
candles = att.get_intraday("فولاد", interval="5min", start="1404-05-20",
                           progress=False)
```

## get_trades() and get_live_trades()

```python
att.get_trades(symbol=None, *, ins_code=None, start=None, end=None,
               include_canceled=False, max_requests=None, raw=False,
               progress=True)

att.get_live_trades(symbol=None, *, ins_code=None, include_canceled=False,
                    max_requests=None, raw=False, progress=True)
```

Per-trade (ریز معاملات) data. `get_trades()` pages through historical days;
`get_live_trades()` returns today's tape. Both are bounded by
`settings.trade_max_requests` (default 250) unless you pass `max_requests`.
`include_canceled=True` keeps cancelled/adjusted prints. `raw=True` returns
the provider payload columns untouched.

## Legacy notes

`stock()`, `stock_RI()`, `stock_RL()`, `stock_intraday()` are thin aliases
kept for 1.x compatibility. On resolver failures they may print a console
message and return `None` instead of raising — the `get_*` names raise typed
errors instead, so prefer them in anything new.
