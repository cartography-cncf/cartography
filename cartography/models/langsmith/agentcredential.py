from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import OtherRelationships
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class LangSmithAgentCredentialNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", description="Agent connection UUID.")
    provider_account_label: PropertyRef = PropertyRef(
        "provider_account_label",
        description="Label identifying which upstream account the token belongs to.",
    )
    scopes: PropertyRef = PropertyRef(
        "scopes", description="OAuth scopes the stored token was granted."
    )
    expires_at: PropertyRef = PropertyRef(
        "expires_at",
        description="Timestamp when the stored token expires, or null if it does not expire.",
    )
    oauth_token_id: PropertyRef = PropertyRef(
        "oauth_token_id",
        description=(
            "Identifier of the stored token record. This is an opaque reference only; no "
            "access or refresh token material is ingested."
        ),
    )
    created_at: PropertyRef = PropertyRef(
        "created_at", description="Timestamp when the connection was authorized."
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class LangSmithAgentCredentialToOrganizationRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:LangSmithOrganization)-[:RESOURCE]->(:LangSmithAgentCredential)
class LangSmithAgentCredentialToOrganizationRel(CartographyRelSchema):
    """Links an organization to an agent credential held within it."""

    target_node_label: str = "LangSmithOrganization"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ORG_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: LangSmithAgentCredentialToOrganizationRelProperties = (
        LangSmithAgentCredentialToOrganizationRelProperties()
    )


@dataclass(frozen=True)
class LangSmithAgentCredentialToAgentRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:LangSmithAgent)-[:HAS_CREDENTIAL]->(:LangSmithAgentCredential)
class LangSmithAgentCredentialToAgentRel(CartographyRelSchema):
    """The agent that can use this credential."""

    target_node_label: str = "LangSmithAgent"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("agent_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS_CREDENTIAL"
    properties: LangSmithAgentCredentialToAgentRelProperties = (
        LangSmithAgentCredentialToAgentRelProperties()
    )


@dataclass(frozen=True)
class LangSmithAgentCredentialToProviderRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:LangSmithAgentCredential)-[:FOR_PROVIDER]->(:LangSmithOAuthProvider)
class LangSmithAgentCredentialToProviderRel(CartographyRelSchema):
    """
    The third-party provider this credential authenticates against.

    Matched on the provider's UUID, resolved during transform, rather than on its
    provider_id slug. The slug is operator-chosen, so two organizations can both define
    one called github-prod, and relationship matching carries no implicit organization
    constraint.
    """

    target_node_label: str = "LangSmithOAuthProvider"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("provider_uuid")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "FOR_PROVIDER"
    properties: LangSmithAgentCredentialToProviderRelProperties = (
        LangSmithAgentCredentialToProviderRelProperties()
    )


@dataclass(frozen=True)
class LangSmithAgentCredentialToUserRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:LangSmithAgentCredential)-[:ON_BEHALF_OF]->(:LangSmithUser)
class LangSmithAgentCredentialToUserRel(CartographyRelSchema):
    """
    The human whose third-party account the agent can act as. This is the edge that answers
    which agents hold which user's OAuth tokens.
    """

    target_node_label: str = "LangSmithUser"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("owner_ls_user_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "ON_BEHALF_OF"
    properties: LangSmithAgentCredentialToUserRelProperties = (
        LangSmithAgentCredentialToUserRelProperties()
    )


@dataclass(frozen=True)
class LangSmithAgentCredentialSchema(CartographyNodeSchema):
    """
    A third-party OAuth token a LangSmith agent holds on a human's behalf, letting the
    agent call that provider's API as them.

    Only metadata is ingested: oauth_token_id is an opaque reference, and no access token,
    refresh token or client secret is requested or returned.
    """

    label: str = "LangSmithAgentCredential"
    properties: LangSmithAgentCredentialNodeProperties = (
        LangSmithAgentCredentialNodeProperties()
    )
    sub_resource_relationship: LangSmithAgentCredentialToOrganizationRel = (
        LangSmithAgentCredentialToOrganizationRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            LangSmithAgentCredentialToAgentRel(),
            LangSmithAgentCredentialToProviderRel(),
            LangSmithAgentCredentialToUserRel(),
        ],
    )
