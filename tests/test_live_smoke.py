"""Live smoke tests — one representative call per API family.

Marked ``online`` (deselected by default: run ``pytest -m online``).
These exercise the exact usage patterns the skill documents, against the
real TSETMC / TGJU / IME endpoints.

Two classes of upstream schedule behavior are treated as **skips**, not
failures (both are documented in the skill):

1. Empty bulk payloads outside publication windows (pre-market mornings,
   evenings, post-close EOD processing): industry membership, the bulk
   client-type feed, freshness-gated screens.
2. The GetInstrumentInfo ``lastDate`` status window: TSETMC serves
   ``lastDate: 0`` market-wide outside the finalized-snapshot state, so
   ``symbol + explicit asset_type`` resolution fails in those hours even
   though the names are actively trading. The tests use the robust
   patterns (auto resolution, pinned ins_code, snapshot-typed resolution)
   and additionally pin the fragile pattern's window behavior.
"""

import pytest

import algotik_tse as att

pytestmark = pytest.mark.online

# فولاد مبارکه اصفهان — canonical equity used across tests. Pinned InsCode
# so tests never depend on the live resolver.
FOOLAD_SELECTOR = "فولاد"
FOOLAD_INS_CODE = "46348559193224090"


def _skip_if_upstream_empty(frame, api):
    """Empty frames from freshness-gated bulk endpoints are skips."""
    __tracebackhide__ = True
    if frame is None or getattr(frame, "empty", False):
        pytest.skip(f"{api}: provider served an empty payload (publication window)")


@pytest.fixture(scope="module")
def foolad_ref():
    # Robust pattern: auto resolution works in every observed provider state.
    return att.resolve_instrument(FOOLAD_SELECTOR)


@pytest.fixture(scope="module")
def foolad_ins_code(foolad_ref):
    return foolad_ref.ins_code


class TestIdentity:
    def test_resolve_and_validate(self):
        ref = att.resolve_instrument(FOOLAD_SELECTOR)
        assert ref.ins_code == FOOLAD_INS_CODE
        assert ref.symbol == "فولاد"
        assert att.validate_ins_code(ref.ins_code) == ref.ins_code

    def test_snapshot_typed_resolution_window_robust(self):
        # Typed resolution via snapshot works in every observed state,
        # including the GetInstrumentInfo lastDate=0 window.
        snap = att.get_market_snapshot()
        ref = att.resolve_instrument(FOOLAD_SELECTOR, asset_type="equity",
                                      snapshot=snap)
        assert ref.asset_type == "equity"
        assert ref.is_active is True

    def test_explicit_asset_type_window_behavior_is_typed(self):
        # Outside the finalized-snapshot state, symbol + explicit asset_type
        # fails with the documented StockNotFoundError; inside it it works.
        # Both are valid 1.8.0 behavior — assert the call is *typed* either way.
        try:
            ref = att.resolve_instrument(FOOLAD_SELECTOR, asset_type="equity")
            assert ref.asset_type == "equity"
        except att.StockNotFoundError:
            pass  # documented evening/post-close window
        except att.AmbiguousSymbolError:
            pass  # same-symbol rival appeared in today's snapshot

    def test_detail_info_stats(self, foolad_ref):
        for frame in (att.get_detail(ins_code=foolad_ref.ins_code),
                      att.get_info(ins_code=foolad_ref.ins_code),
                      att.get_stats(ins_code=foolad_ref.ins_code)):
            assert frame is not None and not frame.empty


class TestPriceAndFlow:
    def test_history_and_client_type(self, foolad_ins_code):
        hist = att.get_history(ins_code=foolad_ins_code, limit=10,
                               progress=False)
        assert len(hist) == 10
        flow = att.get_client_type(ins_code=foolad_ins_code, limit=10,
                                   progress=False)
        assert len(flow) == 10

    def test_intraday_default_session(self, foolad_ref):
        candles = att.get_intraday(symbol=foolad_ref.symbol, interval="5min",
                                   progress=False)
        _skip_if_upstream_empty(candles, "get_intraday")

    def test_trades_recent(self, foolad_ref):
        # get_trades() resolves via the typed resolver, so pass the symbol
        # (ins_code-only resolution is fragile in the status window).
        trades = att.get_trades(foolad_ref.symbol, progress=False)
        _skip_if_upstream_empty(trades, "get_trades")


class TestUniverse:
    def test_symbols_and_master(self):
        bourse = att.get_symbols(bourse=True, farabourse=False, payeh=False,
                                 progress=False)
        assert not bourse.empty
        master = att.get_instrument_master(progress=False)
        assert len(master) > 1000

    def test_shareholders_and_capital(self, foolad_ref):
        holders = att.get_shareholders(ins_code=foolad_ref.ins_code)
        assert not holders.empty
        cap = att.get_capital_increase(ins_code=foolad_ref.ins_code)
        assert cap is not None  # may legitimately be empty for young names


class TestLiveMarket:
    def test_snapshot_dict_shape(self):
        snap = att.get_market_snapshot()
        for key in ("stocks", "order_book", "trade_date", "fetched_at",
                    "is_realtime_fresh", "is_partial", "market_state",
                    "snapshot_age_seconds"):
            assert key in snap, f"snapshot dict missing {key}"

    def test_live_market_or_publication_window(self, foolad_ref):
        try:
            live = att.get_live_market()
        except att.DataParsingError:
            pytest.skip("get_live_market: client-type feed empty (publication window)")
        assert not live.empty
        row = att.get_live_symbol(ins_code=foolad_ref.ins_code)
        assert len(row) == 1

    def test_order_book_and_queue(self, foolad_ref):
        # get_order_book/get_queue take a symbol selector (Persian ticker or
        # InsCode string), not the ins_code keyword.
        book = att.get_order_book(foolad_ref.ins_code)
        assert not book.empty
        queue = att.get_queue(foolad_ref.ins_code, strict=False)
        assert queue is not None  # empty is legitimate: no queue right now


