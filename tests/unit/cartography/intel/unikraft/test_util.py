import pytest

from cartography.intel.unikraft.util import check_count_matches


def test_check_count_matches_raises_when_counts_differ():
    with pytest.raises(ValueError, match="instances"):
        check_count_matches("instances", expected=5, actual=2)


def test_check_count_matches_is_silent_when_counts_match():
    check_count_matches("instances", expected=3, actual=3)


def test_check_count_matches_is_silent_when_expected_is_none():
    """
    A resource type not tracked by the account quota endpoint (e.g. certificates)
    has no expected count to compare against, so this must not raise.
    """
    check_count_matches("certificates", expected=None, actual=7)
