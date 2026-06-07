import pytest

from cartography.intel.jamf.computers import transform


def test_transform_requires_computer_id() -> None:
    with pytest.raises(KeyError, match="id"):
        transform([{"general": {"name": "Springfield-MacBook"}}])