class TestMarketAnalytics:
    def test_overview_breadth_sector(self):
        overview = att.get_market_overview()
        assert not overview.empty
        breadth = att.get_market_breadth(traded_only=True)
        assert not breadth.empty
        sector = att.get_sector_flow(traded_only=True)
        assert not sector.empty

    def test_calendar_value_impact(self):
        cal = att.get_trading_calendar(limit=5)
        assert not cal.empty
        value = att.get_market_value_history(limit=5)
        assert not value.empty
        impact = att.get_index_impact(top=5)
        assert not impact.empty

    def test_fundamentals_stale_fallback(self):
        fresh = att.get_market_fundamentals(progress=False)
        if fresh.empty:
            stale = att.get_market_fundamentals(allow_stale=True, progress=False)
            assert not stale.empty, "allow_stale fallback should return rows"

    def test_market_map(self):
        data = att.get_market_map(group_by="sector", size="value",
                                  color="return", top=20)
        assert data is not None

    def test_top_requires_credentials(self):
        with pytest.raises(att.InvalidParameterError):
            att.get_theoretical_opening_price()


class TestIndustries:
    def test_index_list_and_snapshot(self):
        indices = att.list_industry_indices(progress=False)
        assert len(indices) >= 40
        snap = att.get_industry_snapshot(["فلزات اساسی"], include_empty=True,
                                         progress=False)
        # Pre-market the membership payload can be empty for every industry;
        # the contract is: row present (include_empty) with attrs explaining.
        assert "فلزات اساسی" in snap["IndustryName"].tolist()
        assert "empty_industries" in snap.attrs

    def test_history_and_ranking(self):
        hist = att.get_industry_history("فلزات اساسی", limit=5, progress=False)
        assert len(hist) == 5
        ranked = att.rank_industries(progress=False)
        if ranked.empty:
            pytest.skip("rank_industries: membership payload empty (publication window)")


class TestOwnership:
    def test_recent_change_board(self):
        changes = att.get_major_shareholder_changes(days=5, progress=False)
        _skip_if_upstream_empty(changes, "get_major_shareholder_changes")

    def test_network_and_concentration(self, foolad_ref):
        network = att.get_shareholder_network(progress=False)
        _skip_if_upstream_empty(network, "get_shareholder_network")
        conc = att.get_ownership_concentration(ins_code=foolad_ref.ins_code,
                                               progress=False)
        assert not conc.empty

    def test_symbol_events_default_kinds(self, foolad_ref):
        events = att.get_symbol_events(ins_code=foolad_ref.ins_code,
                                       limit=10, progress=False)
        assert events is not None


class TestOptions:
    def test_option_market_and_chain(self):
        market = att.get_option_market(progress=False)
        assert len(market) > 100
        chain = att.get_options_chain("اهرم", progress=False)
        assert "calls" in chain and "puts" in chain
        pcr = att.option_put_call_ratios(market)
        assert not pcr.empty


class TestFixedIncome:
    def test_debt_yields_table(self):
        debt = att.get_debt_yields()
        assert len(debt) > 100
        treasuries = att.get_debt_yields(debt_type="treasury")
        # The IFB reference page drops its اخزا section outside publication
        # windows (observed empty in the evening); empty is a provider
        # state, not a contract violation.
        if treasuries.empty:
            pytest.skip("treasury section empty (publication window)")
        assert "ReferenceYTM" in treasuries.columns

    def test_treasury_snapshot_stale_fallback(self):
        fresh = att.get_treasury_yields()
        if fresh.empty:
            stale = att.get_treasury_yields(include_stale=True)
            assert not stale.empty, "include_stale fallback should return rows"

    def test_yield_curve_or_publication_window(self):
        try:
            curve = att.get_yield_curve(include_stale=True)
        except ValueError as exc:
            if "no usable nodes" in str(exc):
                pytest.skip("yield curve: not enough traded nodes right now")
            raise
        assert len(curve.nodes) >= 3


class TestFunds:
    def test_three_fund_universes(self):
        assert not att.list_etfs(progress=False).empty
        assert not att.list_funds(progress=False).empty
        assert not att.list_listed_funds(progress=False).empty
        equity = att.list_funds(fund_type="equity", progress=False)
        assert not equity.empty

    def test_debt_instruments(self):
        debt = att.list_debt_instruments(active_only=True, progress=False)
        assert not debt.empty


class TestEnergyCommodity:
    def test_energy_auctions_and_board(self):
        auctions = att.get_energy_auctions(status="all", board="all")
        assert auctions is not None
        board = att.get_commodity_market(kind="all")
        assert not board.empty

    def test_power_and_securities(self):
        assert att.list_power_instruments(market="all") is not None
        assert att.list_energy_securities(kind="all") is not None


class TestTGJU:
    def test_catalog_and_history(self):
        assets = att.list_tgju_assets()
        assert len(assets) >= 80
        usd = att.get_tgju_history("dollar", limit=5, progress=False)
        assert len(usd) == 5
        # Columns are always OHLC; dates live in the index (J-Date by
        # default, Date under gregorian/both).
        assert list(usd.columns) == ["Open", "High", "Low", "Close"]
        assert usd.index.name == "J-Date"
        assert list(usd.index) == sorted(usd.index)  # ascending dates
