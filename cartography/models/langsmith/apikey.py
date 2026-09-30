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
from cartography.models.ontology.labels import API_KEY


@dataclass(frozen=True)
class LangSmithApiKeyNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", description="API key UUID.")
    name: PropertyRef = PropertyRef(
        "description", description="User-supplied description of the key."
    )
    short_key: PropertyRef = PropertyRef(
        "short_key",
        description=(
            "Truncated, non-secret prefix of the key, used to identify it in the UI. "
            "The full key value is never ingested."
        ),
    )
    key_type: PropertyRef = PropertyRef(
        "key_type",
        extra_index=True,
        description=(
            "One of pat (personal access token, lsv2_pt), service_key (organization service "
            "key, lsv2_sk), workspace_key (workspace API key, lsv2_sk) or scim_token (lsv2_sc)."
        ),
    )
    access_scope: PropertyRef = PropertyRef(
        "access_scope",
        description="Whether the key is scoped to an organization or a workspace.",
    )
    read_only: PropertyRef = PropertyRef(
        "read_only",
        description="Deprecated LangSmith flag retained on the API response.",
    )
    created_at: PropertyRef = PropertyRef(
        "created_at", description="Timestamp when the key was created."
    )
    last_used_at: PropertyRef = PropertyRef(
        "last_used_at",
        description="Timestamp when the key was last used to authenticate.",
    )
    expires_at: PropertyRef = PropertyRef(
        "expires_at",
        description="Timestamp when the key expires, or null if the key never expires.",
    )
    revoked_at: PropertyRef = PropertyRef(
        "revoked_at",
        description="Timestamp when the key was revoked, or null if the key is still live.",
    )
    workspace_names: PropertyRef = PropertyRef(
        "workspace_names", description="Names of the workspaces this key can reach."
    )
    default_workspace_name: PropertyRef = PropertyRef(
        "default_workspace_name",
        description="Name of the workspace this key targets when no workspace header is sent.",
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class LangSmithApiKeyToOrganizationRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:LangSmithOrganization)-[:RESOURCE]->(:LangSmithApiKey)
class LangSmithApiKeyToOrganizationRel(CartographyRelSchema):
    """Links an organization to an API key issued within it."""

    target_node_label: str = "LangSmithOrganization"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ORG_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: LangSmithApiKeyToOrganizationRelProperties = (
        LangSmithApiKeyToOrganizationRelProperties()
    )


@dataclass(frozen=True)
class LangSmithApiKeyToUserRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# Canonical ontology edge: (:APIKey)-[:OWNED_BY]->(:UserAccount)
class LangSmithApiKeyToUserRel(CartographyRelSchema):
    """An API key is owned by the user account that created it."""

    target_node_label: str = "LangSmithUser"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("owner_ls_user_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "OWNED_BY"
    properties: LangSmithApiKeyToUserRelProperties = (
        LangSmithApiKeyToUserRelProperties()
    )


@dataclass(frozen=True)
class LangSmithApiKeyToRoleRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:LangSmithApiKey)-[:ASSUMES]->(:LangSmithRole)
class LangSmithApiKeyToRoleRel(CartographyRelSchema):
    """An API key acts with the permissions of the roles it is bound to."""

    target_node_label: str = "LangSmithRole"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("role_ids", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "ASSUMES"
    properties: LangSmithApiKeyToRoleRelProperties = (
        LangSmithApiKeyToRoleRelProperties()
    )


@dataclass(frozen=True)
class LangSmithApiKeyToWorkspaceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:LangSmithWorkspace)-[:CONTAINS]->(:LangSmithApiKey)
class LangSmithApiKeyToWorkspaceRel(CartographyRelSchema):
    """A workspace-scoped API key belongs to a workspace."""

    target_node_label: str = "LangSmithWorkspace"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("workspace_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "CONTAINS"
    properties: LangSmithApiKeyToWorkspaceRelProperties = (
        LangSmithApiKeyToWorkspaceRelProperties()
    )


@dataclass(frozen=True)
class LangSmithApiKeySchema(CartographyNodeSchema):
    """
    A LangSmith credential: a personal access token, an organization service key, a
    workspace API key, or a SCIM token. Only the non-secret short prefix is stored.
    """

    label: str = "LangSmithApiKey"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(
        [API_KEY]
    )  # APIKey label is used for ontology mapping
    properties: LangSmithApiKeyNodeProperties = LangSmithApiKeyNodeProperties()
    sub_resource_relationship: LangSmithApiKeyToOrganizationRel = (
        LangSmithApiKeyToOrganizationRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            LangSmithApiKeyToUserRel(),
            LangSmithApiKeyToRoleRel(),
            LangSmithApiKeyToWorkspaceRel(),
        ],
    )
