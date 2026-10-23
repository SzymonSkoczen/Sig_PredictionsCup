import json

import httpx

from sigcup.bot import Bot
from sigcup.config import Settings
from sigcup.ledger import Ledger
from sigcup.references import KalshiFeed, PolymarketFeed, RefQuote
from sigcup.sig_api import Book, Level, Position, SigApi, RateLimiter
from sigcup.strategy import Order


class FakeApi:
    def __init__(self):
        self.prices_ = {"e1": (0.50, 0.52)}
        self.book_ = Book("e1", [Level(0.50, 100)], [Level(0.52, 400)])
        self.positions_ = []
        self.markets_ = []
        self.sent = []
        self.reads = self.writes = RateLimiter(60)
        self.error_count = 0

    def markets(self):
        return self.markets_

    def place_multi_leg(self, legs, ttl):
        self.sent.append(("multi", legs))
        return [{"id": i} for i in range(len(legs))]

    def prices(self, ids):
        return {i: self.prices_[i] for i in ids if i in self.prices_}

    def book(self, eid):
        return self.books_.get(eid, self.book_) if hasattr(self, "books_") else self.book_

    def positions(self):
        return self.positions_

    def place_order(self, *a):
        self.sent.append(a)
        return {"ok": True}

    def pnl(self):
        return {"totalPnl": 12.5}


class FakeFeed:
    def __init__(self, quotes):
        self.q = quotes

    def quotes(self, refs):
        return {r: self.q[r] for r in refs if r in self.q}


class FakeNotifier:
    channels = []

    def __init__(self):
        self.sent = []

    def send(self, title, body):
        self.sent.append((title, body))
        return []


def make_bot(tmp_path, live=False, fair=(0.59, 0.61)):
    m = tmp_path / "map.csv"
    m.write_text("sig_exchange_id,label,source,ref,invert,weight,enabled\n"
                 "e1,Texas Senate [R],kalshi,KX-R,0,1,1\n"
                 "e2,Ignored,kalshi,KX-D,0,1,0\n")
    s = Settings(map_path=str(m), db_path=str(tmp_path / "db.sqlite"), kill_switch=str(tmp_path / "KILL"))
    clock = [1_000_000.0]
    kalshi = FakeFeed({"KX-R": RefQuote("kalshi", "KX-R", *fair, clock[0])})
    bot = Bot(s, FakeApi(), kalshi, FakeFeed({}), Ledger(s.db_path, "live" if live else "paper"),
              FakeNotifier(), live=live, clock=lambda: clock[0])
    return bot, clock


def test_paper_cycle_enters_then_exits_on_convergence(tmp_path):
    bot, clock = make_bot(tmp_path)
    assert list(bot.map) == ["e1"]  # disabled row ignored
    bot.cycle()
    [h] = bot.ledger.holdings()
    assert (h.side, h.avg_cost) == ("yes", 0.52) and h.qty == 200  # half the level
    # SIG converges up to the reference
    bot.api.prices_["e1"] = (0.595, 0.60)
    bot.api.book_ = Book("e1", [Level(0.595, 1000)], [Level(0.60, 1000)])
    clock[0] += 60
    bot.kalshi.q["KX-R"] = RefQuote("kalshi", "KX-R", 0.59, 0.61, clock[0])
    bot._last_ref = 0
    bot.cycle()
    assert bot.ledger.holdings() == []
    assert abs(bot.ledger.realized_since(0) - 200 * (0.595 - 0.52)) < 1e-6
    report = bot.report()
    assert "PAPER" in report and "Trades last 2h (2)" in report and "totalPnl=12.5" in report
    assert "price gaps: 1 markets reached ≥0.04" in report and "Texas Senate [R] +0.080" in report
    assert "depth at best price: median" in report


def test_kill_switch_blocks_entries_but_alerts_once(tmp_path):
    bot, _ = make_bot(tmp_path)
    (tmp_path / "KILL").write_text("x")
    bot.cycle()
    bot.cycle()
    assert bot.ledger.holdings() == []
    assert len([t for t, _ in bot.notifier.sent if "alert" in t]) == 1


def test_no_trade_without_fresh_reference(tmp_path):
    bot, clock = make_bot(tmp_path)
    clock[0] += 10_000  # quote is now stale
    bot.kalshi.q = {}
    bot.cycle()
    assert bot.ledger.holdings() == []


def test_live_order_reconciled_from_positions(tmp_path):
    bot, clock = make_bot(tmp_path, live=True)
    bot.cycle()
    [(eid, side, action, qty, price, ttl)] = bot.api.sent
    assert (eid, side, action, qty, price) == ("e1", "yes", "buy", 200, 0.52)
    assert bot.ledger.holdings() == []  # not until confirmed
    # Order partially filled on the exchange
    bot.api.positions_ = [Position("e1", "m1", "Texas", "yes", 150, 0.52, 0)]
    clock[0] += ttl + 5
    bot.kalshi.q["KX-R"] = RefQuote("kalshi", "KX-R", 0.59, 0.61, clock[0])
    bot.api.prices_["e1"] = (0.50, 0.58)  # edge gone, no new entry
    bot.cycle()
    [h] = bot.ledger.holdings()
    assert h.qty == 150


