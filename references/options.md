# Options: chains, market snapshot, math and PCR

Scope: اختیار معامله — listed option contracts, per-underlying chains,
the atomic market snapshot, chain analytics (IV, Greeks, parity), put/call
ratios, option history and local snapshots, plus the pure pricing math.

Option symbols encode the underlying and expiry, e.g. `ضهرح-14040910-2500`
(style varies by board) — always treat the option symbol as an opaque exact
string.

## list_options()

```python
opts = att.list_options(underlying=None, progress=True)
```

All active option contracts (1000+ rows live), parsed into structured
metadata: underlying, type (call/put), strike, expiry, symbol, InsCode.
`underlying=` filters to one underlying (e.g. `"اهرم"`, `"طلا"`).

## get_options_chain()

```python
chain = att.get_options_chain(underlying, fetch_oi=False, progress=True)
```

Structured **dict** with `calls` and `puts` DataFrames for one underlying,
aligned by strike/expiry. `fetch_oi=True` adds open interest — it costs
extra requests per contract; leave `False` for bulk scans.

```python
chain = att.get_options_chain("اهرم")
calls = chain["calls"]
puts = chain["puts"]
```

## get_option_market()

```python
market = att.get_option_market(exchange=0, underlying=None,
                               progress=True, max_requests=1)
```

The atomic one-request snapshot of the option boards. `exchange` accepts
`0`/`"all"`, `1`/`"tse"`, `2`/`"ifb"`. `underlying=` restricts to one
underlying. One row per contract with price, volume, OI and underlying
reference. This is the cheapest correct source for market-wide option
statistics — don't loop `get_options_chain` over all underlyings.

## analyze_option_chain()

```python
analysis = att.analyze_option_chain(options=None, underlying=None,
                                    spot=None, risk_free_rate=None,
                                    yield_curve=None, dividend_yield=0.0,
                                    valuation_date=None,
                                    exercise_style="european",
                                    parity_tolerance=None,
                                    liquidity_weights=None, progress=True,
                                    *, allow_unverified_freshness=True)
```

Full chain analytics: implied volatility (solved per contract),
Black–Scholes Greeks, put-call parity checks and liquidity-weighted
aggregates. Inputs are explicit and flexible:

- `options=` — an option frame (e.g. from `get_option_market`) instead of
  refetching by `underlying`.
- `spot=` — override the underlying price; otherwise taken from the
  snapshot.
- `risk_free_rate` or a `YieldCurve` object from `get_yield_curve()`
  (see `fixed-income.md`) — the rate source is never guessed.
- `exercise_style` — `"european"` is the only supported style; the
  parameter exists so unsupported styles fail loudly instead of silently
  pricing wrong. Corporate actions and dividend yields are never guessed
  from TSETMC data either.
- `parity_tolerance` — tolerance for flagging parity violations;
  `liquidity_weights` — non-negative weights (positive sum) for
  aggregations.
- `allow_unverified_freshness=True` — analyze snapshots whose freshness
  flags can't be verified (e.g. frames you saved earlier); the default
  keeps stale-analysis possible but the result reports it.

## option_put_call_ratios()

```python
pcr = att.option_put_call_ratios(options, group_by="market")
```

Put/call ratios from an option frame — volume, value and open-interest
based, grouped per `market` or by another grouping key. PCR is computed
from official totals; it is not a sentiment re-implementation.

## get_option_history(), save/load snapshots

```python
hist = att.get_option_history(symbol, start=None, end=None, limit=0,
                              include_today=False, snapshot_path=None,
                              progress=True, max_requests=3)

att.save_option_snapshot(path, options=None, exchange=0, progress=True, *,
                         lock_timeout=10.0, stale_lock_seconds=300.0)
loaded = att.load_option_snapshots(path)
```

- `get_option_history()` — server-side daily price history of one contract
  (`symbol` must be the exact option symbol). `include_today` follows the
  package-wide opt-in freshness contract. `snapshot_path=` additionally
  reads your locally recorded snapshots of the same contract.
- `save_option_snapshot()` — writes one atomic option-market snapshot to a
  JSON file; the file lock respects `lock_timeout` and `stale_lock_seconds`
  so crashed writers don't wedge later runs. Written only when you ask —
  nothing is recorded implicitly.
- `load_option_snapshots()` — reads saved snapshots back.
- `OPTION_SNAPSHOT_SCHEMA_VERSION` (1) — the on-disk format version; check
  it after upgrades if you keep snapshot files around.

## Pricing math (pure, offline)

```python
price = att.black_scholes_price(spot, strike, time_to_expiry, rate,
                                volatility, option_type="call",
                                dividend_yield=0.0,
                                exercise_style="european")
greeks = att.black_scholes_greeks(spot, strike, time_to_expiry, rate,
                                  volatility, option_type="call",
                                  dividend_yield=0.0,
                                  exercise_style="european")
bounds = att.option_price_bounds(spot, strike, time_to_expiry, rate,
                                 option_type="call", dividend_yield=0.0,
                                 exercise_style="european")
iv = att.implied_volatility(option_price, spot, strike, time_to_expiry,
                            rate, option_type="call", dividend_yield=0.0,
                            exercise_style="european",
                            lower_volatility=0.0, upper_volatility=5.0,
                            tolerance=1e-08, max_iterations=200)
```

- `black_scholes_price()` — closed-form European price; `option_type` is
  `'call'`/`'put'`. `exercise_style` must be `"european"` — the current
  math layer accepts nothing else and raises `ValueError` otherwise.
- `black_scholes_greeks()` — returns a dict: `Delta`, `Gamma`, `Vega`,
  `Vega1Pct`, `ThetaPerYear`, `ThetaPerDay`, `Rho`, `Rho100bp`, plus a
  `Status` (`"ok"` or `"undefined_at_expiry_or_zero_volatility"`).
- `option_price_bounds()` — arbitrage-free price bounds.
- `implied_volatility()` — bisection solver bracketed by
  `lower_volatility`/`upper_volatility` with `tolerance` and iteration
  cap. Returns a dict: `ImpliedVolatility`, `Status` (`"ok"` on
  convergence) and `Iterations`. A price outside the no-arbitrage
  bounds fails with an explicit status — the bounds function and the
  solver agree on the same contract.

These are pure functions — no network — and are covered by the offline
test suite in this repo. `time_to_expiry` is in years; use
`day_count_fraction()` (fixed-income reference) for date math.
