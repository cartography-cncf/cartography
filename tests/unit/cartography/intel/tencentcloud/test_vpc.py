import pytest

from cartography.intel.tencentcloud.vpc import parse_port_range


@pytest.mark.parametrize(
    ("port", "expected"),
    [
        ("all", (0, 65535)),
        ("ALL", (0, 65535)),
        ("22", (22, 22)),
        ("8000-8010", (8000, 8010)),
        ("80,443", (None, None)),
        (None, (None, None)),
    ],
)
def test_parse_port_range(port, expected):
    # Act and assert
    assert parse_port_range(port) == expected
