from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import OtherRelationships
from cartography.models.core.relationships import TargetNodeMatcher
from cartography.models.ontology.labels import THIRD_PARTY_APP


@dataclass(frozen=True)
class LangSmithOAuthClientNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "client_id", description="OAuth client ID issued by LangSmith."
    )
    name: PropertyRef = PropertyRef(
        "client_name", extra_index=True, description="Display name of the OAuth client."
    )
    client_type: PropertyRef = PropertyRef(
        "client_type", description="Client type, for example public or confidential."
    )
    client_uri: PropertyRef = PropertyRef(
        "client_uri", description="Home page URI of the client application."
    )
    logo_uri: PropertyRef = PropertyRef(
        "logo_uri", description="Logo URI of the client application."
    )
    policy_uri: PropertyRef = PropertyRef(
        "policy_uri", description="Privacy policy URI of the client application."
    )
    tos_uri: PropertyRef = PropertyRef(
        "tos_uri", description="Terms of service URI of the client application."
    )
    redirect_uris: PropertyRef = PropertyRef(
        "redirect_uris", description="Redirect URIs registered for this client."
    )
    allowed_scopes: PropertyRef = PropertyRef(
        "allowed_scopes",
        description="LangSmith scopes this client is permitted to request.",
    )
    grant_types: PropertyRef = PropertyRef(
        "grant_types", description="OAuth grant types this client may use."
    )
    disabled: PropertyRef = PropertyRef(
        "disabled", description="True if the client has been disabled."
    )
    created_at: PropertyRef = PropertyRef(
        "created_at", description="Timestamp when the client was registered."
    )
    updated_at: PropertyRef = PropertyRef(
        "updated_at", description="Timestamp when the client was last updated."
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class LangSmithOAuthClientToOrganizationRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:LangSmithOrganization)-[:RESOURCE]->(:LangSmithOAuthClient)
class LangSmithOAuthClientToOrganizationRel(CartographyRelSchema):
    """Links an organization to an OAuth client registered against it."""

    target_node_label: str = "LangSmithOrganization"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ORG_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: LangSmithOAuthClientToOrganizationRelProperties = (
        LangSmithOAuthClientToOrganizationRelProperties()
    )


@dataclass(frozen=True)
class LangSmithOAuthClientToWorkspaceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:LangSmithWorkspace)-[:CONTAINS]->(:LangSmithOAuthClient)
class LangSmithOAuthClientToWorkspaceRel(CartographyRelSchema):
    """Links an OAuth client to the workspace it was registered in."""

    target_node_label: str = "LangSmithWorkspace"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("workspace_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "CONTAINS"
    properties: LangSmithOAuthClientToWorkspaceRelProperties = (
        LangSmithOAuthClientToWorkspaceRelProperties()
    )


@dataclass(frozen=True)
class LangSmithOAuthClientSchema(CartographyNodeSchema):
    """
    A third-party application registered to call the LangSmith API via OAuth. This is
    LangSmith acting as the authorization server, the reverse direction from
    LangSmithOAuthProvider.
    """

    label: str = "LangSmithOAuthClient"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(
        [THIRD_PARTY_APP]
    )  # ThirdPartyApp label is used for ontology mapping
    properties: LangSmithOAuthClientNodeProperties = (
        LangSmithOAuthClientNodeProperties()
    )
    sub_resource_relationship: LangSmithOAuthClientToOrganizationRel = (
        LangSmithOAuthClientToOrganizationRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            LangSmithOAuthClientToWorkspaceRel(),
        ],
    )
