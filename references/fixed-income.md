# Fixed income: اخزا, اراد, گام, bond math and yield curves

Scope: Iranian government treasury bills (اخزا), the IFB reference yield
tables (اراد/گام and other debt), the pure bond-math layer, and yield
curve construction. The face value of اخزا is fixed:
`IRAN_TREASURY_FACE_VALUE = 1_000_000` rials — the package never rescales
it silently.

## The اخزا symbol convention

اخزا symbols encode the maturity date right after the word: `اخزاYYMMDD`
in Jalali. `parse_treasury_maturity()` decodes it and returns a dict:

```python
info = att.parse_treasury_maturity("اخزا020322")
# {'maturity_jalali': '1402/03/22',
#  'maturity_gregorian': datetime.date(2023, 6, 12),
#  'maturity_source': 'user_confirmed_symbol_jalali_yymmdd'}
```

Fields: `maturity_jalali` (slashed Jalali string), `maturity_gregorian`
(parsed `datetime.date`) and `maturity_source` (how the maturity was
derived — the package records its provenance).

Rules (from the package, verified): years `00`–`79` map to 1400–1479,
years `80`–`99` map to 1380–1399. Persian/Arabic digits and common
separators are normalized. A non-matching or invalid encoding returns
`None` — check for it rather than assuming success.

## Pure math layer (offline)

```python
frac = att.day_count_fraction(start, end, convention="ACT/365F")
y = att.treasury_yield(price, maturity_date, settlement_date=None,
                       face_value=1_000_000.0, day_count="ACT/365F")
p = att.bond_price(annual_yield, cashflows=None, settlement_date=None,
                   day_count="ACT/365F", compounding="nominal",
                   frequency=1, price_type="dirty", accrued_interest=None,
                   maturity_date=None, face_value=None, coupon_rate=None,
                   issue_date=None)
ytm = att.yield_to_maturity(price,  # same inputs as bond_price()
                            tolerance=1e-12, max_iterations=300)
risk = att.bond_analytics(price,  # same inputs as bond_price()
                            bump_size=0.0001)
```

- `day_count_fraction()` — conventions: `'ACT/365F'`, `'ACT/360'`,
  `'30E/360'`, `'ACT/ACT-ISDA'`. The interval is start-inclusive /
  end-exclusive (matches Python date subtraction); `end` must be strictly
  after `start`.
- `treasury_yield()` — the اخزا yield analysis from price and maturity.
  TSETMC publishes the price; this returns a rich dict with
  `SimpleAnnualYield`, `BankDiscountYield`, `EffectiveAnnualYield`,
  `ContinuousYield`, `DiscountFactor`, `DaysToMaturity`, `Tenor`,
  duration/convexity/DV01, `YieldConvention`, `DayCount`, `Status` —
  pin the convention you mean when comparing yields, because the
  numbers differ (a 15-day bill at 984050 on a 1M face gives ~0.394
  simple annual vs ~0.383 bank-discount).
- `bond_price()` — price from yield; inputs either an explicit
  `cashflows=` series or `maturity_date`/`coupon_rate`/`face_value`/
  `issue_date`. `price_type` is `'dirty'` or `'clean'`; `compounding`
  `'nominal'` with `frequency` (a positive divisor of 12) or effective.
- `yield_to_maturity()` — solves the same model in the other direction
  (bounded iterations, tight tolerance).
- `bond_analytics()` — duration, convexity and DV01 with `bump_size`.

All of these are pure and covered by this repo's offline tests.

## YieldCurve

```python
curve = att.build_yield_curve(nodes, settlement_date,
                              interpolation="log_discount",
                              extrapolate=False,
                              duplicate_policy="error",
                              day_count="ACT/365F",
                              rate_compounding="effective",
                              rate_frequency=1,
                              enforce_monotonic_discount=True)
```

Build a `YieldCurve` from explicit nodes (maturity/zero-rate pairs).
`duplicate_policy` is `'error'`, `'last'` or `'volume_weighted'`;
interpolation is `'log_discount'` by default;
`enforce_monotonic_discount=True` rejects upward discount factors
(arbitrage). The object exposes:

