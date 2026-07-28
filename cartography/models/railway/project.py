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
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef("name", extra_index=True)
    description: PropertyRef = PropertyRef("description")
    # Exposure signal: a public project's dashboard and logs are readable by anyone.
    is_public: PropertyRef = PropertyRef("isPublic", extra_index=True)
    is_temp_project: PropertyRef = PropertyRef("isTempProject")
    pr_deploys: PropertyRef = PropertyRef("prDeploys")
    subscription_type: PropertyRef = PropertyRef("subscriptionType")
    workspace_id: PropertyRef = PropertyRef("workspaceId")
    created_at: PropertyRef = PropertyRef("createdAt")
    updated_at: PropertyRef = PropertyRef("updatedAt")
    deleted_at: PropertyRef = PropertyRef("deletedAt")


@dataclass(frozen=True)
class RailwayProjectToWorkspaceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:RailwayWorkspace)-[:RESOURCE]->(:RailwayProject)
class RailwayProjectToWorkspaceRel(CartographyRelSchema):
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
    label: str = "RailwayProject"
    properties: RailwayProjectNodeProperties = RailwayProjectNodeProperties()
    # A project is the second tenancy level, mirroring ScalewayOrganization -> ScalewayProject:
    # everything inside it scopes its cleanup to the project rather than to the workspace.
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([TENANT])
    sub_resource_relationship: RailwayProjectToWorkspaceRel = (
        RailwayProjectToWorkspaceRel()
    )
