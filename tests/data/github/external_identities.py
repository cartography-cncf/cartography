ORG = "example-org"
ORG_URL = "https://github.com/example-org"
API_URL = "https://api.github.com/graphql"

IDENTITIES = [
    {
        "id": "E_example_alice",
        "samlIdentity": {"nameId": " Alice@Example.com "},
        "user": {"url": "https://github.com/example-alice"},
    },
    {
        "id": "E_example_bob",
        "samlIdentity": {"nameId": "bob@example.com"},
        "user": {"url": "https://github.com/example-bob"},
    },
    {
        "id": "E_example_unlinked",
        "samlIdentity": {"nameId": "unlinked@example.com"},
        "user": None,
    },
    {
        "id": "E_example_without_saml",
        "samlIdentity": None,
        "user": {"url": "https://github.com/example-carol"},
    },
]


def page(nodes, *, has_next_page=False, cursor=None, org_url=ORG_URL):
    return {
        "data": {
            "organization": {
                "url": org_url,
                "samlIdentityProvider": {
                    "externalIdentities": {
                        "nodes": nodes,
                        "pageInfo": {
                            "hasNextPage": has_next_page,
                            "endCursor": cursor,
                        },
                    }
                },
            }
        }
    }


NO_SAML_PROVIDER = {
    "data": {"organization": {"url": ORG_URL, "samlIdentityProvider": None}}
}
FORBIDDEN = {
    "data": {"organization": {"url": ORG_URL, "samlIdentityProvider": None}},
    "errors": [
        {
            "type": "FORBIDDEN",
            "path": ["organization", "samlIdentityProvider"],
            "message": "Resource not accessible by integration",
        }
    ],
}
