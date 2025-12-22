from unittest.mock import MagicMock
from unittest.mock import patch

from cartography.intel.workday.people import _transform_people_data
from cartography.intel.workday.people import get_workday_directory


def test_transform_people_data_basic():
    """Test basic transformation of Workday people data"""
    # Arrange
    directory_data = {
        "Report_Entry": [
            {
                "Employee_ID": "emp001",
                "Name": "Alice Johnson",
                "businessTitle": "Engineer",
                "Worker_Type": "Employee",
                "location": "SF",
                "Email_-_Work": "alice@example.com",
                "Location_Address_-_Country": "USA",
                "Cost_Center": "Eng",
                "GBL-Custom-Function": "Product",
                "Sub-Function": "Backend",
                "Team": "Core",
                "Sub_Team": "API",
                "Company": "Example",
                "Supervisory_Organization": "Engineering Dept",
                "Worker_s_Manager_group": [{"Manager_ID": "emp002"}],
            },
        ],
    }

    # Act
    people_data, manager_relationships = _transform_people_data(directory_data)

    # Assert
    assert len(people_data) == 1
    person = people_data[0]

    # Check original fields preserved
    assert person["Employee_ID"] == "emp001"
    assert person["Name"] == "Alice Johnson"
    assert person["businessTitle"] == "Engineer"

    # Check transformed fields
    assert person["email"] == "alice@example.com"
    assert person["country"] == "USA"
    assert person["cost_center"] == "Eng"
    assert person["function"] == "Product"
    assert person["sub_function"] == "Backend"
    assert person["source"] == "WORKDAY"
    assert person["Manager_ID"] == "emp002"

    # Check manager relationships
    assert len(manager_relationships) == 1
    assert manager_relationships[0]["Employee_ID"] == "emp001"
    assert manager_relationships[0]["Manager_ID"] == "emp002"


def test_transform_people_data_prevents_self_reporting():
    """Test that self-reporting relationships are filtered out"""
    # Arrange
    directory_data = {
        "Report_Entry": [
            {
                "Employee_ID": "emp001",
                "Name": "Alice",
                "Email_-_Work": "alice@example.com",
                "Supervisory_Organization": "Eng",
                "Worker_s_Manager_group": [{"Manager_ID": "emp001"}],  # Self-reference!
            },
        ],
    }

    # Act
    people_data, manager_relationships = _transform_people_data(directory_data)

    # Assert
    assert len(people_data) == 1
    # Self-reporting relationship should be filtered out
    assert len(manager_relationships) == 0


def test_transform_people_data_handles_no_manager():
    """Test handling of employees without managers"""
    # Arrange
    directory_data = {
        "Report_Entry": [
            {
                "Employee_ID": "ceo001",
                "Name": "CEO Person",
                "Email_-_Work": "ceo@example.com",
                "Supervisory_Organization": "Executive",
                "Worker_s_Manager_group": [],  # No manager
            },
        ],
    }

    # Act
    people_data, manager_relationships = _transform_people_data(directory_data)

    # Assert
    assert len(people_data) == 1
    assert people_data[0]["Manager_ID"] is None
    assert len(manager_relationships) == 0


def test_transform_people_data_handles_empty_report():
    """Test handling of empty employee list"""
    # Arrange
    directory_data = {"Report_Entry": []}

    # Act
    people_data, manager_relationships = _transform_people_data(directory_data)

    # Assert
    assert people_data == []
    assert manager_relationships == []


def test_transform_people_data_handles_missing_optional_fields():
    """Test that missing optional fields don't break transformation"""
    # Arrange
    directory_data = {
        "Report_Entry": [
            {
                "Employee_ID": "emp001",
                "Name": "Minimal Person",
                "Email_-_Work": "minimal@example.com",
                "Supervisory_Organization": "Dept",
                # All other fields missing
            },
        ],
    }

    # Act
    people_data, manager_relationships = _transform_people_data(directory_data)

    # Assert
    assert len(people_data) == 1
    person = people_data[0]

    # Required fields should be present
    assert person["Employee_ID"] == "emp001"
    assert person["Name"] == "Minimal Person"
    assert person["email"] == "minimal@example.com"
    assert person["source"] == "WORKDAY"

    # Optional fields should be None
    assert person.get("cost_center") is None
    assert person.get("function") is None
    assert person["Manager_ID"] is None


def test_transform_people_data_multiple_employees_same_manager():
    """Test that multiple employees can report to the same manager"""
    # Arrange
    directory_data = {
        "Report_Entry": [
            {
                "Employee_ID": "emp001",
                "Name": "Alice",
                "Email_-_Work": "alice@example.com",
                "Supervisory_Organization": "Eng",
                "Worker_s_Manager_group": [{"Manager_ID": "mgr001"}],
            },
            {
                "Employee_ID": "emp002",
                "Name": "Bob",
                "Email_-_Work": "bob@example.com",
                "Supervisory_Organization": "Eng",
                "Worker_s_Manager_group": [{"Manager_ID": "mgr001"}],  # Same manager
            },
            {
                "Employee_ID": "mgr001",
                "Name": "Manager",
                "Email_-_Work": "mgr@example.com",
                "Supervisory_Organization": "Eng",
                "Worker_s_Manager_group": [],
            },
        ],
    }

    # Act
    people_data, manager_relationships = _transform_people_data(directory_data)

    # Assert
    assert len(people_data) == 3
    assert len(manager_relationships) == 2  # Two employees reporting to mgr001

    # Both should reference the same manager
    assert all(rel["Manager_ID"] == "mgr001" for rel in manager_relationships)


