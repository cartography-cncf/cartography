from unittest.mock import MagicMock

import pytest

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


def test_get_paginated_list_raises_when_max_pages_reached():
    mock_list = MagicMock(
        side_effect=[
            {
                "projects": [{"id": "project-1"}],
                "links": {"pages": {"next": "page-2"}},
            },
            {
                "projects": [{"id": "project-2"}],
                "links": {"pages": {"next": "page-3"}},
            },
        ],
    )

    with pytest.raises(
        RuntimeError,
        match="Reached maximum page limit of 2 while more pages are available.",
    ):
        get_paginated_list(
            mock_list,
            "projects",
            max_pages=2,
        )

    assert mock_list.call_count == 2


def test_get_paginated_list_raises_when_target_key_missing():
    mock_list = MagicMock(
        return_value={
            "links": {
                "pages": {},
            },
        },
    )

    with pytest.raises(
        RuntimeError,
        match="Expected key 'projects' in paginated response.",
    ):
        get_paginated_list(
            mock_list,
            "projects",
        )
