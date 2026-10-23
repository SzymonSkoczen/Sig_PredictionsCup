from sigcup.arb import group_races, plan_buy, plan_repair, plan_sell, screen_buy
from sigcup.sig_api import Book, Exchange, Level, Market
from sigcup.strategy import Holding

from test_bot import make_bot


def mkt(eid, party, race="Texas Senate", status="open"):
    return Market(f"m{eid}", f"Will the {party} Party win the {race}?", status, None, [Exchange(eid, None)])


def test_group_races_by_title():
    races = group_races([mkt("d", "Democratic"), mkt("r", "Republican"), mkt("x", "Democratic", "Ohio Senate"),
                         mkt("z", "Republican", "Iowa Senate", status="settled"),
                         Market("q", "Something else?", "open", None, [Exchange("q", None)])])
    assert [(r.key, r.exchange_ids) for r in races] == [("Texas Senate", ["d", "r"])]


def books(d_bids, r_bids, d_asks=((0.99, 1),), r_asks=((0.99, 1),)):
    mk = lambda e, b, a: Book(e, [Level(p, q) for p, q in b], [Level(p, q) for p, q in a])
    return {"d": mk("d", d_bids, d_asks), "r": mk("r", r_bids, r_asks)}


def test_buy_basket_when_yes_bids_sum_above_one():
    [race] = group_races([mkt("d", "Democratic"), mkt("r", "Republican")])
    b = books([(0.45, 200), (0.43, 1000)], [(0.60, 100), (0.58, 1000)])
    assert abs(screen_buy(race, {"d": (0.45, 0.5), "r": (0.60, 0.65)}) - 0.05) < 1e-9
    o = plan_buy(race, b, min_profit=0.02, max_sets=10_000, depth_fraction=1.0)
    # NO asks: d 0.55/0.57, r 0.40/0.42. Sets: 100 @ .95, 100 @ .97, then .57+.42=.99 (< 0.02 profit) stops
    assert o.sets == 200 and o.limits == (0.55, 0.42)
    assert abs(o.per_set - (0.55 + 0.41)) < 1e-9
    assert all(l.side == "no" and l.action == "buy" and l.qty == 200 for l in o.leg_orders())


def test_no_basket_when_bids_sum_below_one():
    [race] = group_races([mkt("d", "Democratic"), mkt("r", "Republican")])
    assert plan_buy(race, books([(0.45, 100)], [(0.54, 100)]), min_profit=0.01, max_sets=100,
                    depth_fraction=1.0) is None


def test_sell_basket_and_repair():
    [race] = group_races([mkt("d", "Democratic"), mkt("r", "Republican")])
    # YES asks 0.40 + 0.55 -> NO sells for 0.60 + 0.45 = 1.05 per set
    b = books([], [], d_asks=[(0.40, 500)], r_asks=[(0.55, 500)])
    o = plan_sell(race, b, sets_held=300, bar=1.0)
    assert o.sets == 300 and abs(o.per_set - 1.05) < 1e-9
    held = {"d": Holding("d", "no", 300, 0.55, 0), "r": Holding("r", "no", 100, 0.40, 0)}
    b = books([(0.45, 100), (0.43, 500)], [(0.62, 500)], d_asks=[(0.56, 500)], r_asks=[(0.62, 500)])
    [rep] = plan_repair(race, held, b, slippage=0.02, unwind=False)
    # r needs 200 more NO; cap = 1 + 0.02 - 0.55 = 0.47; NO asks from r YES bids: 0.38 -> fill all
    assert (rep.exchange_id, rep.action, rep.qty) == ("r", "buy", 200) and abs(rep.price - 0.38) < 1e-9
    [unw] = plan_repair(race, held, b, slippage=0.02, unwind=True)
    assert (unw.exchange_id, unw.action, unw.qty) == ("d", "sell", 200) and abs(unw.price - 0.44) < 1e-9


def test_bot_paper_arb_cycle(tmp_path):
    bot, clock = make_bot(tmp_path)
    bot.map = {}
    bot.api.markets_ = [mkt("d", "Democratic"), mkt("r", "Republican")]
    bot.api.prices_ = {"d": (0.45, 0.47), "r": (0.60, 0.62)}
    bot.api.books_ = books([(0.45, 400)], [(0.60, 400)], d_asks=[(0.47, 400)], r_asks=[(0.62, 400)])
    bot.cycle()
    held = {h.exchange_id: h.qty for h in bot.ledger.holdings("arb")}
    assert held == {"d": 200, "r": 200}  # half the shown depth
    assert bot.ledger.holdings("conv") == []
    assert "Arb baskets held (1)" in bot.report()


def test_every_leg_priced_when_one_ladder_runs_out_first():
    [race] = group_races([mkt("d", "Democratic"), mkt("r", "Republican")])
    # d's only level is used up by the first sets; r still has depth
    o = plan_buy(race, books([(0.45, 200)], [(0.60, 1000)]), min_profit=0.01, max_sets=10_000,
                 depth_fraction=1.0)
    assert o.sets == 200 and o.limits == (0.55, 0.40)
    assert abs(o.per_set - 0.95) < 1e-9
