"""
Test data for GitHub commits module.
"""

MOCK_COMMIT_DATA = [
    {
        "committedDate": "2023-12-01T10:30:00Z",
        "author": {
            "user": {
                "url": "https://github.com/alice",
            }
        },
    },
    {
        "committedDate": "2023-12-02T14:22:00Z",
        "author": {
            "user": {
                "url": "https://github.com/bob",
            }
        },
    },
    {
        "committedDate": "2023-12-03T09:15:00Z",
        "author": {
            "user": {
                "url": "https://github.com/alice",
            }
        },
    },
]

MOCK_COMMITS_BY_REPO = {
    "repo1": [
        MOCK_COMMIT_DATA[0],  # Alice commit
        MOCK_COMMIT_DATA[2],  # Alice commit
    ],
    "repo2": [
        MOCK_COMMIT_DATA[1],  # Bob commit
    ],
}

EXPECTED_COMMIT_RELATIONSHIPS = [
    {
        "user_url": "https://github.com/alice",
        "repo_url": "https://github.com/testorg/repo1",
        "commit_count": 2,
        "last_commit_date": "2023-12-03T09:15:00+00:00",
        "first_commit_date": "2023-12-01T10:30:00+00:00",
    },
    {
        "user_url": "https://github.com/bob",
        "repo_url": "https://github.com/testorg/repo2",
        "commit_count": 1,
        "last_commit_date": "2023-12-02T14:22:00+00:00",
        "first_commit_date": "2023-12-02T14:22:00+00:00",
    },
]
