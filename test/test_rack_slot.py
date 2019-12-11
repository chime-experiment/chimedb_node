import pytest


@pytest.mark.parametrize(
    "value,out",
    [
        (None, None),
        ("CN0g0", "cn0g0"),
        ("Cn1g1", "cn1g1"),
        ("CN2g2", "cn2g2"),
        ("cn3g3", "cn3g3"),
        ("cS4g4", "cs4g4"),
        ("Cs5g5", "cs5g5"),
        ("CS6g6", "cs6g6"),
        ("cs7g7", "cs7g7"),
        ("cN8g8", "cn8g8"),
        ("Cn9g9", "cn9g9"),
        ("cNag1", "cnAg1"),
        ("csBg1", "csBg1"),
        ("CScg1", "csCg1"),
        ("csDg1", "csDg1"),
        ("cSeg1", "csEg1"),
        ("Cfan1", "cfAn1"),
        ("nag1", "cnAg1"),
        ("f3n1", "cf3n1"),
    ],
)
def test_valid_name(value, out):
    from chimedb.node.util import valid_rack_slot

    assert valid_rack_slot(value) == out


@pytest.mark.parametrize(
    "value", ["", "cn0g0a", "cn0n0", "cf0g0", "cf0na", "cs0n0", "nfg2", "sfg33"]
)
def test_invalid_name(value):
    from chimedb.node.util import valid_rack_slot

    with pytest.raises(ValueError):
        valid_rack_slot(value)
