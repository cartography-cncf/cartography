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
class RailwayProjectNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", description="ID of the Railway project.")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef(
        "name", extra_index=True, description="Name of the project."
    )
    description: PropertyRef = PropertyRef(
        "description", description="Free-text project description."
    )
    # Exposure signal: a public project's dashboard and logs are readable by anyone.
    is_public: PropertyRef = PropertyRef(
        "isPublic",
        extra_index=True,
        description="Whether the project's dashboard, build logs, and metrics are publicly readable.",
    )
    is_temp_project: PropertyRef = PropertyRef(
        "isTempProject", description="Whether this is a temporary project."
    )
    pr_deploys: PropertyRef = PropertyRef(
        "prDeploys", description="Whether pull-request environments are enabled."
    )
    subscription_type: PropertyRef = PropertyRef(
        "subscriptionType", description="Billing tier of the project."
    )
    workspace_id: PropertyRef = PropertyRef(
        "workspaceId", description="ID of the owning workspace."
    )
    created_at: PropertyRef = PropertyRef(
        "createdAt", description="Time when the project was created."
    )
    updated_at: PropertyRef = PropertyRef(
        "updatedAt", description="Time when the project was last modified."
    )
    deleted_at: PropertyRef = PropertyRef(
        "deletedAt", description="Time when the project was deleted, if applicable."
    )


@dataclass(frozen=True)
class RailwayProjectToWorkspaceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:RailwayWorkspace)-[:RESOURCE]->(:RailwayProject)
class RailwayProjectToWorkspaceRel(CartographyRelSchema):
    """Connects a Railway workspace to a project that it contains."""

    target_node_label: str = "RailwayWorkspace"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("WORKSPACE_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: RailwayProjectToWorkspaceRelProperties = (
        RailwayProjectToWorkspaceRelProperties()
    )


@dataclass(frozen=True)
class RailwayProjectSchema(CartographyNodeSchema):
    """A Railway project that contains environments and deployable resources."""

    label: str = "RailwayProject"
    properties: RailwayProjectNodeProperties = RailwayProjectNodeProperties()
    # A project is the second tenancy level, mirroring ScalewayOrganization -> ScalewayProject:
    # everything inside it scopes its cleanup to the project rather than to the workspace.
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([TENANT])
    sub_resource_relationship: RailwayProjectToWorkspaceRel = (
        RailwayProjectToWorkspaceRel()
    )
