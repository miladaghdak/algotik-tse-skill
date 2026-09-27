"""Options: market snapshot, chain, analytics, PCR.

Run:  python examples/06_options.py
"""

import algotik_tse as att


def main():
    market = att.get_option_market(progress=False)
    print("active option contracts:", len(market))

    chain = att.get_options_chain("اهرم", progress=False)
    print("calls:", len(chain["calls"]), "| puts:", len(chain["puts"]))

    pcr = att.option_put_call_ratios(market)
    print("put/call ratios:\n", pcr.to_string())

    # Pure math sanity check: price -> IV -> price round-trip.
    price = att.black_scholes_price(spot=1000.0, strike=1000.0,
                                    time_to_expiry=0.25, rate=0.20,
                                    volatility=0.35)
    iv = att.implied_volatility(option_price=price, spot=1000.0,
                                strike=1000.0, time_to_expiry=0.25,
                                rate=0.20)
    greeks = att.black_scholes_greeks(spot=1000.0, strike=1000.0,
                                      time_to_expiry=0.25, rate=0.20,
                                      volatility=0.35)
    print("price:", round(price, 2), "| implied vol:",
          round(iv["ImpliedVolatility"], 4), "| status:", iv["Status"])
    print("delta:", round(greeks["Delta"], 4),
          "| gamma:", round(greeks["Gamma"], 6))

if __name__ == "__main__":
    main()
