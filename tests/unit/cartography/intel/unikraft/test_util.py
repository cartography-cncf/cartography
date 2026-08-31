import pytest

from cartography.intel.unikraft.util import check_count_matches
from cartography.intel.unikraft.util import require_tracked_count


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


def test_require_tracked_count_returns_the_count_when_present():
    assert require_tracked_count({"instances": 4, "volumes": 0}, "instances") == 4


def test_require_tracked_count_returns_zero_when_present_and_zero():
    assert require_tracked_count({"instances": 0}, "instances") == 0


def test_require_tracked_count_raises_when_key_is_missing():
    """
    A missing count for a resource type quotas is known to track (unlike
    certificates, which quotas genuinely never reports) means the quota response
    itself is malformed - failing closed here is safer than silently disabling
    check_count_matches()'s truncation guard for it.
    """
    with pytest.raises(ValueError, match="instances"):
        require_tracked_count({"volumes": 0}, "instances")
