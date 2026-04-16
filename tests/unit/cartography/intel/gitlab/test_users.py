from cartography.intel.gitlab.users import transform_commit_activity


def test_transform_commit_activity_falls_back_to_author_name():
    commits_by_project = {
        123: [
            {
                "author_name": "Alice Smith",
                "author_email": None,
                "committed_date": "2024-12-01T10:00:00Z",
            },
        ],
    }
    users_by_email = {}
    users_by_name = {"Alice Smith": 1}
    user_records = [
        {
            "id": 1,
            "username": "alice",
            "name": "Alice Smith",
            "web_url": "https://gitlab.example.com/alice",
            "gitlab_url": "https://gitlab.example.com",
        },
    ]

    records = transform_commit_activity(
        commits_by_project,
        users_by_email,
        users_by_name,
        user_records,
    )

    assert len(records) == 1
    assert records[0]["id"] == 1
    assert records[0]["project_id"] == 123
    assert records[0]["commit_count"] == 1
