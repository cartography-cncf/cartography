import pytest

from cartography.intel.notion.pages import transform
from tests.data.notion.pages import PRIVATE_PAGE
from tests.data.notion.pages import PUBLIC_PAGE


def test_transform_keeps_only_public_page_metadata():
    # Act
    public_pages, unpublished_page_ids = transform(
        [PUBLIC_PAGE, PRIVATE_PAGE],
        "workspace-1",
        {"page-private"},
    )

    # Assert
    assert public_pages == [
        {
            "id": "workspace-1/page-public",
            "notion_page_id": "page-public",
            "title": "Public security guidance",
            "url": "https://www.notion.so/page-public",
            "public_url": "https://example.notion.site/page-public",
            "is_public": True,
            "created_time": "2026-01-02T03:04:05.000Z",
            "last_edited_time": "2026-02-03T04:05:06.000Z",
            "in_trash": False,
            "is_locked": True,
            "parent_type": "page_id",
            "parent_notion_id": "page-parent",
            "created_by_notion_user_id": "person-1",
            "created_by_id": "workspace-1/person-1",
        },
    ]
    assert unpublished_page_ids == ["workspace-1/page-private"]


def test_transform_does_not_delete_new_private_pages():
    # Act
    public_pages, unpublished_page_ids = transform(
        [PRIVATE_PAGE],
        "workspace-1",
        set(),
    )

    # Assert
    assert public_pages == []
    assert unpublished_page_ids == []


@pytest.mark.parametrize(
    "page",
    [
        {**PUBLIC_PAGE, "object": "database"},
        {**PUBLIC_PAGE, "id": None},
        {**PUBLIC_PAGE, "public_url": []},
        {**PUBLIC_PAGE, "created_by": []},
        {**PUBLIC_PAGE, "parent": []},
        {**PUBLIC_PAGE, "properties": []},
    ],
)
def test_transform_rejects_malformed_pages(page):
    # Act and assert
    with pytest.raises(ValueError):
        transform([page], "workspace-1", set())
