# Audit report: algotik-tse skill vs algotik-tse 1.8.0

Date of work: 2026-09-27 (Tehran), against `algotik-tse==1.8.0` (PyPI,
matching github.com/mohsenalipour/algotik_tse HEAD, tag content
byte-identical to the installed wheel modulo line endings).

Method: read the installed package source; enumerate the exported API
(167 names); cross-check every claim against the upstream README and the
package docstrings; run the upstream test suite against the installed
package; write a machine-checked inventory suite for this skill; exercise
one representative call per API family live against TSETMC, TGJU and IME
in more than one time-of-day window.

## Verification evidence

| Check | Result |
|---|---|
| Installed 1.8.0 == upstream HEAD (diff, CR-stripped) | identical |
| Upstream offline suite (`pytest`, not online) | 501 passed |
| Upstream live suite (`pytest -m online`) | 118 passed (pre-open window) |
| This skill: offline inventory/snippets/math suite | 207 passed |
| This skill: live smoke suite (`-m online`, evening window) | 30 passed, 1 window-skip |
| Examples | 12 scripts, all run against live providers |

## Findings against the previous skill text

The skill this repo replaces was written against the 1.0.x era. Gaps:

1. **Version drift.** Claimed 1.0.2; the package is 1.8.0 with 167
   exported names (150 functions, 11 classes, settings, constants). The
   previous text documented roughly 30 of them.
2. **Missing API families.** No coverage of: fixed income (اخزا/اراد/گام,
   bond math, yield curves, IFB tables), energy exchange and IME
   commodity markets (13 functions), industry analytics (17 functions),
   ownership analytics (shareholder history/network/concentration/
   accumulation), market analytics (calendar, activity, index impact,
   TOP/pre-open, comparisons, liquidity, regime, market map),
   fundamentals, local SQLite history, TGJU catalog, instrument
   master/resolver utilities.
3. **Wrong dependency list.** `urllib3` is a real dependency in 1.8.0;
   `plotly>=5.0` is an optional extra (`[visualization]`) needed only by
   `plot_market_map()`.
4. **Incomplete legacy alias table.** `stock_introduction()` and
   `market_data()` (deprecated, redirects to `market_watch()`) were
   missing.
5. **`get_introduction()` unexplained.** It always raises
   `UnsupportedDataSourceError` — company introductions are a Codal
   product and Codal is outside the package's enforced source boundary.
   The previous skill did not say this, which guarantees a confused
   debugging session.
6. **Return-type overclaim.** "Outputs are generally pandas.DataFrame"
   is wrong for a large part of the surface: snapshots are dicts,
   `resolve_instrument` returns `InstrumentRef`, yield curves return
   `YieldCurve`, the watcher yields `MarketEvent`, chain analysis and the
   Black-Scholes/IV/treasury math return dicts, `parse_treasury_maturity`
   returns a dict with provenance.
7. **No behavioral contracts.** `df.attrs` metadata, `include_today`
   freshness semantics, `save_path`-is-a-folder, `Close` vs `Final`,
   error hierarchy, rate limiting and the source boundary were absent.

## Live behaviors the package docs don't state

These were all reproduced directly against the providers and are encoded
in the references and tests:

1. **`GetInstrumentInfo` status window.** Outside the finalized-snapshot
   state (observed from just after the 15:00 Tehran close through the
   evening; pre-open mornings behaved fine), TSETMC serves
   `lastDate: 0` for the whole market on the point-info endpoint. The
   resolver treats that endpoint as authoritative for activity whenever
   it must verify an explicit `asset_type` or confirm an `ins_code`, so:
   - `resolve_instrument("فولاد", asset_type="equity")` →
     `StockNotFoundError: No active instrument matched`;
   - legacy data calls (`get_history`, `get_client_type`, …) with
     `asset_type="equity"` print `Stock Not Found, Please try again ...`
     and return `None`;
   - `resolve_instrument(ins_code=...)` without a snapshot fails the same
     way, and `get_trades(ins_code=...)` inherits it (it resolves
     through the typed resolver).
   Robust in every observed state: `resolve_instrument(symbol)` with
   `auto`, data calls with `ins_code` + default `asset_type`,
   `require_active=False`, and typed resolution with an explicit
   `snapshot=att.get_market_snapshot()` — which is why the skill's
   recommended production pattern is *pin the InsCode early, keep
   `asset_type` at `auto`, pass a snapshot when you need typed
   resolution*.
