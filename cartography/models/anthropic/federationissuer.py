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
from cartography.models.ontology.labels import IDENTITY_PROVIDER


@dataclass(frozen=True)
class AnthropicFederationIssuerNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", description="Anthropic federation issuer ID.")
    name: PropertyRef = PropertyRef("name", description="Federation issuer name.")
    issuer_url: PropertyRef = PropertyRef(
        "issuer_url",
        extra_index=True,
        description="URL of the OIDC identity provider whose tokens this issuer trusts.",
    )
    check_jti: PropertyRef = PropertyRef(
        "check_jti",
        description=(
            "Whether the token exchange enforces single use per jti claim (replay "
            "protection). Defaults to true, and only applies to assertions that "
            "carry a jti."
        ),
    )
    max_jwt_lifetime_seconds: PropertyRef = PropertyRef(
        "max_jwt_lifetime_seconds",
        description="Longest lifetime accepted on an assertion from this issuer.",
    )
    jwks_type: PropertyRef = PropertyRef(
        "jwks_type",
        description=(
            "How the signing keys are obtained: discovery, explicit_url, or inline. "
            "Inline keys are never refreshed automatically."
        ),
    )
    jwks_url: PropertyRef = PropertyRef(
        "jwks_url",
        description=(
            "URL the signing keys are fetched from. Empty for inline keys, and for "
            "discovery unless a non-default discovery base is configured."
        ),
    )
    jwks_polling_disabled_at: PropertyRef = PropertyRef(
        "jwks_polling_disabled_at",
        description=(
            "RFC 3339 timestamp when key polling was disabled. A live issuer with "
            "polling disabled will not pick up a key rotation."
        ),
    )
    poll_status_consecutive_failures: PropertyRef = PropertyRef(
        "poll_status.consecutive_failures",
        description="Number of consecutive failed attempts to fetch the signing keys.",
    )
    poll_status_last_fetched_at: PropertyRef = PropertyRef(
        "poll_status.last_fetched_at",
        description="RFC 3339 timestamp when the signing keys were last fetched.",
    )
    created_at: PropertyRef = PropertyRef(
        "created_at",
        description="RFC 3339 timestamp when the issuer was registered.",
    )
    updated_at: PropertyRef = PropertyRef(
        "updated_at",
        description="RFC 3339 timestamp when the issuer was last updated.",
    )
    archived_at: PropertyRef = PropertyRef(
        "archived_at",
        description=(
            "RFC 3339 timestamp when the issuer was archived. Empty while the "
            "issuer is live."
        ),
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AnthropicFederationIssuerToOrganizationRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:AnthropicOrganization)-[:RESOURCE]->(:AnthropicFederationIssuer)
class AnthropicFederationIssuerToOrganizationRel(CartographyRelSchema):
    """The organization contains the federation issuer."""

    target_node_label: str = "AnthropicOrganization"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ORG_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: AnthropicFederationIssuerToOrganizationRelProperties = (
        AnthropicFederationIssuerToOrganizationRelProperties()
    )


@dataclass(frozen=True)
class AnthropicFederationIssuerSchema(CartographyNodeSchema):
    """An external OIDC identity provider trusted for Workload Identity Federation.

    Only readable with an org:admin OAuth token, never with an Admin API key.
    """

    label: str = "AnthropicFederationIssuer"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([IDENTITY_PROVIDER])
    properties: AnthropicFederationIssuerNodeProperties = (
        AnthropicFederationIssuerNodeProperties()
    )
    sub_resource_relationship: AnthropicFederationIssuerToOrganizationRel = (
        AnthropicFederationIssuerToOrganizationRel()
    )
