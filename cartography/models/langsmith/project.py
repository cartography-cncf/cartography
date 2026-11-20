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
        description="Retention tier new traces in the project are stored under.",
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
# (:LangSmithWorkspace)-[:CONTAINS]->(:LangSmithProject)
class LangSmithProjectToWorkspaceRel(CartographyRelSchema):
    """Links a tracing project to the workspace it belongs to."""

    target_node_label: str = "LangSmithWorkspace"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("workspace_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "CONTAINS"
    properties: LangSmithProjectToWorkspaceRelProperties = (
        LangSmithProjectToWorkspaceRelProperties()
    )


@dataclass(frozen=True)
class LangSmithProjectToResourceTagRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:LangSmithProject)-[:TAGGED]->(:LangSmithResourceTag)
class LangSmithProjectToResourceTagRel(CartographyRelSchema):
    """
    A resource tag applied to the project. Attribute-based access policies with a
    resource_tag_key condition match on these tags.
    """

    target_node_label: str = "LangSmithResourceTag"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("tag_value_ids", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "TAGGED"
    properties: LangSmithProjectToResourceTagRelProperties = (
        LangSmithProjectToResourceTagRelProperties()
    )


@dataclass(frozen=True)
class LangSmithProjectSchema(CartographyNodeSchema):
    """
    A tracing project, which holds the traces whose read access attribute-based access
    policies restrict. Experiments are not included.
    """

    label: str = "LangSmithProject"
    properties: LangSmithProjectNodeProperties = LangSmithProjectNodeProperties()
    sub_resource_relationship: LangSmithProjectToOrganizationRel = (
        LangSmithProjectToOrganizationRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            LangSmithProjectToWorkspaceRel(),
            LangSmithProjectToResourceTagRel(),
        ],
    )
