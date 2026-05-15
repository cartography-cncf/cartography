from copy import deepcopy
from typing import Any
from typing import cast

from tests.data.github.users import GITHUB_ENTERPRISE_OWNER_DATA
from tests.data.github.users import GITHUB_ORG_DATA
from tests.data.github.users import GITHUB_USER_DATA

CLASSIC_PAT_FIXTURE = "ghp_fixture"
FINE_GRAINED_PAT_FIXTURE = "github_pat_fixture"
GENERIC_PAT_FIXTURE = "pat_fixture"

PAT_CONFIG_BY_KEY = {
    "token": GENERIC_PAT_FIXTURE,
    "classic_pat": CLASSIC_PAT_FIXTURE,
    "fine_grained_pat": FINE_GRAINED_PAT_FIXTURE,
}

GITHUB_RATE_LIMIT_OK = {
    "resources": {
        "graphql": {
            "limit": 5000,
            "remaining": 5000,
            "reset": 4102444800,
            "used": 0,
            "resource": "graphql",
        },
    },
}


def build_graphql_page(
    resource_type: str, edges: list[dict[str, Any]]
) -> dict[str, Any]:
    return {
        "data": {
            "organization": {
                "url": GITHUB_ORG_DATA["url"],
                "login": GITHUB_ORG_DATA["login"],
                resource_type: {
                    "nodes": [],
                    "edges": deepcopy(edges),
                    "pageInfo": {
                        "endCursor": None,
                        "hasNextPage": False,
                    },
                },
            },
        },
    }


GITHUB_USERS_GRAPHQL_RESPONSE = build_graphql_page(
    "membersWithRole",
    cast(list[dict[str, Any]], GITHUB_USER_DATA[0]),
)
GITHUB_ENTERPRISE_OWNERS_GRAPHQL_RESPONSE = build_graphql_page(
    "enterpriseOwners",
    cast(list[dict[str, Any]], GITHUB_ENTERPRISE_OWNER_DATA[0]),
)
