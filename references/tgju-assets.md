# TGJU: currency, gold, silver, coin and metals

Scope: price history for assets that trade in the free/parallel market and
global metals — dollar, euro, gold, silver, coins (with the separate
"bubble" series), and global metals — sourced from TGJU's verified
catalog. These are **market price series**, distinct from TSETMC
instruments; they don't have InsCodes.

## The verified catalog

```python
assets = att.list_tgju_assets(category=None, include_aliases=False)
```

Returns the verified TGJU asset catalog — ~87 series live. `category`
filters one or more of: `currency`, `official_rate`, `gold`, `silver`,
`coin`, `coin_bubble`, `global_metal`. `include_aliases=True` adds the
`Aliases` column (the several slug names TGJU historically serves some
series under). **Only catalog names are supported** — the history
provider rejects arbitrary slugs rather than guessing, so screen this
table first when a user asks for an unusual asset.

```python
import algotik_tse as att

assets = att.list_tgju_assets()
dollars = att.list_tgju_assets(category="currency")
```

## get_tgju_history() and get_currency()

```python
hist = att.get_tgju_history(name="", start=None, end=None, limit=0,
                            output_type="standard",
                            date_format="jalali", progress=True,
                            save_to_file=False, dropna=True,
                            return_type=None, ascending=True,
                            save_path=None, **kwargs)

# get_currency() is the legacy alias with the same signature
hist = att.get_tgju_history(name="", start=None, end=None, limit=0, progress=False)
```

Daily OHLC history for one catalog asset or a list of them (multi-asset
calls return a dict of frames). Names are English slugs (`"dollar"`,
`"euro"`) or Persian (`"ربع سکه"`, `"سکه امامی"`, `"طلای ۱۸ عیار"`) —
use exactly what `list_tgju_assets()` shows.

Output: columns are always `Open`, `High`, `Low`, `Close`; the **index**
carries the dates and its name/values follow `date_format` — `J-Date` with
Jalali strings (`1405-06-30`) under the default `'jalali'`, `Date` with
`datetime64` values under `'gregorian'` and also under `'both'` (the
Gregorian index wins in both). Multi-name calls return a dict of frames
keyed by the name you passed.

```python
usd = att.get_tgju_history("dollar", limit=30, progress=False)
coins = att.get_currency(["ربع سکه", "سکه امامی"], limit=30, progress=False)
```

## Gotchas

- `coin_bubble` (حباب سکه) is a separate catalog category — the bubble
  series is the premium of coin over its melt value, not a price level;
  don't chart it on the same axis as coin prices without saying so.
- `official_rate` (نرخ رسمی/بانکی) and free-market `currency` rates are
  different series; mixing them silently produces nonsense comparisons.
- TGJU serves rows newest-first; the package returns them chronologically
  oldest→newest by default (`ascending=True`). Pass `ascending=False`
  only if you really want newest-first rows.
- TGJU series have no volume — any liquidity analysis on them is
  meaningless.
- The history provider is TGJU's API; rate limiting still applies through
- TGJU requests go through the same shared rate-limited client as
  everything else; use `progress=False` in scripts and notebooks.
