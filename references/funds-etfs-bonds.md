# ETFs, funds, bonds and debt instruments

Scope: the three fund universes (TSETMC registry funds, listed ETF-like
funds, commodity funds), ETFs with NAV, bonds, and the newer debt
instrument view. The words "fund" and "ETF" are **not interchangeable**
here — each API covers a different, explicitly bounded universe, and the
package never fuzzy-joins them.

## The three universes (and why there are three)

1. **Registry funds** — `list_funds()`: the TSETMC Fund API, a rich
   registry of ~560 investment funds (NAV, returns, portfolio
   composition, manager, type). **Rows are not guaranteed to be
   exchange-listed and carry no canonical ticker/InsCode.**
2. **Listed funds** — `list_listed_funds()`: the exact current
   exchange-listed fund instruments (tradable tickers), including
   commodity funds, filterable by category/strategy.
3. **ETFs** — `list_etfs()`: the legacy exchange-listed ETF path (public
   بورس funds of type 305) with NAV and discount/premium.

`list_funds(listed_only=True)` restricts the registry view to currently
listed instruments — but the two sources are still never joined by name:
listed-only registry rows and `list_listed_funds()` rows come from
different official sources. For tradable fund tickers use
`list_listed_funds()`; for fund analytics (NAV, portfolio, manager) use
`list_funds()`.

```python
import algotik_tse as att

registry = att.list_funds(progress=False)
listed = att.list_listed_funds(progress=False)
etfs = att.list_etfs(progress=False)
```

## list_funds()

```python
funds = att.list_funds(fund_type=None, progress=True, *, listed_only=False,
                       strategy=None, commodity_underlying=None,
                       classification_status=None)
```

Registry view with NAV, returns over standard windows, portfolio
composition, manager and registration metadata. Filters:

- `fund_type` — string or list. Valid values (per the fund taxonomy,
  `FUND_TAXONOMY_VERSION` constant, currently `2026-09-11`):
  `equity` (سهام), `fixed_income` (درآمد ثابت), `mixed` (مختلط),
  `market_maker` (بازارگردانی), `venture_capital` (جسورانه; `'venture'`
  accepted), `project` (پروژه), `real_estate` (زمین و ساختمان),
  `commodity` (کالایی — طلا، نقره، …), `private`, `fund_of_funds`
  (صندوق در صندوق), `sector`, `leveraged`, `index`,
  `capital_guaranteed`, `supplementary_retirement`.
  `None` returns all types.
- `strategy` — strategy classification filter.
- `commodity_underlying` — for commodity funds (e.g. gold/silver).
- `classification_status` — restrict by evidence status of the taxonomy
  classification.

## list_listed_funds()

```python
listed = att.list_listed_funds(progress=True, *, fund_category=None,
                               strategy=None, commodity_underlying=None,
                               classification_status=None,
                               include_unknown=True)
```

The exact listed fund instruments with their exchange data. Same filter
vocabulary as `list_funds` plus `include_unknown=True` (keep rows the
taxonomy can't classify — safer default for universe completeness).

## list_etfs()

```python
etfs = att.list_etfs(progress=True)
```

Exchange-listed ETF-style funds with **NAV and NAV discount/premium**
columns — `NAV_Discount` is percent, negative = discount, positive =
premium, so `nsmallest` finds the deepest discounts. The quick screen
for premium/discount anomalies.

## list_bonds() and list_debt_instruments()

```python
bonds = att.list_bonds(progress=True)

debt = att.list_debt_instruments(debt_type=None, active_only=False,
                                 progress=True)
```

- `list_bonds()` — murabaha, ijara, sukuk and treasury bills with maturity
  data. The legacy board view.
- `list_debt_instruments()` — the newer view with an exact `DebtType`
  classification and filtering by `debt_type` (`'treasury'`, `'erad'`,
  `'gam'`, `'other'` — same vocabulary as `get_debt_yields()`), plus
  `active_only=True` to drop matured/expired paper. Yield math lives in
  `fixed-income.md`.

Both returned ~360 rows in the live verification run.

## Choosing the right list

| Question | API |
|---|---|
| "Give me tradable fund tickers" | `list_listed_funds()` |
| "Fund NAV / portfolio / manager analytics" | `list_funds()` (+ `listed_only=True` to stay tradable) |
| "ETF premium/discount screen" | `list_etfs()` |
| "Bond board with maturities" | `list_bonds()` or `list_debt_instruments()` |
| "Only active treasury/erad/gam paper" | `list_debt_instruments(debt_type=..., active_only=True)` |

Gotchas:

- `list_funds()` rows are registry entries — never treat their names as
  tickers or join them to price data by name.
- Fund taxonomy values are validated; a bad `fund_type` raises
  `InvalidParameterError` rather than returning everything.
- The fund type labels in the registry are Persian; the taxonomy keys
  above are the exact strings the filter accepts.
