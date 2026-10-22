"""Command line: `sigcup <command>`. Run `sigcup -h` for the list."""
from __future__ import annotations

import argparse
import csv
import difflib
import logging
import re
import signal
import sys
from datetime import datetime, timezone
from pathlib import Path

from .bot import Bot
from .config import Settings
from .ledger import Ledger
from .notify import Notifier
from .pricing import write_map
from .references import KalshiFeed, PolymarketFeed
from .sig_api import SigApi


def ledger_path(s: Settings, live: bool) -> Path:
    """Paper and live keep separate ledgers, so paper positions are never "sold" for real."""
    p = Path(s.db_path)
    return p.with_name(f"{p.stem}-{'live' if live else 'paper'}{p.suffix or '.db'}")


def decide_live(s: Settings, want_live: bool, now: datetime | None = None) -> tuple[bool, str]:
    """Live only with --live, MODE=live, after LIVE_FROM, and after a healthy paper run."""
    now = now or datetime.now(timezone.utc)
    if not want_live:
        return False, "paper (no --live flag)"
    if not s.live:
        return False, "paper (MODE is not live)"
    if s.live_from:
        start = datetime.fromisoformat(s.live_from)
        if now < start:
            return False, f"paper until {start.isoformat()}"
    cycles = int(Ledger(ledger_path(s, False)).get("paper_cycles", "0"))
    if cycles < s.paper_min_cycles:
        return False, f"paper: live blocked, only {cycles}/{s.paper_min_cycles} healthy paper cycles so far"
    return True, "live"


def build(s: Settings, live: bool) -> Bot:
    if not s.sig_api_key:
        sys.exit("Set SIG_API_KEY (environment variable or .env; see .env.example).")
    api = SigApi(s.sig_api_key, s.sig_base_url, s.sig_tournament_slug, s.read_budget, s.write_budget)
    api.pick_tournament()
    return Bot(s, api, KalshiFeed(s.kalshi_base_url), PolymarketFeed(s.polymarket_gamma_url, s.polymarket_clob_url),
               Ledger(ledger_path(s, live), "live" if live else "paper"), Notifier(s), live=live)


def cmd_check(s: Settings, args) -> None:
    api = SigApi(s.sig_api_key, s.sig_base_url, s.sig_tournament_slug, s.read_budget, s.write_budget)
    print("account:", api.account())
    api.pick_tournament()
    for t in api.tournaments():
        print(f"  tournament slug={t.get('slug')} id={t.get('id')} name={t.get('name') or t.get('title')}")
    if api.slug:
        print("tournament:", api.slug, "id:", api.tournament_id)
        print("markets:", len(api.markets()))
    print("notification channels:", Notifier(s).channels or "none configured")


def cmd_markets(s: Settings, args) -> None:
    """Dump every SIG exchange to CSV: the starting point for the market map."""
    api = SigApi(s.sig_api_key, s.sig_base_url, s.sig_tournament_slug, s.read_budget, s.write_budget)
    api.pick_tournament()
    rows = []
    for m in api.markets():
        for e in m.exchanges:
            label = f"{m.title} [{e.option}]" if e.option else m.title
            rows.append({"sig_exchange_id": e.id, "market_id": m.id, "label": label, "status": m.status,
                         "settlement_date": m.settlement_date or ""})
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]) if rows else ["sig_exchange_id"])
        w.writeheader()
        w.writerows(rows)
    print(f"wrote {len(rows)} exchanges to {out}")


def _tokens(text: str) -> set[str]:
    stop = {"the", "will", "win", "of", "in", "a", "2026", "election", "race", "who", "be", "to", "for", "and"}
    return {w for w in re.findall(r"[a-z]+", text.lower()) if w not in stop and len(w) > 1}


def _score(a: str, b: str) -> float:
    ta, tb = _tokens(a), _tokens(b)
    if not ta or not tb:
        return 0.0
    jac = len(ta & tb) / len(ta | tb)
    return 0.7 * jac + 0.3 * difflib.SequenceMatcher(None, a.lower(), b.lower()).ratio()


