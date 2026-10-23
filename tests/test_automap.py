from sigcup.automap import build_rows, race_series


def test_race_series():
    assert race_series("Texas Senate") == ["SENATETX", "SENATETXS"]
    assert race_series("Texas Governor") == ["GOVPARTYTX"]
    assert race_series("PA-07 House race") == ["HOUSEPA7", "KXHOUSEPA7"]
    assert race_series("U.S. House") == ["CONTROLH"]
    assert race_series("Narnia Senate") is None


def test_build_rows_exact_ambiguous_and_sanity():
    events = {
        "SENATETX": [{"event_ticker": "SENATETX-26", "markets": [
            {"ticker": "SENATETX-26-D", "yes_bid_dollars": "0.65", "yes_ask_dollars": "0.66"},
            {"ticker": "SENATETX-26-R", "yes_bid_dollars": "0.33", "yes_ask_dollars": "0.34"}]},
            {"event_ticker": "SENATETX-24", "markets": [{"ticker": "SENATETX-24-D"}]}],
        "SENATEOH": [{"event_ticker": "SENATEOH-26", "markets": [{"ticker": "SENATEOH-26-D"}]}],
        "SENATEOHS": [{"event_ticker": "SENATEOHS-26", "markets": [{"ticker": "SENATEOHS-26-D"}]}],
    }
    sig = [("a", "Will the Democratic Party win the Texas Senate?"),
           ("b", "Will the Republican Party win the Texas Senate?"),
           ("c", "Will the Democratic Party win the Ohio Senate?"),
           ("d", "Will the Independent Party win the Texas Senate?")]
    prices = {"a": (0.64, 0.66), "b": (0.80, 0.82)}  # b's Cup price is nowhere near Kalshi's
    rows, notes = build_rows(sig, lambda s: events.get(s, []), prices)
    assert [(r["sig_exchange_id"], r["ref"]) for r in rows] == [("a", "SENATETX-26-D")]
    assert any("too far apart" in n for n in notes)
    assert any("ambiguous" in n and "Ohio" in n for n in notes)
    assert any("no Kalshi market" in n and "Independent" in n for n in notes)