def test_transform_people_data_preserves_workday_field_names():
    """Test that original Workday field names are preserved for other fields"""
    # Arrange
    directory_data = {
        "Report_Entry": [
            {
                "Employee_ID": "emp001",
                "Name": "Alice",
                "businessTitle": "Engineer",
                "Worker_Type": "Employee",
                "location": "SF Office",
                "Team": "Core Platform",
                "Sub_Team": "API",
                "Company": "Example Corp",
                "Email_-_Work": "alice@example.com",
                "Location_Address_-_Country": "USA",
                "Cost_Center": "ENG-100",
                "GBL-Custom-Function": "Product Development",
                "Sub-Function": "Backend",
                "Supervisory_Organization": "Engineering",
                "Worker_s_Manager_group": [],
            },
        ],
    }

    # Act
    people_data, _ = _transform_people_data(directory_data)

    # Assert
    person = people_data[0]

    # Original Workday field names should be preserved
    assert person["businessTitle"] == "Engineer"
    assert person["Worker_Type"] == "Employee"
    assert person["Team"] == "Core Platform"
    assert person["Sub_Team"] == "API"
    assert person["Company"] == "Example Corp"
    assert person["Supervisory_Organization"] == "Engineering"

    # Mapped fields should exist with clean names
    assert person["email"] == "alice@example.com"
    assert person["country"] == "USA"
    assert person["cost_center"] == "ENG-100"
    assert person["function"] == "Product Development"
    assert person["sub_function"] == "Backend"


def test_transform_people_data_handles_multiple_manager_entries():
    """Test handling of Worker_s_Manager_group with multiple entries (take first)"""
    # Arrange
    directory_data = {
        "Report_Entry": [
            {
                "Employee_ID": "emp001",
                "Name": "Alice",
                "Email_-_Work": "alice@example.com",
                "Supervisory_Organization": "Eng",
                "Worker_s_Manager_group": [
                    {"Manager_ID": "mgr001"},  # Should use this
                    {"Manager_ID": "mgr002"},  # Ignore additional entries
                ],
            },
        ],
    }

    # Act
    people_data, manager_relationships = _transform_people_data(directory_data)

    # Assert
    assert people_data[0]["Manager_ID"] == "mgr001"
    assert len(manager_relationships) == 1
    assert manager_relationships[0]["Manager_ID"] == "mgr001"


@patch("requests.get")
def test_get_workday_directory_success(mock_get):
    """Test successful API call to Workday"""
    # Arrange
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "Report_Entry": [
            {
                "Employee_ID": "emp001",
                "Name": "Alice",
                "Email_-_Work": "alice@example.com",
            },
        ],
    }
    mock_get.return_value = mock_response

    # Act
    result = get_workday_directory(
        "https://workday.example.com/api",
        "test_user",
        "test_password",
    )

    # Assert
    assert result == {
        "Report_Entry": [
            {
                "Employee_ID": "emp001",
                "Name": "Alice",
                "Email_-_Work": "alice@example.com",
            }
        ]
    }
    # Verify HTTP Basic Auth was used
    call_kwargs = mock_get.call_args[1]
    assert call_kwargs["auth"].username == "test_user"
    assert call_kwargs["auth"].password == "test_password"
    assert call_kwargs["timeout"] == (60, 60)


@patch("requests.get")
def test_get_workday_directory_handles_http_error(mock_get):
    """Test that HTTP errors are properly raised"""
    # Arrange
    mock_response = MagicMock()
    mock_response.status_code = 401
    mock_response.content = b"Unauthorized"
    mock_get.return_value = mock_response

    # Act & Assert
    try:
        get_workday_directory("https://workday.example.com/api", "user", "pass")
        assert False, "Should have raised Exception"
    except Exception as e:
        assert "Workday API returned HTTP 401" in str(e)
        assert "credentials" in str(e).lower()


@patch("requests.get")
def test_get_workday_directory_handles_json_parse_error(mock_get):
    """Test that JSON parsing errors are properly handled"""
    # Arrange
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.side_effect = ValueError("Invalid JSON")
    mock_get.return_value = mock_response

    # Act & Assert
    try:
        get_workday_directory("https://workday.example.com/api", "user", "pass")
        assert False, "Should have raised Exception"
    except Exception as e:
        assert "Unable to parse Workday API response as JSON" in str(e)


@patch("requests.get")
def test_get_workday_directory_handles_empty_response(mock_get):
    """Test that empty JSON response is caught"""
    # Arrange
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {}  # Empty dict
    mock_response.content = b"{}"
    mock_get.return_value = mock_response

    # Act & Assert
    try:
        get_workday_directory("https://workday.example.com/api", "user", "pass")
        assert False, "Should have raised Exception"
    except Exception as e:
        assert "Workday API returned empty response" in str(e)
