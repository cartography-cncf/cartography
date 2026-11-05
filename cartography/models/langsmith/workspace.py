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
from cartography.models.ontology.labels import TENANT


@dataclass(frozen=True)
class LangSmithWorkspaceNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", description="Workspace (tenant) UUID.")
    name: PropertyRef = PropertyRef(
        "display_name", description="Workspace display name."
    )
    tenant_handle: PropertyRef = PropertyRef(
        "tenant_handle", description="URL handle for the workspace."
    )
    is_personal: PropertyRef = PropertyRef(
        "is_personal",
        description="True if this is a user's personal workspace rather than a shared one.",
    )
    is_deleted: PropertyRef = PropertyRef(
        "is_deleted", description="True if the workspace has been deleted."
    )
    data_plane_url: PropertyRef = PropertyRef(
        "data_plane_url",
        description="URL of the data plane serving this workspace, for self-hosted and BYOC deployments.",
    )
    created_at: PropertyRef = PropertyRef(
        "created_at", description="Timestamp when the workspace was created."
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class LangSmithWorkspaceToOrganizationRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:LangSmithOrganization)-[:RESOURCE]->(:LangSmithWorkspace)
class LangSmithWorkspaceToOrganizationRel(CartographyRelSchema):
    """Links an organization to a workspace it owns."""

    target_node_label: str = "LangSmithOrganization"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ORG_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: LangSmithWorkspaceToOrganizationRelProperties = (
        LangSmithWorkspaceToOrganizationRelProperties()
    )


@dataclass(frozen=True)
class LangSmithWorkspaceSchema(CartographyNodeSchema):
    """A LangSmith workspace, called a tenant in the API, scoping projects, datasets and deployments."""

    label: str = "LangSmithWorkspace"
    properties: LangSmithWorkspaceNodeProperties = LangSmithWorkspaceNodeProperties()
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([TENANT])
    sub_resource_relationship: LangSmithWorkspaceToOrganizationRel = (
        LangSmithWorkspaceToOrganizationRel()
    )
