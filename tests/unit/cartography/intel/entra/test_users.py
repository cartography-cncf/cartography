from unittest.mock import MagicMock

from cartography.intel.entra.users import transform_users


def test_transform_users_with_assigned_plans():
    # Arrange
    mock_user = MagicMock()
    mock_user.id = "test-user-id"
    mock_user.user_principal_name = "test@example.com"
    mock_user.display_name = "Test User"
    mock_user.given_name = "Test"
    mock_user.surname = "User"
    mock_user.mail = "test@example.com"
    mock_user.mobile_phone = None
    mock_user.business_phones = []
    mock_user.job_title = None
    mock_user.department = None
    mock_user.office_location = None
    mock_user.city = None
    mock_user.state = None
    mock_user.country = None
    mock_user.company_name = None
    mock_user.preferred_language = None
    mock_user.employee_id = None
    mock_user.employee_type = None
    mock_user.account_enabled = True
    mock_user.age_group = None
    mock_user.manager = None

    # Mock assigned plans
    mock_plan1 = MagicMock()
    mock_plan1.service_plan_id = "plan-id-1"
    mock_plan1.service = "Exchange"
    mock_plan1.capability_status = "Enabled"

    mock_plan2 = MagicMock()
    mock_plan2.service_plan_id = "plan-id-2"
    mock_plan2.service = "SharePoint"
    mock_plan2.capability_status = "Suspended"

    mock_user.assigned_plans = [mock_plan1, mock_plan2]

    users = [mock_user]

    # Act
    result = list(transform_users(users))

    # Assert
    assert len(result) == 1
    transformed_user = result[0]
    assert transformed_user["id"] == "test-user-id"
    assert "assigned_plans" in transformed_user
    assert len(transformed_user["assigned_plans"]) == 2

    assert transformed_user["assigned_plans"][0]["service_plan_id"] == "plan-id-1"
    assert transformed_user["assigned_plans"][0]["service"] == "Exchange"
    assert transformed_user["assigned_plans"][0]["capability_status"] == "Enabled"

    assert transformed_user["assigned_plans"][1]["service_plan_id"] == "plan-id-2"
    assert transformed_user["assigned_plans"][1]["service"] == "SharePoint"
    assert transformed_user["assigned_plans"][1]["capability_status"] == "Suspended"


def test_transform_users_with_no_assigned_plans():
    # Arrange
    mock_user = MagicMock()
    mock_user.id = "test-user-id"
    mock_user.assigned_plans = None

    # Fill required fields with dummies
    mock_user.user_principal_name = None
    mock_user.display_name = None
    mock_user.given_name = None
    mock_user.surname = None
    mock_user.mail = None
    mock_user.mobile_phone = None
    mock_user.business_phones = []
    mock_user.job_title = None
    mock_user.department = None
    mock_user.office_location = None
    mock_user.city = None
    mock_user.state = None
    mock_user.country = None
    mock_user.company_name = None
    mock_user.preferred_language = None
    mock_user.employee_id = None
    mock_user.employee_type = None
    mock_user.account_enabled = None
    mock_user.age_group = None
    mock_user.manager = None

    users = [mock_user]

    # Act
    result = list(transform_users(users))

    # Assert
    assert len(result) == 1
    assert result[0]["assigned_plans"] == []