- `.nodes` — a **DataFrame**, one row per curve instrument: identity
  (InsCode/ISIN/Symbol), `MaturityJalali` + parsed `Maturity`, `Tenor`,
  `Price` + `PriceSource`, `SimpleAnnualYield`, `MacaulayDuration`,
  `ModifiedDuration`, `Convexity`, `DV01`, `DiscountFactor`,
  `ContinuousZeroRate`, staleness flags. Inspect it — it is the audit
  trail for the curve.
- `.settlement_date`, `.day_count`, `.interpolation`, `.extrapolate`
- `.discount_factor(maturity)` — D(t)
- `.zero_rate(maturity)` — continuously-compounded zero rate
- `.forward_rate(start, end)` — forward rate over an interval

Curves built by `get_yield_curve()` from live اخزا data use
`duplicate_policy="volume_weighted"` (several اخزا can mature on the same
day; volume-weighting merges them instead of erroring).

## get_debt_yields()

```python
debt = att.get_debt_yields(debt_type=None)
```

The official IFB "all securities" YTM reference table. `DebtType` is
classified by exact symbol prefix — `اخزا`, `اراد`, `گام` — and
`debt_type` filters `'treasury'`, `'erad'`, `'gam'` or `'other'` (string or
is the published reference, nothing more. Row count and section
availability vary with the publication window — the اخزا (treasury) rows
can disappear from the live page outside publishing hours while erad/
gam/other rows remain (observed empty in the evening), so treat an empty
filtered view as a window state before assuming the data model changed.

## get_treasury_yields() and its history

```python
snapshot = att.get_treasury_yields(symbol=None, settlement_date=None,
                                   face_value=1_000_000.0,
                                   include_stale=False, min_volume=0,
                                   price_source="auto",
                                   day_count="ACT/365F", strict=False,
                                   face_value_source=None, source="tsetmc",
                                   maturity_date=None, maturity_map=None,
                                   allow_no_trade=False)

history = att.get_treasury_yield_history(symbol=None, start=None,
                                         end=None, limit=0)
# get_treasury_yields_history() is the plural alias of the same call
```

Per-instrument اخزا yield snapshot computed from traded prices, with the
maturity parsed from the symbol (or `maturity_date`/`maturity_map`
overrides). For the live snapshot `price_source` is `'auto'`, `'mid'`,
'last' or `'close'` — `'auto'` picks the best available price and the
result frame records which source each row used. The history functions
accept `'auto'`, `'final'` or `'close'` (daily snapshots have no
bid/ask mid).

**Freshness gotcha (live-verified):** with the default
`include_stale=False` this returns an **empty frame whenever no اخزا has
traded yet in the current session** (mornings before the first treasury
trades, non-trading days). That is correct behavior, not a bug — pass
`include_stale=True` to get the last traded snapshot (14 rows in the
verification run). Same for `min_volume`: it can filter out everything.

## get_yield_curve() and get_yield_curve_history()

```python
curve = att.get_yield_curve(symbol=None, settlement_date=None,
                            face_value=1_000_000.0, include_stale=False,
                            min_volume=0, min_nodes=3,
                            price_source="auto", day_count="ACT/365F",
                            interpolation="log_discount", extrapolate=False,
                            duplicate_policy="volume_weighted",
                            enforce_monotonic_discount=True,
                            source="tsetmc")

curves = att.get_yield_curve_history(symbol=None, start=None, end=None,
                                     limit=0, face_value=1_000_000.0,
                                     include_today=False, progress=True,
                                     max_requests=250, maturity_map=None)
```

Live and historical yield curves built from the اخزا board. `min_nodes=3`
is the floor — with fewer traded instruments there is no curve to build
and the function raises (live-verified: with only stale data and
`include_stale=False` it raises `ValueError: yield curve has no usable
nodes`; `include_stale=True` builds the curve). The result is a
`YieldCurve`; history returns one per session (use the plural history
functions' frames for time series of specific tenors).

## get_ifb_yield_table()

```python
table = att.get_ifb_yield_table(category="treasury")
```

The official Iran Fara Bourse reference YTM page.
`category` is `'treasury'`, `'all'` or `'latest_history'` — and that is
all: the function intentionally does not emulate ASP.NET postbacks or
claim to expose the filtered history behind the page.

## What this family deliberately does not do

No coupon inference for اراد/گام rows (the IFB table is quoted as-is), no
face-value guessing (`face_value_source` is explicit), no curve
extrapolation unless `extrapolate=True`, and no silent merging of
same-day maturities unless `duplicate_policy` says so. If a caller needs
those, they must state them.
