"""
Test data for https://cloud-native.slack.com/archives/C080M2LRLDA/p1758092875954949.
"""

from typing import Any

# Simplified test repos for collaborators bug reproduction
COLLABORATORS_TEST_REPOS: list[dict[str, Any]] = [
    {
        "name": "repo1",
        "url": "https://github.com/testorg/repo1",
        "directCollaborators": {"totalCount": 1},
        "outsideCollaborators": {"totalCount": 0},
        # Minimal required fields
        "nameWithOwner": "testorg/repo1",
        "primaryLanguage": {"name": "Python"},
        "sshUrl": "git@github.com:testorg/repo1.git",
        "createdAt": "2021-01-01T00:00:00Z",
        "description": "Test repo 1",
        "updatedAt": "2021-01-01T00:00:00Z",
        "homepageUrl": "",
        "languages": {"totalCount": 1, "nodes": [{"name": "Python"}]},
        "defaultBranchRef": {"name": "main", "id": "ref1"},
        "isPrivate": False,
        "isArchived": False,
        "isDisabled": False,
        "isLocked": False,
        "owner": {
            "url": "https://github.com/testorg",
            "login": "testorg",
            "__typename": "Organization",
        },
        "requirements": None,
        "setupCfg": None,
    },
    {
        "name": "repo2",
        "url": "https://github.com/testorg/repo2",
        "directCollaborators": {"totalCount": 1},
        "outsideCollaborators": {"totalCount": 0},
        # Minimal required fields
        "nameWithOwner": "testorg/repo2",
        "primaryLanguage": {"name": "Python"},
        "sshUrl": "git@github.com:testorg/repo2.git",
        "createdAt": "2021-01-01T00:00:00Z",
        "description": "Test repo 2",
        "updatedAt": "2021-01-01T00:00:00Z",
        "homepageUrl": "",
        "languages": {"totalCount": 1, "nodes": [{"name": "Python"}]},
        "defaultBranchRef": {"name": "main", "id": "ref2"},
        "isPrivate": False,
        "isArchived": False,
        "isDisabled": False,
        "isLocked": False,
        "owner": {
            "url": "https://github.com/testorg",
            "login": "testorg",
            "__typename": "Organization",
        },
        "requirements": None,
        "setupCfg": None,
    },
]
