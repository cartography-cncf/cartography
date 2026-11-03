import pytest

from cartography.intel.microsoft.util import (
    parse_and_validate_microsoft_requested_syncs,
)


def test_parse_requested_syncs_accepts_valid_resources() -> None:
    assert parse_and_validate_microsoft_requested_syncs("users, groups,intune") == [
        "users",
        "groups",
        "intune",
    ]


def test_parse_requested_syncs_rejects_unknown_resource() -> None:
    with pytest.raises(ValueError, match="microsoft-requested-syncs"):
        parse_and_validate_microsoft_requested_syncs("users,devices")
