from cartography.intel.sentinelone.utils import get_application_id
from tests.data.sentinelone.utils import APPLICATION_ID_EDGE_CASES
from tests.data.sentinelone.utils import APPLICATION_ID_TEST_CASES


def test_get_application_id_standard_cases():
    """
    Test get_application_id with standard application and vendor names
    """
    for case in APPLICATION_ID_TEST_CASES:
        result = get_application_id(case["name"], case["vendor"])
        assert (
            result == case["expected"]
        ), f"Failed for {case['name']} by {case['vendor']}"


def test_get_application_id_edge_cases():
    """
    Test get_application_id with edge cases like special characters, spaces, and mixed case
    """
    for case in APPLICATION_ID_EDGE_CASES:
        result = get_application_id(case["name"], case["vendor"])
        assert (
            result == case["expected"]
        ), f"Failed for {case['name']} by {case['vendor']}"


def test_get_application_id_underscore_preservation():
    """
    Test that get_application_id preserves underscores after processing
    """
    result = get_application_id("App_Name_Test", "Vendor_Name_Test")
    assert result == "vendor_name_test:app_name_test"


def test_get_application_id_single_character():
    """
    Test that get_application_id handles single character inputs
    """
    result = get_application_id("A", "B")
    assert result == "b:a"


def test_get_application_id_consistent_results():
    """
    Test that get_application_id produces consistent results for the same input
    """
    name = "Microsoft Office"
    vendor = "Microsoft"

    result1 = get_application_id(name, vendor)
    result2 = get_application_id(name, vendor)
    result3 = get_application_id(name, vendor)

    assert result1 == result2 == result3


def test_get_application_id_return_type():
    """
    Test that get_application_id always returns a string
    """
    result = get_application_id("Test App", "Test Vendor")
    assert isinstance(result, str)

    # Test with empty inputs
    result = get_application_id("", "")
    assert isinstance(result, str)


def test_get_application_id_format():
    """
    Test that get_application_id always returns the correct format: vendor:name
    """
    result = get_application_id("Test App", "Test Vendor")
    assert ":" in result
    assert result.count(":") == 1

    parts = result.split(":")
    assert len(parts) == 2
    assert parts[0] == "test_vendor"
    assert parts[1] == "test_app"
