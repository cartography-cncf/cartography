import re

import pytest

from cartography.intel.sentinelone.utils import get_application_id
from tests.data.sentinelone.utils import APPLICATION_ID_EDGE_CASES
from tests.data.sentinelone.utils import APPLICATION_ID_TEST_CASES


def _case_id(prefix: str, name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")
    return f"{prefix}-{slug or 'empty'}"


@pytest.mark.parametrize(
    ("name", "vendor", "expected"),
    [
        # Standard application and vendor names.
        *(
            pytest.param(
                case["name"],
                case["vendor"],
                case["expected"],
                id=_case_id("standard", case["name"]),
            )
            for case in APPLICATION_ID_TEST_CASES
        ),
        # Edge cases like special characters, spaces, mixed case and empty input.
        *(
            pytest.param(
                case["name"],
                case["vendor"],
                case["expected"],
                id=_case_id("edge", case["name"]),
            )
            for case in APPLICATION_ID_EDGE_CASES
        ),
        # Underscores are preserved after processing.
        pytest.param(
            "App_Name_Test",
            "Vendor_Name_Test",
            "vendor_name_test:app_name_test",
            id="underscore_preservation",
        ),
        # Single character inputs.
        pytest.param("A", "B", "b:a", id="single_character"),
        # The result has the vendor:name format.
        pytest.param("Test App", "Test Vendor", "test_vendor:test_app", id="format"),
    ],
)
def test_get_application_id(name, vendor, expected):
    # Act
    result = get_application_id(name, vendor)

    # Assert
    assert result == expected
