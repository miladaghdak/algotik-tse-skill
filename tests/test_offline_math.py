"""Deterministic, network-free checks of the pure parts of algotik_tse.

These pin the behavior the skill documents: اخزا maturity parsing, day
counts, Black–Scholes/IV round-trip, InsCode validation, text
normalization, YieldCurve math and the bond analytics layer.
"""

import datetime

import pytest

import algotik_tse as att


class TestTreasuryMaturity:
    def test_decodes_jalali_yymmdd(self):
        info = att.parse_treasury_maturity("اخزا020322")
        assert info["maturity_jalali"] == "1402/03/22"
        assert info["maturity_gregorian"] == datetime.date(2023, 6, 12)
        assert info["maturity_source"]

    def test_year_99_maps_to_1399(self):
        info = att.parse_treasury_maturity("اخزا991117")
        assert info["maturity_jalali"] == "1399/11/17"

    def test_persian_digits_are_normalized(self):
        info = att.parse_treasury_maturity("اخزا۰۲۰۳۲۲")
        assert info["maturity_jalali"] == "1402/03/22"

    def test_non_matching_or_invalid_returns_none(self):
        assert att.parse_treasury_maturity("فولاد") is None
        assert att.parse_treasury_maturity("اخزا990232") is None  # day 32
        assert att.parse_treasury_maturity("اخزا9901173") is None  # 7 digits

class TestDayCount:
    def test_act_365f(self):
        frac = att.day_count_fraction(
            datetime.date(2024, 1, 1), datetime.date(2025, 1, 1)
        )
        assert frac == pytest.approx(366 / 365)

    def test_act_360(self):
        frac = att.day_count_fraction(
            datetime.date(2024, 1, 1), datetime.date(2024, 7, 1), "ACT/360"
        )
        assert frac == pytest.approx(182 / 360)

    def test_end_must_be_after_start(self):
        with pytest.raises(Exception):
            att.day_count_fraction(
                datetime.date(2024, 1, 2), datetime.date(2024, 1, 1)
            )

    def test_unsupported_convention_raises(self):
        with pytest.raises(Exception):
            att.day_count_fraction(
                datetime.date(2024, 1, 1), datetime.date(2024, 1, 2), "30/360US"
            )


class TestBlackScholes:
    SPOT, STRIKE, T, RATE, VOL = 1000.0, 1000.0, 0.25, 0.20, 0.35

    def test_call_price_positive_and_put_call_parity(self):
        call = att.black_scholes_price(self.SPOT, self.STRIKE, self.T,
                                       self.RATE, self.VOL)
        put = att.black_scholes_price(self.SPOT, self.STRIKE, self.T,
                                      self.RATE, self.VOL, option_type="put")
        # C - P = S - K e^{-rT}
        assert call - put == pytest.approx(
            self.SPOT - self.STRIKE * pow(2.718281828459045, -self.RATE * self.T),
            rel=1e-4,
        )

    def test_greeks_dict_keys(self):
        greeks = att.black_scholes_greeks(self.SPOT, self.STRIKE, self.T,
                                          self.RATE, self.VOL)
        for key in ("Delta", "Gamma", "Vega", "Vega1Pct", "ThetaPerYear",
                    "ThetaPerDay", "Rho", "Rho100bp", "Status"):
            assert key in greeks
        assert greeks["Status"] == "ok"
        assert 0 < greeks["Delta"] < 1

    def test_implied_volatility_round_trip(self):
        call = att.black_scholes_price(self.SPOT, self.STRIKE, self.T,
                                       self.RATE, self.VOL)
        iv = att.implied_volatility(call, self.SPOT, self.STRIKE, self.T,
                                    self.RATE)
        assert iv["Status"] == "ok"
        assert iv["ImpliedVolatility"] == pytest.approx(self.VOL, rel=1e-5)
        assert iv["Iterations"] > 0

    def test_only_european_style_supported(self):
        with pytest.raises(ValueError):
            att.black_scholes_price(self.SPOT, self.STRIKE, self.T, self.RATE,
                                    self.VOL, exercise_style="american")

    def test_price_bounds_contain_model_price(self):
        bounds = att.option_price_bounds(self.SPOT, self.STRIKE, self.T,
                                         self.RATE)
        call = att.black_scholes_price(self.SPOT, self.STRIKE, self.T,
                                       self.RATE, self.VOL)
        assert bounds[0] <= call <= bounds[1]


class TestIdentityTools:
    def test_validate_ins_code_accepts_int_and_ascii_digits(self):
        assert att.validate_ins_code(46348859393796168) == "46348859393796168"
        assert att.validate_ins_code("46348859393796168") == "46348859393796168"

    @pytest.mark.parametrize("bad", [0, "0", 1.5, True, "4634٨۵۹٣", "-5", "4 6", ""])
    def test_validate_ins_code_rejects_ambiguity(self, bad):
        with pytest.raises(Exception):
            att.validate_ins_code(bad)

    def test_validate_ins_code_strips_outer_whitespace(self):
        assert att.validate_ins_code(" 46 ") == "46"

    def test_normalize_unifies_arabic_yeh_and_kaf(self):
        assert att.normalize_instrument_text("كيا") == "کیا"
        assert att.normalize_instrument_text("س ي نا") == "س ی نا"


