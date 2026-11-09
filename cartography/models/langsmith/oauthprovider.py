from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import TargetNodeMatcher
from cartography.models.ontology.labels import THIRD_PARTY_APP


@dataclass(frozen=True)
class LangSmithOAuthProviderNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", description="OAuth provider record UUID.")
    provider_id: PropertyRef = PropertyRef(
        "provider_id",
        extra_index=True,
        description="Operator-chosen provider slug, for example github-prod.",
    )
    name: PropertyRef = PropertyRef(
        "name", description="Display name of the OAuth provider."
    )
    provider_type: PropertyRef = PropertyRef(
        "provider_type", description="Provider category, for example oauth2 or mcp."
    )
    client_id: PropertyRef = PropertyRef(
        "client_id",
        description=(
            "OAuth client ID registered with the upstream provider. The client secret is "
            "never returned by the API and is not ingested."
        ),
    )
    auth_url: PropertyRef = PropertyRef(
        "auth_url", description="Upstream authorization endpoint."
    )
    token_url: PropertyRef = PropertyRef(
        "token_url", description="Upstream token endpoint."
    )
    mcp_server_url: PropertyRef = PropertyRef(
        "mcp_server_url",
        description="URL of the MCP server this provider fronts, when the provider is MCP-backed.",
    )
    uses_pkce: PropertyRef = PropertyRef(
        "uses_pkce", description="True if the provider uses PKCE."
    )
    token_endpoint_auth_method: PropertyRef = PropertyRef(
        "token_endpoint_auth_method",
        description="How LangSmith authenticates to the token endpoint.",
    )
    is_dynamic_client: PropertyRef = PropertyRef(
        "is_dynamic_client",
        description="True if the OAuth client was registered dynamically rather than configured.",
    )
    allowed_redirect_uris: PropertyRef = PropertyRef(
        "allowed_redirect_uris",
        description="Redirect URIs accepted when completing the OAuth flow.",
    )
    is_platform_provider: PropertyRef = PropertyRef(
        "is_platform_provider",
        description="True if this is a LangChain-managed provider rather than one the organization configured.",
    )
    created_at: PropertyRef = PropertyRef(
        "created_at", description="Timestamp when the provider was registered."
    )
    updated_at: PropertyRef = PropertyRef(
        "updated_at", description="Timestamp when the provider was last updated."
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class LangSmithOAuthProviderToOrganizationRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:LangSmithOrganization)-[:RESOURCE]->(:LangSmithOAuthProvider)
class LangSmithOAuthProviderToOrganizationRel(CartographyRelSchema):
    """Links an organization to an OAuth provider configured within it."""

    target_node_label: str = "LangSmithOrganization"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ORG_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: LangSmithOAuthProviderToOrganizationRelProperties = (
        LangSmithOAuthProviderToOrganizationRelProperties()
    )


@dataclass(frozen=True)
class LangSmithOAuthProviderSchema(CartographyNodeSchema):
    """
    A third-party OAuth provider that LangSmith agents can obtain tokens from on a user's
    behalf, such as GitHub, Google or an MCP server.
    """

    label: str = "LangSmithOAuthProvider"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(
        [THIRD_PARTY_APP]
    )  # ThirdPartyApp label is used for ontology mapping
    properties: LangSmithOAuthProviderNodeProperties = (
        LangSmithOAuthProviderNodeProperties()
    )
    sub_resource_relationship: LangSmithOAuthProviderToOrganizationRel = (
        LangSmithOAuthProviderToOrganizationRel()
    )
