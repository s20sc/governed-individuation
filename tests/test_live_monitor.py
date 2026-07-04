import tempfile
from toolgym.live_monitor import demo_runtime_indirection

def test_live_tracer_catches_runtime_indirection():
    # the exact bypass the STATIC monitor misses (named target benign, real open forbidden)
    with tempfile.TemporaryDirectory() as root:
        res = demo_runtime_indirection(root)
    assert res["refused_by_live_monitor"] is True
    assert any("eval/answer.json" in p for p in res["forbidden_effects_observed"])
    assert not res["crashed"]