class TestYieldCurve:
    def test_build_and_query_curve(self):
        import pandas as pd

        settlement = datetime.date(2026, 9, 27)
        nodes = pd.DataFrame(
            {
                "Maturity": [datetime.date(2026, 12, 27),
                             datetime.date(2027, 6, 27),
                             datetime.date(2028, 9, 27)],
                "ZeroRate": [0.30, 0.32, 0.34],
            }
        )
        curve = att.build_yield_curve(nodes, settlement)
        assert len(curve.nodes) == 3
        assert curve.discount_factor(1.0) < 1.0
        assert curve.zero_rate(1.0) > 0
        # zero rates are increasing in the input
        assert curve.zero_rate(0.25) < curve.zero_rate(1.5)
        # monotone discount factors
        dfs = [curve.discount_factor(t) for t in (0.25, 0.75, 1.5)]
        assert dfs[0] >= dfs[1] >= dfs[2]
        forward = curve.forward_rate(0.25, 0.5)
        assert forward > -1


class TestBondMath:
    def test_bond_price_and_ytm_round_trip(self):
        # One annual coupon of 30% on face 1M, one year, zero-coupon-ish
        # simple case: annual coupon bond priced at par-ish yield.
        price = att.bond_price(annual_yield=0.30,
                               maturity_date=datetime.date(2027, 9, 27),
                               settlement_date=datetime.date(2026, 9, 27),
                               face_value=1_000_000.0,
                               coupon_rate=0.30, frequency=1)
        ytm = att.yield_to_maturity(price,
                                    maturity_date=datetime.date(2027, 9, 27),
                                    settlement_date=datetime.date(2026, 9, 27),
                                    face_value=1_000_000.0,
                                    coupon_rate=0.30, frequency=1)
        assert ytm == pytest.approx(0.30, rel=1e-6)

    def test_bond_analytics_returns_risk_metrics(self):
        price = att.bond_price(annual_yield=0.30,
                               maturity_date=datetime.date(2027, 9, 27),
                               settlement_date=datetime.date(2026, 9, 27),
                               face_value=1_000_000.0,
                               coupon_rate=0.30, frequency=1)
        analytics = att.bond_analytics(price,
                                       maturity_date=datetime.date(2027, 9, 27),
                                       settlement_date=datetime.date(2026, 9, 27),
                                       face_value=1_000_000.0,
                                       coupon_rate=0.30, frequency=1)
        assert analytics["MacaulayDuration"] > 0
        assert analytics["ModifiedDuration"] > 0
        assert analytics["Convexity"] > 0
        assert analytics["DV01"] > 0

    def test_treasury_yield_discount_instrument(self):
        # اخزا trades below face; a 15-day bill at 984050 gives a rich dict.
        y = att.treasury_yield(price=984050.0,
                               maturity_date=datetime.date(2026, 10, 12),
                               settlement_date=datetime.date(2026, 9, 27))
        assert y["Status"] == "ok"
        assert y["FaceValue"] == 1_000_000.0
        assert y["DaysToMaturity"] == 15
        assert y["SimpleAnnualYield"] == pytest.approx(0.3944, rel=1e-3)
        assert y["BankDiscountYield"] == pytest.approx(0.3828, rel=1e-3)
        for key in ("DiscountFactor", "EffectiveAnnualYield",
                    "ContinuousYield", "MacaulayDuration",
                    "ModifiedDuration", "Convexity", "DV01",
                    "Tenor", "YieldConvention", "DayCount"):
            assert key in y


class TestConstantsAndErrors:
    def test_documented_constants(self):
        assert att.IRAN_TREASURY_FACE_VALUE == 1_000_000.0
        assert att.MARKET_HISTORY_SCHEMA_VERSION == 2
        assert att.MARKET_HISTORY_APPLICATION_ID == 1096045381
        assert att.OPTION_SNAPSHOT_SCHEMA_VERSION == 1
        assert att.FUND_TAXONOMY_VERSION == "2026-09-11"

    def test_error_hierarchy(self):
        for exc in (att.AmbiguousSymbolError, att.ConnectionError,
                    att.DataParsingError, att.InvalidParameterError,
                    att.StockNotFoundError, att.UnsupportedDataSourceError):
            assert issubclass(exc, att.AlgotikTSEError)

    def test_get_introduction_always_raises(self):
        with pytest.raises(att.UnsupportedDataSourceError):
            att.get_introduction("فولاد")

    def test_settings_defaults(self):
        from algotik_tse.settings import settings

        assert settings.ssl_verify is True
        assert settings.timeout == 10
        assert settings.rate_limit_delay == 0.3
        assert settings.order_book_max_requests == 250
        assert settings.trade_max_requests == 250