def cmd_suggest_map(s: Settings, args) -> None:
    """Fuzzy-match SIG exchanges to Kalshi/Polymarket markets. Every row is written with
    enabled=0: check each one by hand (same race, same outcome, invert?) before enabling."""
    api = SigApi(s.sig_api_key, s.sig_base_url, s.sig_tournament_slug, s.read_budget, s.write_budget)
    api.pick_tournament()
    sig = [(e.id, f"{m.title} [{e.option}]" if e.option else m.title)
           for m in api.markets() for e in m.exchanges]
    print(f"{len(sig)} SIG exchanges; loading Kalshi events…")
    kalshi = KalshiFeed(s.kalshi_base_url).open_election_markets()
    poly = PolymarketFeed(s.polymarket_gamma_url, s.polymarket_clob_url)
    rows = []
    for eid, label in sig:
        best_k = sorted(kalshi, key=lambda k: -_score(label, k["title"]))[:args.per_source]
        for k in best_k:
            if _score(label, k["title"]) >= args.min_score:
                rows.append({"sig_exchange_id": eid, "label": label, "source": "kalshi", "ref": k["ticker"],
                             "invert": "0", "weight": "1", "enabled": "0",
                             "note": f"{_score(label, k['title']):.2f} {k['title']}"})
        try:
            cands = poly.search(re.sub(r"\[.*?\]", "", label).strip())
        except Exception as e:
            print(f"polymarket search failed for {label}: {e}")
            cands = []
        for c in sorted(cands, key=lambda c: -_score(label, c["title"]))[:args.per_source]:
            if _score(label, c["title"]) >= args.min_score:
                rows.append({"sig_exchange_id": eid, "label": label, "source": "polymarket", "ref": c["ref"],
                             "invert": "0", "weight": "1", "enabled": "0",
                             "note": f"{_score(label, c['title']):.2f} {c['title']}"})
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["sig_exchange_id", "label", "source", "ref", "invert", "weight",
                                          "enabled", "note"])
        w.writeheader()
        w.writerows(rows)
    print(f"wrote {len(rows)} suggestions to {out}. Review them, set enabled=1 on correct rows, "
          f"delete the 'note' column if you like, and save as {s.map_path}.")


def cmd_scan(s: Settings, args) -> None:
    bot = build(s, live=False)
    bot.refresh_refs()
    bot.compute_fairs()
    bot.prices = bot.api.prices(list(bot.map)) if bot.map else {}
    print(f"{'market':45} {'SIG bid/ask':>13} {'fair':>6} {'edge':>7}  note")
    for eid, (fair, why) in sorted(bot.fairs.items(), key=lambda kv: bot.labels[kv[0]]):
        bid, ask = bot.prices.get(eid, (None, None))
        ba = f"{bid if bid is not None else '-'}/{ask if ask is not None else '-'}"
        if fair is None:
            print(f"{bot.labels[eid][:45]:45} {ba:>13} {'-':>6} {'-':>7}  {why}")
            continue
        edges = [fair.p - ask if ask is not None else None, bid - fair.p if bid is not None else None]
        edge = max([e for e in edges if e is not None], default=0.0)
        flag = "  <-- TRADE" if edge >= s.min_edge else ""
        print(f"{bot.labels[eid][:45]:45} {ba:>13} {fair.p:6.3f} {edge:+7.3f}  {fair.detail}{flag}")


def cmd_run(s: Settings, args) -> None:
    live, why = decide_live(s, args.live)
    logging.getLogger(__name__).info("mode: %s", why)
    bot = build(s, live=live)
    bot.mode_note = why
    signal.signal(signal.SIGTERM, _stop)  # systemd/docker stop -> clean shutdown (cancels live orders)
    bot.run(minutes=args.minutes, report_file=args.report_file)


def _stop(signum, frame) -> None:
    raise KeyboardInterrupt


def cmd_report(s: Settings, args) -> None:
    bot = build(s, live=decide_live(s, s.live)[0])
    bot.refresh_refs()
    bot.compute_fairs()
    bot.prices = bot.api.prices(list(bot.map)) if bot.map else {}
    if args.send:
        bot.send_report()
    else:
        print(bot.report())