def test_ledger_ignores_manual_position_changes_without_pending(tmp_path):
    led = Ledger(":memory:")
    assert led.reconcile({("e1", "yes"): 500}, now=1e9) == []
    assert led.holdings() == []
    led.record_fill(Order("e1", "yes", "buy", 10, 0.4, 0.5, "t"), 10, "x")
    led.record_fill(Order("e1", "yes", "sell", 999, 0.5, 0.5, "t"), 999, "x")  # can't sell more than held
    assert abs(led.realized_since(0) - 1.0) < 1e-9


def test_sig_api_order_body_and_retry():
    calls = []

    def handler(req: httpx.Request):
        calls.append(req)
        if req.url.path.endswith("/tournaments/cup"):
            return httpx.Response(200, json={"id": 42})
        if len([c for c in calls if c.method == "POST"]) == 1:
            return httpx.Response(502, json={"error": {"code": "ORDER_STATUS_UNKNOWN", "message": "?"}})
        return httpx.Response(200, json={"data": {"id": 7}})

    api = SigApi("k", "https://x/api/v1", "cup", transport=httpx.MockTransport(handler), sleep=lambda s: None)
    api.place_order("e1", "no", "buy", 10, 0.3333, ttl_seconds=15)
    posts = [c for c in calls if c.method == "POST"]
    assert len(posts) == 2
    b1, b2 = (json.loads(p.content) for p in posts)
    assert b1 == b2  # same idempotency key on retry
    assert b1["tournamentId"] == "42" and b1["price"] == 0.33 and b1["side"] == "no"
    assert posts[0].headers["Authorization"] == "Bearer k"


def test_kalshi_and_polymarket_parsing():
    def handler(req: httpx.Request):
        if req.url.host == "k":
            return httpx.Response(200, json={"markets": [
                {"ticker": "A", "status": "active", "yes_bid_dollars": "0.4100", "yes_ask_dollars": "0.4300"},
                {"ticker": "B", "status": "active", "yes_bid": 0, "yes_ask": 12}]})
        if req.url.host == "g":
            return httpx.Response(200, json=[{"outcomes": '["Yes","No"]', "clobTokenIds": '["111","222"]'}])
        return httpx.Response(200, json=[{"asset_id": "222", "bids": [{"price": "0.30", "size": "5"},
                                                                       {"price": "0.35", "size": "9"}],
                                          "asks": [{"price": "0.40", "size": "1"}]}])

    t = httpx.MockTransport(handler)
    k = KalshiFeed("https://k", transport=t, sleep=lambda s: None).quotes(["A", "B"])
    assert (k["A"].bid, k["A"].ask) == (0.41, 0.43) and (k["B"].bid, k["B"].ask) == (None, 0.12)
    p = PolymarketFeed("https://g", "https://c", transport=t, sleep=lambda s: None).quotes(["slug:No"])
    assert (p["slug:No"].bid, p["slug:No"].ask) == (0.35, 0.40)


def test_decide_live_gates(tmp_path):
    from datetime import datetime, timezone
    from sigcup.cli import decide_live, ledger_path
    s = Settings(mode="live", db_path=str(tmp_path / "s.db"), live_from="2026-10-23T00:00:00+01:00",
                 paper_min_cycles=30)
    before = datetime(2026, 10, 22, 20, tzinfo=timezone.utc)
    after = datetime(2026, 10, 23, 1, tzinfo=timezone.utc)
    assert decide_live(s, True, before)[0] is False
    assert decide_live(s, False, after)[0] is False
    live, why = decide_live(s, True, after)
    assert live is False and "0/30" in why  # no paper history yet
    Ledger(ledger_path(s, False)).put("paper_cycles", 30)
    assert decide_live(s, True, after) == (True, "live")
    assert ledger_path(s, True).name == "s-live.db"


def test_review_digest(tmp_path):
    from sigcup.cli import ledger_path, review_text
    s = Settings(db_path=str(tmp_path / "s.db"))
    led = Ledger(ledger_path(s, False))
    led.event("ERROR", "KeyError: 'bestBid'")
    led.event("ERROR", "KeyError: 'bestBid'")
    led.event("INFO", "buy no Texas [D]: filled 50/200")
    led.event("INFO", "buy no Texas [R]: filled 200/200")
    led.record_fill(Order("e1", "yes", "buy", 10, 0.5, 0.6, "edge"), 10, "X")
    led.record_fill(Order("e1", "yes", "sell", 10, 0.4, 0.4, "stop"), 10, "X")
    txt = review_text(s, 3)
    assert "ERROR x2: KeyError: 'bestBid'" in txt
    assert "filled 50/200" in txt and "filled 200/200" not in txt
    assert "LOSS: X yes sell 10 @0.400 (stop) -1" in txt


