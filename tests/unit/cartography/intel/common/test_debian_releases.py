import pytest

from cartography.intel.common.debian_releases import major_release
from cartography.intel.common.debian_releases import release_version


@pytest.mark.parametrize(
    ("codename", "expected"),
    [
        ("bookworm", "12"),
        ("trixie", "13"),
        ("forky", "14"),
        ("sid", None),
        ("experimental", None),
    ],
)
def test_release_version(codename, expected):
    # Act and assert
    assert release_version(codename) == expected


@pytest.mark.parametrize(
    ("debian_version", "expected"),
    [
        ("12.7", "12"),
        ("12", "12"),
        ("13.6", "13"),
        ("9.13", "9"),
        (" 12.13\n", "12"),
        ("trixie/sid", "13"),
        ("forky/sid", "14"),
        ("bookworm", "12"),
        ("sid", None),
        ("unknown/sid", None),
        ("", None),
        (None, None),
    ],
)
def test_major_release(debian_version, expected):
    # Act and assert
    assert major_release(debian_version) == expected
