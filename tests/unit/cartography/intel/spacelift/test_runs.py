from cartography.intel.spacelift.runs import extract_users_from_runs
from cartography.models.spacelift.user import SpaceliftUserNodeProperties


def test_extract_users_from_runs_marks_email_triggers_as_human():
    # Arrange
    runs_data = [{"id": "run-1", "triggeredBy": "alice@example.com"}]

    # Act
    users = extract_users_from_runs(runs_data)

    # Assert
    assert users == [
        {
            "id": "alice@example.com",
            "username": "alice@example.com",
            "email": "alice@example.com",
            "name": "alice",
            "user_type": "human",
        }
    ]


def test_extract_users_from_runs_marks_non_email_triggers_as_system():
    # Arrange
    runs_data = [{"id": "run-1", "triggeredBy": "vcs/commit"}]

    # Act
    users = extract_users_from_runs(runs_data)

    # Assert
    assert users == [
        {
            "id": "vcs/commit",
            "username": "vcs/commit",
            "email": None,
            "name": "vcs/commit",
            "user_type": "system",
        }
    ]


def test_user_type_schema_description_matches_writer():
    # Arrange
    description = SpaceliftUserNodeProperties().user_type.description or ""

    # Act
    # (nothing to do: we are asserting on the declared schema documentation)

    # Assert
    # The writer only ever emits `human` or `system`, so the generated schema docs
    # must not advertise any other value.
    assert "human" in description
    assert "system" in description
    assert "machine" not in description
