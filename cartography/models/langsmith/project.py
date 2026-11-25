from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_source_node_matcher
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import OtherRelationships
from cartography.models.core.relationships import SourceNodeMatcher
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class LangSmithProjectNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", description="Tracing project UUID.")
    name: PropertyRef = PropertyRef(
        "name", extra_index=True, description="Tracing project name."
    )
    description: PropertyRef = PropertyRef(
        "description", description="Human-readable description of the project."
    )
    start_time: PropertyRef = PropertyRef(
        "start_time", description="When the project was created."
    )
    trace_tier: PropertyRef = PropertyRef(
        "trace_tier",
        description="Retention tier that LangSmith stores the project's new traces in.",
    )
    workspace_id: PropertyRef = PropertyRef(
        "workspace_id", description="UUID of the workspace the project belongs to."
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class LangSmithProjectToOrganizationRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:LangSmithOrganization)-[:RESOURCE]->(:LangSmithProject)
class LangSmithProjectToOrganizationRel(CartographyRelSchema):
    """Links an organization to a tracing project in one of its workspaces."""

    target_node_label: str = "LangSmithOrganization"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ORG_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: LangSmithProjectToOrganizationRelProperties = (
        LangSmithProjectToOrganizationRelProperties()
    )


@dataclass(frozen=True)
class LangSmithProjectToWorkspaceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:LangSmithWorkspace)-[:RESOURCE]->(:LangSmithProject)
class LangSmithProjectToWorkspaceRel(CartographyRelSchema):
    """Links a tracing project to the workspace it belongs to."""

    target_node_label: str = "LangSmithWorkspace"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("WORKSPACE_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: LangSmithProjectToWorkspaceRelProperties = (
        LangSmithProjectToWorkspaceRelProperties()
    )


@dataclass(frozen=True)
class LangSmithProjectToResourceTagRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    _sub_resource_label: PropertyRef = PropertyRef(
        "_sub_resource_label", set_in_kwargs=True
    )
    _sub_resource_id: PropertyRef = PropertyRef("_sub_resource_id", set_in_kwargs=True)


@dataclass(frozen=True)
# (:LangSmithProject)-[:TAGGED]->(:LangSmithResourceTag)
class LangSmithProjectToResourceTagRel(CartographyRelSchema):
    """
    A resource tag applied to the project. Access policies for the project
    resource type match on these tags.
    """

    source_node_label: str = "LangSmithProject"
    source_node_matcher: SourceNodeMatcher = make_source_node_matcher(
        {"id": PropertyRef("project_id")},
    )
    target_node_label: str = "LangSmithResourceTag"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("tag_value_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "TAGGED"
    properties: LangSmithProjectToResourceTagRelProperties = (
        LangSmithProjectToResourceTagRelProperties()
    )


@dataclass(frozen=True)
class LangSmithProjectToDeploymentRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:LangSmithDeployment)-[:TRACES_TO]->(:LangSmithProject)
class LangSmithProjectToDeploymentRel(CartographyRelSchema):
    """
    Links a deployment to the tracing project it writes runs to. Access policies on the
    project decide who can read the deployment's traces.
    """

    target_node_label: str = "LangSmithDeployment"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"tracer_session_id": PropertyRef("id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "TRACES_TO"
    properties: LangSmithProjectToDeploymentRelProperties = (
        LangSmithProjectToDeploymentRelProperties()
    )


@dataclass(frozen=True)
class LangSmithProjectSchema(CartographyNodeSchema):
    """
    A tracing project. Attribute-based access policies restrict who can read the traces
    it holds. Cartography doesn't ingest experiments.
    """

    label: str = "LangSmithProject"
    properties: LangSmithProjectNodeProperties = LangSmithProjectNodeProperties()
    sub_resource_relationship: LangSmithProjectToWorkspaceRel = (
        LangSmithProjectToWorkspaceRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            LangSmithProjectToOrganizationRel(),
            LangSmithProjectToDeploymentRel(),
        ],
    )
