from datetime import datetime, timezone

from sigcup import value as V
from sigcup.sig_api import Book, Level, Position
from sigcup.strategy import Holding
from sigcup.references import RefQuote

from test_bot import make_bot


def test_edge_is_return_on_cash():
    assert abs(V.edge(0.98, 0.90) - 0.0889) < 1e-3   # 8 points on 90c
    assert abs(V.edge(0.35, 0.30) - 0.1667) < 1e-3   # 5 points on 30c ranks higher


def test_race_scaled_only_near_one():
    races = [["d", "r"], ["x", "y"]]
    out = V.race_scaled({"d": 0.52, "r": 0.50, "x": 0.40, "y": 0.40}, races)
    assert abs(out["d"] + out["r"] - 1) < 1e-9          # 1.02 -> scaled
    assert out["x"] == 0.40                             # 0.80: a contender the Cup does not list, left alone


def test_state_of():
    assert V.state_of("Rhode Island Senate") == "RI"
    assert V.state_of("West Virginia Governor") == "WV"
    assert V.state_of("PA-07 House race") == "PA"
    assert V.state_of("U.S. House") is None


def test_ladder_levels_under_favourite_touch():
    # Cup favourite at 0.88/0.89, fair 0.98: bids at .88/.86/.84/.82, each >= 8% edge
    book = Book("e", [Level(0.88, 10)], [Level(0.89, 10)])
    lv = V.ladder_levels("e", 0.98, book, favourite_p=0.9, offsets=[0, .02, .04, .06], min_edge=0.08,
                         level_cost=3000)
    assert [l.price for l in lv] == [0.88, 0.86, 0.84, 0.82] and all(l.side == "yes" for l in lv)
    assert lv[0].qty == int(3000 / 0.88)
    # longshot YES at 0.10/0.12 with fair 0.03 -> NO side is the favourite: NO bid = 1 - 0.12 = 0.88
    lv = V.ladder_levels("e", 0.03, Book("e", [Level(0.10, 1)], [Level(0.12, 1)]), favourite_p=0.9,
                         offsets=[0, .02], min_edge=0.08, level_cost=3000)
    assert [(l.side, l.price) for l in lv] == [("no", 0.88), ("no", 0.86)]
    # edge below 8% at the touch: nothing
    assert V.ladder_levels("e", 0.95, book, favourite_p=0.9, offsets=[0], min_edge=0.08, level_cost=3000) == []


def test_within_budget_trims_last():
    lv = [V.Level("a", "yes", 0.9, 1000, 0.10), V.Level("b", "yes", 0.8, 1000, 0.20)]
    out = V.within_budget(lv, 1200)
    assert [(l.exchange_id, l.qty) for l in out] == [("b", 1000), ("a", 444)]


def test_swap_sellers_and_plan():
    hs = [Holding("a", "yes", 1000, 0.90, 0), Holding("b", "yes", 1000, 0.80, 0), Holding("c", "yes", 500, .5, 0)]
    fairs = {"a": 0.985, "b": 0.95, "c": 0.60}
    tops = {"a": (0.98, 0.99), "b": (0.85, 0.86), "c": (0.50, 0.52)}
    sellers = V.swap_sellers(hs, fairs, tops, max_keep_edge=0.05, sell_margin=0.03, pinned=set())
    # a: keep (0.985-0.98)/0.98 = 0.5% -> seller; b: 11.8% keep -> no; c: 20% -> no
    assert [x.exchange_id for x in sellers] == ["a"]
    sales = V.plan_swap_sales(sellers, best_buy_edge=0.10, need=500, turnover_left=15000, min_gain=0.05)
    assert sales[0][1] == 511  # ceil(500 / 0.98)
    assert V.plan_swap_sales(sellers, best_buy_edge=0.04, need=500, turnover_left=15000, min_gain=0.05) == []
    # floor: a sale more than 3c below fair is never made
    assert V.swap_sellers(hs, {"a": 1.0, "b": .95, "c": .6}, {"a": (0.96, 0.97), "b": (.85, .86), "c": (.5, .52)},
                          max_keep_edge=0.05, sell_margin=0.03, pinned=set()) == []


def test_swing():
    r_up, d_up = V.swing_value_change([("Republican", "yes", 1000, 0.80), ("Democratic", "no", 1000, 0.20)], 0.15)
    assert abs(r_up - 300) < 1e-6 and abs(d_up + 300) < 1e-6


def test_bot_ladder_places_tracks_fills_and_requotes(tmp_path):
    bot, clock = make_bot(tmp_path, live=True, fair=(0.97, 0.99))
    s = bot.s
    s.ladder_enabled, s.min_edge = True, 0.5  # no gap entries, ladder only
    bot.api.prices_["e1"] = (0.88, 0.89)
    bot.api.book_ = Book("e1", [Level(0.88, 10)], [Level(0.89, 10)])
    bot.cycle()
    placed = [x for x in bot.api.sent if x[2] == "buy"]
    assert sorted(x[4] for x in placed) == [0.82, 0.84, 0.86, 0.88]
    rest = bot.ledger.resting()
    assert len(rest) == 4
    # a fill on the 0.86 level arrives
    oid = [r[0] for r in rest if r[3] == 0.86][0]
    bot.api.fills_ = [{"id": 5, "orderId": oid, "exchangeId": "e1", "price": 0.86, "quantity": 100, "side": "yes"}]
    clock[0] += 30
    bot.kalshi.q["KX-R"] = RefQuote("kalshi", "KX-R", 0.97, 0.99, clock[0])
    bot._last_ref = 0
    bot.cycle()
    [h] = bot.ledger.holdings()
    assert (h.qty, h.avg_cost) == (100, 0.86)
    assert len([x for x in bot.api.sent if x[2] == "buy"]) == 4  # kept: touch and fair unchanged
    # the touch moves 2c: the market is re-quoted
    bot.api.prices_["e1"] = (0.90, 0.91)
    clock[0] += 30
    bot.kalshi.q["KX-R"] = RefQuote("kalshi", "KX-R", 0.97, 0.99, clock[0])
    bot._last_ref = 0
    bot.cycle()
    assert len(bot.api.cancelled) == 4 and len([x for x in bot.api.sent if x[2] == "buy"]) > 4


