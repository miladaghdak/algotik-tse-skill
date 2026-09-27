# Energy exchange and commodity markets

Scope: بورس انرژی ایران (IRENEX) — auctions, power contracts, salaf and
futures — and بورس کالا (IME) — certificates, the physical market board
and aggregate activity — plus generic futures-curve analytics.

Data sources: energy data comes from TSETMC-hosted endpoints; commodity
data comes from IME (`cdn.ime.co.ir`). Both are inside the package's
source boundary. `Value` on IME rows is published **in thousand rials**
and is never silently rescaled — the `ValueUnit` column records it.

## Energy auctions

```python
auctions = att.get_energy_auctions(status="upcoming", board="physical",
                                   top=100)
detail = att.get_energy_auction(auction_id, include_trades=True,
                                include_instrument_history=False)
overview = att.get_energy_market_overview(market="all")
```

- `get_energy_auctions()` — official auction notices.
  `status` ∈ `'upcoming'`, `'active'`, `'surplus'`, `'ended'`, `'all'`;
  `board` ∈ `'physical'`, `'power'`, `'special'`, `'green'`, `'free'`,
  `'all'`; `top` caps rows. Results keep delivery, payment, price-band,
  lot-size and discovery fields — everything needed to evaluate an
  auction.
- `get_energy_auction()` — one auction by `auction_id` (from the list
  above), optionally with the auction's own trades
  (`include_trades=True`) and the instrument's history
  (`include_instrument_history=True`).
- `get_energy_market_overview()` — daily official flow statistics for the
  energy exchange and the power market; `market` ∈ `'standard'`,
  `'green'`, `'free'`, `'all'`.

## Power and energy securities

```python
power = att.list_power_instruments(market="all", top=100)
securities = att.list_energy_securities(kind="all", active=True, top=100,
                                        enrich_futures=True)
contract = att.get_energy_future_contract(ins_code)
```

- `list_power_instruments()` — standard, green and free electricity
  contracts (برق استاندارد/سبز/آزاد); `market` ∈ `'standard'`, `'green'`,
  `'free'`, `'all'`.
- `list_energy_securities()` — energy salaf, certificates and futures by
  exact provider category; `kind` ∈ `'certificate'`, `'standard_salaf'`,
  `'fund'`, `'future'`, `'all'`. `active` keeps only tradable rows;
  `enrich_futures=True` decorates futures with contract details.
- `get_energy_future_contract()` — full contract specification for one
  futures `ins_code`: expiry, margin (وجه تضمین), fees and delivery
  rules.

## IME commodity board

```python
board = att.get_commodity_market(kind="all")
phys = att.get_commodity_physical_history(start, end=None)
summary = att.get_commodity_physical_summary(start, end=None, hall="all")
activity = att.get_commodity_market_activity(start, end=None, market="all")
```

- `get_commodity_market()` — IME's live board of certificates, salaf,
  commodity funds and futures; `kind` ∈ `'certificate'`,
  `'standard_salaf'`, `'fund'`, `'future'`, `'all'`.
- `get_commodity_physical_history()` — daily physical-market volume and
  value series over an **explicit** date range (`start` is required).
- `get_commodity_physical_summary()` — physical-hall aggregates
  (volume/value by hall) plus the trade-to-offer ratio; `hall` scopes to
  one hall or `'all'`.
- `get_commodity_market_activity()` — aggregate activity across physical,
  futures, options, financial and certificate markets over an explicit
  range.

## Futures curve analytics

```python
curve = att.get_futures_curve(contracts, underlying=None,
                              valuation_date=None, price="settlement",
                              spot_price=None)

spreads = att.get_calendar_spreads(curve)

carry = att.analyze_cash_and_carry(curve, annual_rate,
                                   storage_rate=0.0,
                                   convenience_yield=0.0)
```

Generic term-structure tools that accept explicit contract rows — they
work on the output of `get_energy_future_contract()` /
`list_energy_securities(kind="future")`, on IME futures rows, or on your
own DataFrame:

- `get_futures_curve()` — builds the term structure from contract rows;
  `price` ∈ `'settlement'`, `'close'`, `'last'`; `spot_price=` anchors the
  front end explicitly.
- `get_calendar_spreads()` — spreads between adjacent maturities with
  contango/backwardation detection.
- `analyze_cash_and_carry()` — futures price vs fair value under explicit
  carry assumptions (`annual_rate`, `storage_rate`,
  `convenience_yield`). The assumptions are yours — the package never
  guesses a carry model.

## Gotchas

- IME's published `Value` unit (thousand rials) is preserved as-is; read
  `ValueUnit` before comparing across sources.
- Physical-market history needs an explicit `start` — there is no
  "latest N days" convenience overload.
- Auction `status`/`board` filters are exact provider categories; passing
  e.g. `board="electricity"` raises `InvalidParameterError` with the
  valid list.
- `analyze_cash_and_carry` output is only as good as the rate assumptions
  you pass; label them in anything user-facing.
