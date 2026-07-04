import tempfile
from toolgym.verifier_eval import evaluate

def test_verifier_ladder_and_dynamic_closes_delta_a():
    with tempfile.TemporaryDirectory() as root:
        out = evaluate(root)
    far = out["false_allow_rate"]
    # monotone rising monitor strength
    assert far["name"] > far["substring"] > far["realpath_static"] > far["realpath_dynamic"]
    # dynamic tracing closes the residual to exactly zero
    assert far["realpath_dynamic"] == 0.0
    # holds uniformly across all four effect classes
    for cls, m in out["per_class_false_allow"].items():
        assert m["realpath_dynamic"] == 0.0 and m["name"] >= m["realpath_static"]
    assert out["n_forbidden_reaching"] == 32
