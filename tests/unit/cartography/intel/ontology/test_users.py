from copy import deepcopy

from cartography.intel.ontology.users import transform_users


def test_transform_users_preserves_primary_email_and_source_data():
    # Arrange
    data = [
        {"email": " Alice@Example.com ", "fullname": "Alice Example"},
        {"email": "alice@example.com"},
        {"email": None},
        {"email": " "},
        {},
    ]
    original = deepcopy(data)

    # Act
    result = transform_users(data)

    # Assert
    assert [user["normalized_email"] for user in result] == [
        "alice@example.com",
        "alice@example.com",
        None,
        None,
        None,
    ]
    assert result[0]["email"] == " Alice@Example.com "
    assert result[0]["fullname"] == "Alice Example"
    assert data == original
