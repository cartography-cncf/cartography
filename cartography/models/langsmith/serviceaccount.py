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
from cartography.models.ontology.labels import SERVICE_ACCOUNT


@dataclass(frozen=True)
class LangSmithServiceAccountNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", description="Service account UUID.")
    name: PropertyRef = PropertyRef(
        "name", extra_index=True, description="Service account name."
    )
    created_at: PropertyRef = PropertyRef(
        "created_at", description="Timestamp when the service account was created."
    )
    updated_at: PropertyRef = PropertyRef(
        "updated_at", description="Timestamp when the service account was last updated."
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class LangSmithServiceAccountToOrganizationRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:LangSmithOrganization)-[:RESOURCE]->(:LangSmithServiceAccount)
class LangSmithServiceAccountToOrganizationRel(CartographyRelSchema):
    """Links an organization to one of its service accounts."""

    target_node_label: str = "LangSmithOrganization"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ORG_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: LangSmithServiceAccountToOrganizationRelProperties = (
        LangSmithServiceAccountToOrganizationRelProperties()
    )


@dataclass(frozen=True)
class LangSmithServiceAccountToWorkspaceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:LangSmithServiceAccount)-[:DEFAULT_WORKSPACE]->(:LangSmithWorkspace)
class LangSmithServiceAccountToWorkspaceRel(CartographyRelSchema):
    """Links a service account to the workspace it defaults to."""

    target_node_label: str = "LangSmithWorkspace"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("default_workspace_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "DEFAULT_WORKSPACE"
    properties: LangSmithServiceAccountToWorkspaceRelProperties = (
        LangSmithServiceAccountToWorkspaceRelProperties()
    )


@dataclass(frozen=True)
class LangSmithServiceAccountSchema(CartographyNodeSchema):
    """A LangSmith service account: a non-human principal that can hold service keys."""

    label: str = "LangSmithServiceAccount"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(
        [SERVICE_ACCOUNT]
    )  # ServiceAccount label is used for ontology mapping
    properties: LangSmithServiceAccountNodeProperties = (
        LangSmithServiceAccountNodeProperties()
    )
    sub_resource_relationship: LangSmithServiceAccountToOrganizationRel = (
        LangSmithServiceAccountToOrganizationRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            LangSmithServiceAccountToWorkspaceRel(),
        ],
    )
