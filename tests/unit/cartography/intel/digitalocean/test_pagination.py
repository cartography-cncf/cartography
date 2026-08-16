from cartography.intel.digitalocean.util.pagination import get_paginated_list


def test_get_paginated_list():
    responses = {
        1: {
            "projects": [{"id": "project_1"}],
            "links": {"pages": {"next": "page2"}},
        },
        2: {
            "projects": [{"id": "project_2"}],
            "links": {"pages": {}},
        },
    }

    def mock_list(*, page, per_page=20):
        return responses[page]

    result = get_paginated_list(
        mock_list,
        "projects",
        per_page=100,
    )

    assert result == [
        {"id": "project_1"},
        {"id": "project_2"},
    ]


def test_get_paginated_list_max_pages():
    def mock_list(*, page, per_page=20):
        return {
            "projects": [{"id": f"project_{page}"}],
            "links": {"pages": {"next": "next"}},
        }

    result = get_paginated_list(
        mock_list,
        "projects",
        max_pages=2,
    )

    assert len(result) == 2
