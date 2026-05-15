from cartography.intel.jumpcloud import applications


def test_transform_builds_one_to_many_user_ids() -> None:
    api_result = [
        {
            "id": "app-1",
            "catalog_app_id": "google-workspace",
            "users": [
                {"user_id": "u-1"},
                {"user_id": "u-2"},
            ],
        },
        {
            "id": "app-2",
            "catalog_app_id": "atlassian",
            "users": [
                {"user_id": "u-2"},
                {"user_id": "u-3"},
                {"other_field": "ignored"},
            ],
        },
    ]

    transformed = applications.transform(api_result)

    assert transformed == [
        {
            "id": "app-1",
            "name": "google-workspace",
            "user_ids": ["u-1", "u-2"],
        },
        {
            "id": "app-2",
            "name": "atlassian",
            "user_ids": ["u-2", "u-3"],
        },
    ]