def test_ladder_off_before_election_night_and_cancels(tmp_path):
    bot, clock = make_bot(tmp_path, live=True, fair=(0.97, 0.99))
    s = bot.s
    s.ladder_enabled, s.min_edge = True, 0.5
    s.election_night_start = datetime.fromtimestamp(clock[0] + 7200, timezone.utc).isoformat()
    bot.api.prices_["e1"] = (0.88, 0.89)
    bot.cycle()
    assert len(bot.ledger.resting()) == 4
    clock[0] += 3700  # within an hour of election night
    bot.kalshi.q["KX-R"] = RefQuote("kalshi", "KX-R", 0.97, 0.99, clock[0])
    bot._last_ref = 0
    bot.cycle()
    assert bot.ledger.resting() == [] and len(bot.api.cancelled) == 4


def test_election_night_buys_lagging_called_race(tmp_path):
    bot, clock = make_bot(tmp_path, fair=(0.97, 0.98))
    s = bot.s
    s.night_enabled, s.min_edge = True, 0.5   # ordinary entries off
    s.election_night_start = datetime.fromtimestamp(clock[0] - 60, timezone.utc).isoformat()
    s.election_reserve = 50_000
    bot.api.prices_["e1"] = (0.90, 0.92)
    bot.api.book_ = Book("e1", [Level(0.90, 1000)], [Level(0.92, 1000), Level(0.96, 1000)])
    assert bot.night() and bot.reserve() == s.cash_reserve  # reserve released
    bot.cycle()
    [h] = bot.ledger.holdings()
    assert h.side == "yes" and h.avg_cost == 0.92   # 0.96 is not 2c under the 0.97 reference bid
    # closing: no new orders
    s.trading_close = datetime.fromtimestamp(clock[0] + 300, timezone.utc).isoformat()
    assert bot.entries_blocked() == "trading closes soon"


def test_allocator_sells_low_edge_holding_for_better_buy(tmp_path):
    bot, clock = make_bot(tmp_path, live=True, fair=(0.59, 0.61))
    s = bot.s
    s.alloc_enabled, s.min_return = True, 0.05
    s.cash_reserve, s.election_reserve = 0, 0
    # nearly settled holding on e2-like market "z" (not mapped): use e1's map only for the buy
    bot.ledger.replace_holdings([("conv", "z", "yes", 5000, 0.95, clock[0])])
    bot.scaled = {}
    bot.map["z"] = []
    bot.api.prices_["z"] = (0.985, 0.99)
    bot.api.holdings_value = 99_990   # no spare cash
    bot.compute_fairs = lambda: setattr(bot, "scaled", {"e1": 0.60, "z": 0.99})
    bot.fairs = {}
    bot.cycle()
    sells = [x for x in bot.api.sent if x[2] == "sell"]
    assert sells and sells[0][0] == "z" and sells[0][1] == "yes" and sells[0][4] == 0.985


def test_state_cap_limits_entries(tmp_path):
    from sigcup.sig_api import Exchange, Market
    bot, clock = make_bot(tmp_path)
    bot.api.markets_ = [Market("m1", "Will the Republican Party win the Texas Senate?", "open", None, [Exchange("e1", None)]),
                        Market("m2", "Will the Republican Party win the Texas Governor?", "open", None, [Exchange("tg", None)])]
    bot.s.state_max_cost = 100
    bot.refresh_races()
    bot.labels["tg"] = "Texas Governor [Republican]"
    bot.ledger.replace_holdings([("conv", "tg", "yes", 100, 0.9, clock[0])])  # 90 already in Texas
    bot.cycle()
    [h] = [h for h in bot.ledger.holdings() if h.exchange_id == "e1"]
    assert h.qty * h.avg_cost <= 10 + 1e-9   # only 10 left under the 100 Texas cap


def test_ladder_respects_race_cap(tmp_path):
    bot, clock = make_bot(tmp_path, live=True, fair=(0.97, 0.99))
    s = bot.s
    s.ladder_enabled, s.min_edge, s.max_race_cost = True, 0.5, 4000
    bot.labels["e1"] = "Texas Senate [R]"
    bot.ledger.replace_holdings([("conv", "e1", "yes", 1000, 0.90, clock[0])])   # 900 used of 4000
    bot.api.prices_["e1"] = (0.88, 0.89)
    bot.cycle()
    assert sum(r[3] * r[4] for r in bot.ledger.resting()) <= 3100 + 1e-6
