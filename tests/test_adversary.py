import tempfile
from toolgym.adversary import evaluate

def test_monitor_strength_ladder():
    with tempfile.TemporaryDirectory() as root:
        out = evaluate(root)
    far = out["false_allow_rate"]
    # rising monitor strength: name > substring > realpath
    assert far["name_gate"] > far["substring_gate"] > far["realpath_gate"]
    # realpath catches every STATIC bypass; only runtime indirection slips through
    rows = {r["bypass"]: r for r in out["rows"]}
    assert not rows["symlink_clean"]["realpath_allows"]      # caught by resolution
    assert rows["runtime_indirection"]["realpath_allows"]    # honest residual delta_A
    assert rows["symlink_clean"]["substring_allows"]         # substring fooled by clean alias