def test_other_opportunities_section(tmp_path):
    from sigcup.sig_api import Exchange, Market
    bot, clock = make_bot(tmp_path)
    bot.api.markets_ = [Market("m1", "Will the Democratic Party win the Ohio Senate?", "open", None, [Exchange("d", None)]),
                        Market("m2", "Will the Republican Party win the Ohio Senate?", "open", None, [Exchange("r", None)])]
    bot.api.prices_.update({"d": (0.30, 0.45), "r": (0.50, 0.52)})
    bot.cycle()
    clock[0] += 60
    bot.kalshi.q["KX-R"] = RefQuote("kalshi", "KX-R", 0.65, 0.67, clock[0])
    bot._last_ref = 0
    bot.cycle()
    txt = "\n".join(bot.other_opportunity_lines())
    assert "wide spreads" in txt and "Ohio Senate [Democratic] 0.150" in txt
    assert "Ohio Senate +0.030" in txt          # 1 - (0.45 + 0.52)
    assert "Texas Senate [R] ref +0.060" in txt  # fair 0.60 -> 0.66
    assert "2 Cup markets have no Kalshi/Polymarket mapping" in txt


def test_rejected_order_does_not_kill_cycle_and_scope_error_stops_orders(tmp_path):
    from sigcup.sig_api import ApiError
    bot, clock = make_bot(tmp_path, live=True)

    def refuse(*a):
        raise ApiError(403, "INSUFFICIENT_SCOPES", "Required: trade")
    bot.api.place_order = refuse
    bot.cycle()  # must not raise
    assert bot.health.consecutive_errors == 0 and bot.health.cycles == 1
    assert "INSUFFICIENT_SCOPES" in bot.entries_blocked()
    assert bot.ledger.pending_exchanges() == set()
    assert any("can't place orders" in b for _, b in bot.notifier.sent)


def test_arb_sets_capped_per_race_across_cycles(tmp_path):
    from test_arb import books, mkt
    bot, clock = make_bot(tmp_path)
    bot.map = {}
    bot.s.arb_max_sets = 300
    bot.api.markets_ = [mkt("d", "Democratic"), mkt("r", "Republican")]
    bot.api.prices_ = {"d": (0.45, 0.47), "r": (0.60, 0.62)}
    bot.api.books_ = books([(0.45, 400)], [(0.60, 400)], d_asks=[(0.47, 400)], r_asks=[(0.62, 400)])
    for _ in range(5):  # paper books never deplete: must stop at the cap
        bot.cycle()
    assert {h.exchange_id: h.qty for h in bot.ledger.holdings("arb")} == {"d": 300, "r": 300}


def test_no_position_parsed_as_positive_and_resync(tmp_path):
    from sigcup.sig_api import Exchange, Market
    raw = {"exchangeId": "d", "marketId": "1", "marketTitle": "x", "option": "YES", "quantity": -300,
           "avgCost": 0.55, "lots": [{"side": "NO", "quantity": 300}]}
    p = Position.from_api(raw)
    assert (p.side, p.qty, p.avg_cost) == ("no", 300.0, 0.55)
    assert Position.from_api({**raw, "lots": []}).side == "no"

    bot, clock = make_bot(tmp_path, live=True)
    bot.api.markets_ = [Market("m1", "Will the Democratic Party win the Ohio Senate?", "open", None, [Exchange("d", None)]),
                        Market("m2", "Will the Republican Party win the Ohio Senate?", "open", None, [Exchange("r", None)])]
    bot.refresh_races()
    bot.api.positions_ = [Position("d", "1", "", "no", 300, 0.55, 0), Position("r", "2", "", "no", 500, 0.43, 0),
                          Position("e1", "3", "", "yes", 40, 0.5, 0)]
    bot.resync_from_exchange()
    arb = {h.exchange_id: h.qty for h in bot.ledger.holdings("arb")}
    conv = {(h.exchange_id, h.side): h.qty for h in bot.ledger.holdings("conv")}
    assert arb == {"d": 300, "r": 300}
    assert conv == {("r", "no"): 200, ("e1", "yes"): 40}


def test_live_reconcile_with_negative_no_quantity(tmp_path):
    bot, clock = make_bot(tmp_path, live=True, fair=(0.40, 0.42))  # SIG too high -> buy NO
    bot.cycle()
    [(eid, side, action, qty, price, ttl)] = bot.api.sent
    assert side == "no"
    raw = {"exchangeId": "e1", "quantity": -qty, "avgCost": price, "lots": [{"side": "NO"}]}
    bot.api.positions_ = [Position.from_api(raw)]
    clock[0] += ttl + 5
    bot.kalshi.q["KX-R"] = RefQuote("kalshi", "KX-R", 0.40, 0.42, clock[0])
    bot._last_ref = 0
    bot.api.prices_["e1"] = (0.44, 0.46)  # edge gone
    bot.cycle()
    [h] = bot.ledger.holdings()
    assert (h.side, h.qty) == ("no", qty) and len(bot.api.sent) == 1  # credited once, no re-buy
