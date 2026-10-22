from sigcup.pricing import RefLeg, fair_value
from sigcup.references import RefQuote
from sigcup.sig_api import Book, Level, round_to_tick
from sigcup.strategy import Holding, kelly_cost, plan_entry, plan_exit

KW = dict(min_edge=0.04, depth_fraction=0.5, max_cost=10_000, kelly_fraction=0.25, bankroll=100_000)
EXIT = dict(exit_band=0.01, stop_loss=0.08, max_hold_hours=72, exit_slippage=0.02)


def book(bids, asks):
    return Book("e1", [Level(p, q) for p, q in bids], [Level(p, q) for p, q in asks])


def test_round_to_tick_never_worsens_price():
    assert round_to_tick(0.6123, "buy") == 0.61
    assert round_to_tick(0.6123, "sell") == 0.615
    assert round_to_tick(0.61, "buy") == 0.61
    assert round_to_tick(0.0001, "buy") == 0.005


def test_buys_yes_when_sig_cheap_and_stops_at_min_edge():
    b = book([(0.50, 100)], [(0.52, 200), (0.54, 400), (0.58, 1000)])
    o = plan_entry("e1", 0.60, b, **KW)
    assert (o.side, o.action) == ("yes", "buy")
    # 0.52 and 0.54 have >= 0.04 edge; 0.58 does not. Half of each level.
    assert o.qty == 100 + 200 and o.price == 0.54


def test_buys_no_when_sig_rich():
    b = book([(0.70, 300)], [(0.72, 300)])
    o = plan_entry("e1", 0.60, b, **KW)
    assert o.side == "no" and abs(o.price - 0.30) < 1e-9 and abs(o.fair - 0.40) < 1e-9


def test_no_trade_inside_edge():
    assert plan_entry("e1", 0.60, book([(0.58, 100)], [(0.62, 100)]), **KW) is None


def test_size_capped_by_kelly_and_max_cost():
    b = book([], [(0.50, 1_000_000)])
    o = plan_entry("e1", 0.60, b, **KW)
    stake = kelly_cost(0.60, 0.50, 0.25, 100_000)  # 0.25 * 0.2 * 100k = 5000
    assert abs(stake - 5000) < 1e-6 and o.qty == 10_000
    o = plan_entry("e1", 0.60, b, **{**KW, "max_cost": 1000})
    assert o.qty == 2000


def test_exit_when_converged():
    h = Holding("e1", "yes", 300, 0.53, opened_at=0)
    b = book([(0.595, 200), (0.59, 500)], [(0.60, 100)])
    o = plan_exit(h, 0.60, b, now=10, **EXIT)
    assert o.reason == "converged" and o.action == "sell" and o.qty == 300 and o.price == 0.59


def test_hold_while_still_cheap():
    h = Holding("e1", "yes", 300, 0.53, opened_at=0)
    assert plan_exit(h, 0.60, book([(0.55, 500)], [(0.56, 100)]), now=10, **EXIT) is None


def test_stop_when_fair_falls_below_cost():
    h = Holding("e1", "yes", 100, 0.53, opened_at=0)
    o = plan_exit(h, 0.40, book([(0.37, 50), (0.36, 500)], [(0.45, 100)]), now=10, **EXIT)
    # converged check first: bid 0.37 >= 0.40-0.01? no. Fair 0.40 <= 0.53-0.08 -> stop.
    assert o.reason == "stop" and o.qty == 100 and o.price == 0.36


def test_no_side_exit_uses_yes_asks():
    h = Holding("e1", "no", 100, 0.30, opened_at=0)
    o = plan_exit(h, 0.60, book([(0.55, 100)], [(0.605, 500)]), now=10, **EXIT)
    assert o.reason == "converged" and abs(o.price - 0.395) < 1e-9


def test_timeout_exit():
    h = Holding("e1", "yes", 100, 0.53, opened_at=0)
    o = plan_exit(h, None, book([(0.55, 500)], []), now=73 * 3600, **EXIT)
    assert o.reason == "timeout"


def test_fair_value_filters_and_weights():
    now = 1000.0
    k = RefLeg("e1", "x", "kalshi", "K1", False, 1)
    p = RefLeg("e1", "x", "polymarket", "a:Yes", False, 1)
    quotes = {("kalshi", "K1"): RefQuote("kalshi", "K1", 0.58, 0.60, now),
              ("polymarket", "a:Yes"): RefQuote("polymarket", "a:Yes", 0.60, 0.64, now)}
    f, _ = fair_value([k, p], quotes, now, max_age=60, max_spread=0.06, max_disagreement=0.05, min_sources=1)
    # mids 0.59 (spread .02, weight 50) and 0.62 (spread .04, weight 25)
    assert abs(f.p - (0.59 * 50 + 0.62 * 25) / 75) < 1e-9 and f.n_sources == 2
    f, why = fair_value([k], {("kalshi", "K1"): RefQuote("kalshi", "K1", 0.4, 0.6, now)}, now,
                        max_age=60, max_spread=0.06, max_disagreement=0.05, min_sources=1)
    assert f is None and "spread" in why
    f, why = fair_value([k], {("kalshi", "K1"): RefQuote("kalshi", "K1", 0.58, 0.6, now - 100)}, now,
                        max_age=60, max_spread=0.06, max_disagreement=0.05, min_sources=1)
    assert f is None and "stale" in why


def test_inverted_and_summed_legs():
    now = 0.0
    leg = RefLeg("e1", "x", "kalshi", "A+B", True, 1)
    quotes = {("kalshi", "A"): RefQuote("kalshi", "A", 0.30, 0.31, now),
              ("kalshi", "B"): RefQuote("kalshi", "B", 0.10, 0.11, now)}
    f, _ = fair_value([leg], quotes, now, max_age=60, max_spread=0.06, max_disagreement=0.05, min_sources=1)
    # sum 0.40/0.42 -> inverted 0.58/0.60
    assert abs(f.p - 0.59) < 1e-9
