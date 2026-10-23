from sigcup.sig_api import SigApi


def test_positions_tolerates_null_body():
    api = SigApi.__new__(SigApi)
    api.slug = "t"
    api.get = lambda path, **kw: None
    assert api.positions() == []
