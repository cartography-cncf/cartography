from unittest.mock import Mock

from cartography.intel.opsgenie.resources import get_users


def test_get_users_paginates_until_total_count():
    # Arrange
    session = Mock()
    first_response = Mock()
    first_response.json.return_value = {"data": [{"id": "user-1"}], "totalCount": 2}
    second_response = Mock()
    second_response.json.return_value = {"data": [{"id": "user-2"}], "totalCount": 2}
    session.get.side_effect = [first_response, second_response]

    # Act
    users = get_users(session, "https://api.opsgenie.com", 60)

    # Assert
    assert users == [{"id": "user-1"}, {"id": "user-2"}]
    assert session.get.call_args_list[1].kwargs["params"] == {"limit": 100, "offset": 1}
