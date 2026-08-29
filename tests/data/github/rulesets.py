"""
Test data for GitHub repository rulesets.
Normalized from https://docs.github.com/en/rest/repos/rules#get-a-repository-ruleset
"""

from typing import Any

RULESET_PRODUCTION = {
    "id": "RRS_lACkVXNlcs4AXenizgBRqVA",
    "databaseId": 5351760,
    "name": "production-ruleset",
    "target": "BRANCH",
    "source": {},
    "enforcement": "ACTIVE",
    "createdAt": "2025-05-07T21:04:33Z",
    "updatedAt": "2025-05-07T21:04:33Z",
    "conditions": {
        "refName": {
            "include": ["~DEFAULT_BRANCH"],
            "exclude": [],
        },
        "repositoryName": {
            "include": ["important-*"],
            "exclude": ["important-archive"],
            "protected": False,
        },
        "repositoryId": {
            "repositoryIds": [123456789],
        },
        "repositoryProperty": {
            "include": [
                {
                    "name": "visibility",
                    "propertyValues": ["private"],
                    "source": "custom",
                },
            ],
            "exclude": [],
        },
        "organizationProperty": {
            "include": [
                {
                    "name": "environment",
                    "propertyValues": ["prod"],
                },
            ],
            "exclude": [
                {
                    "name": "lifecycle",
                    "propertyValues": ["deprecated"],
                },
            ],
        },
    },
    "rules": {
        "nodes": [
            {
                "id": "RRU_kwDORule001",
                "type": "DELETION",
                "parameters": None,
            },
            {
                "id": "RRU_kwDORule002",
                "type": "PULL_REQUEST",
                "parameters": {
                    "requiredApprovingReviewCount": 2,
                    "dismissStaleReviewsOnPush": True,
                    "requireCodeOwnerReview": True,
                },
            },
            {
                "id": "RRU_kwDORule003",
                "type": "REQUIRED_STATUS_CHECKS",
                "parameters": {
                    "requiredStatusChecks": [
                        {"context": "ci/tests"},
                    ],
                },
            },
        ],
    },
}

RULESET_EVALUATE = {
    "id": "RRS_lACqUmVwb3NpdG9yec4AnLYqzgBmHxs",
    "databaseId": 6692635,
    "name": "CLA Enforcement",
    "target": "BRANCH",
    "source": {},
    "enforcement": "EVALUATE",
    "createdAt": "2025-07-14T17:28:11Z",
    "updatedAt": "2025-12-18T09:04:50Z",
    "conditions": {
        "refName": {
            "include": ["~ALL"],
            "exclude": ["refs/heads/dependabot/**/*"],
        },
    },
    "rules": {
        "nodes": [
            {
                "id": "RRU_kwDORule101",
                "type": "REQUIRED_STATUS_CHECKS",
                "parameters": {},
            },
        ],
    },
}

RULESET_TAGS = {
    "id": "RRS_kwDOTag001",
    "databaseId": 1234567,
    "name": "Tag Protection",
    "target": "TAG",
    "source": {},
    "enforcement": "ACTIVE",
    "createdAt": "2025-01-15T10:00:00Z",
    "updatedAt": "2025-01-15T10:00:00Z",
    "conditions": {
        "refName": {
            "include": ["refs/tags/v*"],
            "exclude": [],
        },
    },
    "rules": {
        "nodes": [
            {
                "id": "RRU_kwDORule201",
                "type": "DELETION",
                "parameters": None,
            },
        ],
    },
}

RULESETS_DATA: list[dict[str, Any]] = [
    RULESET_PRODUCTION,
    RULESET_EVALUATE,
    RULESET_TAGS,
]

SINGLE_RULESET: list[dict[str, Any]] = [
    RULESET_PRODUCTION,
]

NO_RULESETS: list[dict[str, Any]] = []
