from msgraph.generated.models.o_auth2_permission_grant import OAuth2PermissionGrant

from cartography.intel.microsoft.entra.oauth2_permission_grants import (
    MICROSOFT_GRAPH_APP_ID,
)
from cartography.intel.microsoft.entra.oauth2_permission_grants import (
    transform_oauth2_permission_grants,
)

TENANT_ID = "tenant-1"
GRAPH_SP_ID = "sp-graph"
CUSTOM_API_SP_ID = "sp-custom-api"


def _grant(**kwargs: str) -> OAuth2PermissionGrant:
    return OAuth2PermissionGrant(**kwargs)


def test_transform_oauth2_permission_grants() -> None:
    grants = [
        # One consent to an app that calls two APIs arrives as two grants.
        _grant(
            client_id="sp-vendor",
            consent_type="Principal",
            principal_id="user-1",
            resource_id=GRAPH_SP_ID,
            scope=" User.Read Mail.Read ",
        ),
        _grant(
            client_id="sp-vendor",
            consent_type="Principal",
            principal_id="user-1",
            resource_id=CUSTOM_API_SP_ID,
            scope="access_as_user",
        ),
        _grant(
            client_id="sp-vendor",
            consent_type="AllPrincipals",
            resource_id=GRAPH_SP_ID,
            scope="User.Read",
        ),
        # The API's service principal is not in the graph: fall back to its id.
        _grant(
            client_id="sp-other",
            consent_type="Principal",
            principal_id="user-2",
            resource_id="sp-unknown",
            scope="Read",
        ),
        _grant(
            client_id="sp-empty",
            consent_type="Principal",
            principal_id="user-1",
            resource_id=GRAPH_SP_ID,
            scope=" ",
        ),
    ]

    authorizations, admin_consents = transform_oauth2_permission_grants(
        grants,
        TENANT_ID,
        {GRAPH_SP_ID: MICROSOFT_GRAPH_APP_ID, CUSTOM_API_SP_ID: "custom-api-app-id"},
    )

    assert authorizations == [
        {
            "principal_id": "user-1",
            "client_id": "sp-vendor",
            "scopes": [
                "custom-api-app-id/access_as_user",
                "https://graph.microsoft.com/Mail.Read",
                "https://graph.microsoft.com/User.Read",
            ],
            "match_method": None,
        },
        {
            "principal_id": "user-2",
            "client_id": "sp-other",
            "scopes": ["sp-unknown/Read"],
            "match_method": None,
        },
    ]
    assert admin_consents == [
        {
            "tenant_id": TENANT_ID,
            "client_id": "sp-vendor",
            "scopes": ["https://graph.microsoft.com/User.Read"],
        },
    ]
