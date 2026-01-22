from unittest.mock import patch

from cartography.intel.workday.people import _load_manager_relationships
from cartography.intel.workday.people import _load_organizations
from cartography.intel.workday.people import _load_people
from cartography.intel.workday.people import _transform_people_data
from cartography.intel.workday.people import sync_workday_people
from tests.data.workday.people import GET_WORKDAY_DIRECTORY_RESPONSE
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
TEST_WORKDAY_API_URL = "https://example.workday.com/api"
TEST_WORKDAY_LOGIN = "test_user"
TEST_WORKDAY_PASSWORD = "test_password"


def _ensure_local_neo4j_has_test_data(neo4j_session):
    """Helper to load test data into Neo4j"""
    people_data, manager_relationships = _transform_people_data(
        GET_WORKDAY_DIRECTORY_RESPONSE
    )
    _load_organizations(neo4j_session, people_data, TEST_UPDATE_TAG)
    _load_people(neo4j_session, people_data, TEST_UPDATE_TAG)
    _load_manager_relationships(neo4j_session, manager_relationships, TEST_UPDATE_TAG)


def test_transform_people_data():
    """Test that people data is transformed correctly"""
    people_data, manager_relationships = _transform_people_data(
        GET_WORKDAY_DIRECTORY_RESPONSE
    )

    # Check that we have 4 people
    assert len(people_data) == 4

    # Check that all people have source field
    for person in people_data:
        assert person["source"] == "WORKDAY"

    # Check manager relationships
    # emp001 -> emp003, emp002 -> emp003, emp003 -> emp004
    assert len(manager_relationships) == 3
    assert {"Employee_ID": "emp001", "Manager_ID": "emp003"} in manager_relationships
    assert {"Employee_ID": "emp002", "Manager_ID": "emp003"} in manager_relationships
    assert {"Employee_ID": "emp003", "Manager_ID": "emp004"} in manager_relationships


def test_load_workday_people(neo4j_session):
    """Test that Workday people are loaded correctly into Neo4j"""
    # Arrange & Act
    _ensure_local_neo4j_has_test_data(neo4j_session)

    # Assert - Check that people nodes exist
    assert check_nodes(
        neo4j_session,
        "WorkdayHuman",
        ["id", "employee_id", "name", "email"],
    ) == {
        ("emp001", "emp001", "Alice Johnson", "alice.johnson@example.com"),
        ("emp002", "emp002", "Bob Smith", "bob.smith@example.com"),
        ("emp003", "emp003", "Carol Williams", "carol.williams@example.com"),
        ("emp004", "emp004", "David Brown", "david.brown@example.com"),
    }

    # Check that all humans have the Human label
    result = neo4j_session.run(
        "MATCH (h:WorkdayHuman:Human) RETURN count(h) as count",
    )
    record = result.single()
    assert record["count"] == 4


def test_load_workday_organizations(neo4j_session):
    """Test that Workday organizations are loaded correctly into Neo4j"""
    # Arrange & Act
    _ensure_local_neo4j_has_test_data(neo4j_session)

    # Assert - Check that organization nodes exist
    assert check_nodes(
        neo4j_session,
        "WorkdayOrganization",
        ["id", "name"],
    ) == {
        ("Engineering Department", "Engineering Department"),
        ("Executive Department", "Executive Department"),
    }


def test_load_organization_relationships(neo4j_session):
    """Test that MEMBER_OF_ORGANIZATION relationships are created correctly"""
    # Arrange & Act
    _ensure_local_neo4j_has_test_data(neo4j_session)

    # Assert - Check MEMBER_OF_ORGANIZATION relationships
    assert check_rels(
        neo4j_session,
        "WorkdayHuman",
        "id",
        "WorkdayOrganization",
        "id",
        "MEMBER_OF_ORGANIZATION",
        rel_direction_right=True,
    ) == {
        ("emp001", "Engineering Department"),
        ("emp002", "Engineering Department"),
        ("emp003", "Engineering Department"),
        ("emp004", "Executive Department"),
    }


def test_load_manager_relationships(neo4j_session):
    """Test that REPORTS_TO (manager) relationships are created correctly"""
    # Arrange & Act
    _ensure_local_neo4j_has_test_data(neo4j_session)

    # Assert - Check REPORTS_TO relationships
    assert check_rels(
        neo4j_session,
        "WorkdayHuman",
        "id",
        "WorkdayHuman",
        "id",
        "REPORTS_TO",
        rel_direction_right=True,
    ) == {
        ("emp001", "emp003"),  # Alice reports to Carol
        ("emp002", "emp003"),  # Bob reports to Carol
        ("emp003", "emp004"),  # Carol reports to David
    }


@patch("cartography.intel.workday.people.get_workday_directory")
def test_sync_workday_people(mock_get_workday_directory, neo4j_session):
    """Test the full sync_workday_people function"""
    # Arrange
    mock_get_workday_directory.return_value = GET_WORKDAY_DIRECTORY_RESPONSE

    # Act
    sync_workday_people(
        neo4j_session,
        TEST_WORKDAY_API_URL,
        TEST_WORKDAY_LOGIN,
        TEST_WORKDAY_PASSWORD,
        TEST_UPDATE_TAG,
    )

    # Assert - Verify the mock was called correctly
    mock_get_workday_directory.assert_called_once_with(
        TEST_WORKDAY_API_URL,
        TEST_WORKDAY_LOGIN,
        TEST_WORKDAY_PASSWORD,
    )

    # Verify data was loaded correctly
    assert check_nodes(
        neo4j_session,
        "WorkdayHuman",
        ["id", "name"],
    ) == {
        ("emp001", "Alice Johnson"),
        ("emp002", "Bob Smith"),
        ("emp003", "Carol Williams"),
        ("emp004", "David Brown"),
    }
