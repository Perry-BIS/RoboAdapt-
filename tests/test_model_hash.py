from pathlib import Path

from roboadapt.env import canonical_asset_bytes, canonical_asset_digest, canonical_asset_hash


def test_model_hash_is_newline_independent():
    lf = b"<mujoco>\n  <worldbody/>\n</mujoco>\n"
    crlf = lf.replace(b"\n", b"\r\n")
    assert canonical_asset_bytes(crlf) == lf
    assert canonical_asset_digest(lf) == canonical_asset_digest(crlf)


def test_checked_in_scene_has_historical_normalized_hash():
    scene = Path(__file__).parents[1] / "roboadapt" / "assets" / "scene.xml"
    assert canonical_asset_hash(scene) == "498e7b75553ad823"