2. **Empty bulk payloads outside publication windows.**
   `ClosingPrice/GetIndexCompany` (industry membership) was empty
   pre-market: `get_industry_members` returned 0 rows, snapshots dropped
   industries (`include_empty=True` surfaces them; attrs records
   `empty_industries`). The bulk client-type feed
   (`old.tsetmc.com/tsev2/data/ClientTypeAll.aspx`) was empty
   pre-open-ish and mid-morning: `get_live_market` raised
   `DataParsingError: Empty response from client type endpoint`; the same
   feed was repopulated by ~20:00 Tehran. The IFB reference yield page
   served an empty اخزا (treasury) section in the evening while erad/gam
   rows remained. Freshness-gated screens (`get_market_fundamentals`
   with `allow_stale=False`, `get_treasury_yields` with
   `include_stale=False`) return empty frames by design outside
   publication windows — `allow_stale=True` / `include_stale=True`
   recovers the last published snapshot (verified: 0 → 925 rows
   fundamentals; 0 → 14 rows treasuries; yield curve went from
   "no usable nodes" to a 4-node curve).
3. **`watch_market()` fast-view incompatibility.** The watcher boots
   against `MarketWatchInit.aspx`, whose fast-view section TSETMC now
   also serves in a 17-field variant; 1.8.0's parser accepts only 3 or 16
   fields and raises `DataParsingError: fast-view section has 17
   fields`. Reproduced repeatedly in the evening; the same URL also
   served the compatible 3-field variant minutes apart (backend
   variance). The bulk snapshot APIs use `MarketWatchPlus` and are
   unaffected. Treat watcher startup as retryable until upstream ships a
   fix.
4. **`save_market_snapshot()` scale pathology.** On a whole-market live
   frame (~3.7k rows × 163 columns) the save is dominated by pandas
   attrs deepcopy (self-referential snapshot metadata) and did not
   complete in 10 minutes; a 30-row watchlist frame saves in ~19s.
   Passing the raw `market_watch()` dict as `snapshot=` is not a
   supported pattern and exhibits the same blow-up. Supported: default
   fetch (trading hours), or a live-view DataFrame you already hold —
   and in practice, a filtered one.
5. **Symbol ambiguity is real and time-varying.** `شتران` matched two
   same-rank active instruments during the pre-open window and resolved
   uniquely again later the same day — the data decides, which is
   exactly why the resolver raises instead of guessing.
6. **`get_shareholder_history` requires `start`/`end`** (no "latest N"
   overload) and pre-computes the required request budget from the date
   range (a one-month daily range needed 12 requests; `max_requests=5`
   raised `InvalidParameterError`).
7. **TGJU frame shape.** Columns are always `Open/High/Low/Close`; dates
   live in the index — `J-Date` (Jalali strings) by default, `Date`
   (`datetime64`) under `gregorian` and also under `both`. Ascending
   order by default.
8. **Small contract corrections found while writing the skill's own
   tests** (the test suite earns its keep): `implied_volatility` returns
   `{ImpliedVolatility, Status, Iterations}` (not a scalar);
   `treasury_yield` returns a rich dict with per-convention yields;
   `parse_treasury_maturity` returns a dict with
   `maturity_jalali/maturity_gregorian/maturity_source`;
   `black_scholes_greeks` returns Vega1Pct/ThetaPerYear/ThetaPerDay/
   Rho100bp plus Status; `validate_ins_code` trims outer whitespace but
   rejects inner whitespace; ETF NAV column is `NAV_Discount` (percent,
   negative = discount); `list_funds` type keys come from the dated fund
   taxonomy (`FUND_TAXONOMY_VERSION`); `YieldCurve.nodes` is a
   DataFrame with full per-instrument audit columns.

## Known-open items (as of this audit)

- No upstream release beyond 1.8.0 exists (PyPI checked), so items 1–4
  above are current-state facts, not fixed bugs. The skill documents the
  mechanisms and the robust patterns rather than waiting for upstream.
- `algotik_tse.exceptions.RateLimitError` exists but is not exported at
  package level — matches the package README.