def review_text(s: Settings, hours: float, now: float | None = None) -> str:
    """Plain-text digest of what went wrong recently, read by the next scheduled run."""
    import time
    from collections import Counter
    now = now or time.time()
    since = now - hours * 3600
    out = [f"Review of the last {hours:g}h"]
    for live in (False, True):
        path = ledger_path(s, live)
        if not path.exists():
            continue
        led = Ledger(path)
        mode = "LIVE" if live else "PAPER"
        rows = led.db.execute("SELECT level, msg FROM events WHERE ts >= ?", (since,)).fetchall()
        errors = Counter(m[:160] for lvl, m in rows if lvl == "ERROR")
        alerts = [m for lvl, m in rows if lvl == "ALERT"]
        partial = [m for lvl, m in rows if lvl == "INFO" and "filled" in m and not _fully_filled(m)]
        fills = led.fills_since(since)
        losers = [f for f in fills if f[4] == "sell" and f[9] < 0]
        stuck = led.db.execute("SELECT strategy, label, action, qty FROM pending WHERE expires < ?",
                               (now - 120,)).fetchall()
        arb = {h.exchange_id: h.qty for h in led.holdings("arb")}
        out.append(f"\n[{mode}] {len(fills)} fills, {sum(1 for lvl, _ in rows if lvl == 'TRADE')} orders, "
                   f"{sum(errors.values())} errors, {len(alerts)} alerts, {len(partial)} partial/unfilled orders, "
                   f"{len(losers)} losing exits, {len(stuck)} stuck pending orders, "
                   f"paper_cycles={led.get('paper_cycles', '0')}")
        out += [f"  ERROR x{n}: {m}" for m, n in errors.most_common(10)]
        out += [f"  ALERT: {m[:160]}" for m in alerts[-10:]]
        out += [f"  PARTIAL: {m[:160]}" for m in partial[-10:]]
        out += [f"  LOSS: {f[2]} {f[3]} {f[4]} {f[5]:g} @{f[6]:.3f} ({f[8]}) {f[9]:+.0f}" for f in losers[-10:]]
        out += [f"  STUCK: {r}" for r in stuck]
        if arb:
            out.append(f"  arb legs held: {len(arb)}")
    return "\n".join(out)


def _fully_filled(note: str) -> bool:
    import re as _re
    m = _re.search(r"filled ([\d.]+)/(\d+)", note)
    return bool(m) and float(m.group(1)) >= float(m.group(2))


def cmd_review(s: Settings, args) -> None:
    print(review_text(s, args.hours))


def cmd_kill(s: Settings, args) -> None:
    Path(s.kill_switch).write_text("stop new entries\n")
    print(f"created {s.kill_switch}: the running bot stops opening trades (exits continue).")


def cmd_resume(s: Settings, args) -> None:
    Path(s.kill_switch).unlink(missing_ok=True)
    print(f"removed {s.kill_switch}: entries allowed again.")


def main(argv: list[str] | None = None) -> None:
    p = argparse.ArgumentParser(prog="sigcup", description=__doc__)
    p.add_argument("--env", default=".env", help="path to the .env file")
    p.add_argument("-v", "--verbose", action="store_true")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("check", help="verify API key, list tournaments and notification channels")
    m = sub.add_parser("markets", help="dump all SIG exchanges to CSV")
    m.add_argument("--out", default="data/sig_markets.csv")
    sm = sub.add_parser("suggest-map", help="fuzzy-match SIG markets to Kalshi/Polymarket (for review)")
    sm.add_argument("--out", default="data/suggested_map.csv")
    sm.add_argument("--per-source", type=int, default=2)
    sm.add_argument("--min-score", type=float, default=0.25)
    sub.add_parser("scan", help="print SIG vs reference prices once; never trades")
    r = sub.add_parser("run", help="run the bot (paper unless --live and MODE=live)")
    r.add_argument("--live", action="store_true")
    r.add_argument("--minutes", type=float, default=0, help="stop after this long (0 = run forever)")
    r.add_argument("--report-file", default="", help="write the final report here on exit")
    rep = sub.add_parser("report", help="print (or --send) the status report now")
    rep.add_argument("--send", action="store_true")
    rv = sub.add_parser("review", help="digest of recent errors, partial fills, losses (no API calls)")
    rv.add_argument("--hours", type=float, default=3)
    sub.add_parser("kill", help="pause new entries (creates the kill-switch file)")
    sub.add_parser("resume", help="remove the kill-switch file")
    args = p.parse_args(argv)
    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO,
                        format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    logging.getLogger("httpx").setLevel(logging.WARNING)
    s = Settings.from_env(args.env)
    globals()[f"cmd_{args.cmd.replace('-', '_')}"](s, args)


if __name__ == "__main__":
    main()
