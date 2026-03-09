from cartography.intel.jumpcloud import applications


def test_extract_user_id_handles_known_shapes() -> None:
    assert applications._extract_user_id("u-1") == "u-1"
    assert applications._extract_user_id({"id": "u-2"}) == "u-2"
    assert applications._extract_user_id({"_id": "u-3"}) == "u-3"
    assert applications._extract_user_id({"user_id": "u-4"}) == "u-4"
    assert applications._extract_user_id({"userId": "u-5"}) == "u-5"
    assert applications._extract_user_id({"user": {"id": "u-6"}}) == "u-6"
    assert applications._extract_user_id({"user": {"_id": "u-7"}}) == "u-7"
    assert applications._extract_user_id({"foo": "bar"}) is None


def test_transform_builds_one_to_many_user_ids() -> None:
    api_result = [
        {
            "id": "app-1",
            "name": "App One",
            "description": "desc",
            "users": [{"id": "u-1"}, {"user": {"id": "u-2"}}],
        },
        {
            "_id": "app-2",
            "name": "App Two",
            "users": ["u-3", {"user_id": "u-4"}, {"bad": "value"}],
        },
    ]

    transformed = applications.transform(api_result)

    assert transformed == [
        {
            "id": "app-1",
            "name": "App One",
            "description": "desc",
            "user_ids": ["u-1", "u-2"],
        },
        {
            "id": "app-2",
            "name": "App Two",
            "description": None,
            "user_ids": ["u-3", "u-4"],
        },
    ]
