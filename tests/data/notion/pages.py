PUBLIC_PAGE = {
    "object": "page",
    "id": "page-public",
    "created_time": "2026-01-02T03:04:05.000Z",
    "last_edited_time": "2026-02-03T04:05:06.000Z",
    "created_by": {"object": "user", "id": "person-1"},
    "last_edited_by": {"object": "user", "id": "person-2"},
    "parent": {"type": "page_id", "page_id": "page-parent"},
    "in_trash": False,
    "is_locked": True,
    "properties": {
        "Name": {
            "id": "title",
            "type": "title",
            "title": [
                {"type": "text", "plain_text": "Public security guidance"},
            ],
        },
    },
    "url": "https://www.notion.so/page-public",
    "public_url": "https://example.notion.site/page-public",
}

PRIVATE_PAGE = {
    **PUBLIC_PAGE,
    "id": "page-private",
    "url": "https://www.notion.so/page-private",
    "public_url": None,
}
