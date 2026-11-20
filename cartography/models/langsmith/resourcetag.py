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
from cartography.models.ontology.labels import TAG


@dataclass(frozen=True)
class LangSmithResourceTagNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", description="Tag value UUID.")
    key: PropertyRef = PropertyRef("key", extra_index=True, description="Tag key name.")
    value: PropertyRef = PropertyRef("value", description="Tag value.")
    key_id: PropertyRef = PropertyRef(
        "key_id", description="UUID of the tag key this value belongs to."
    )
    workspace_id: PropertyRef = PropertyRef(
        "workspace_id", description="UUID of the workspace the tag is defined in."
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class LangSmithResourceTagToWorkspaceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:LangSmithWorkspace)-[:RESOURCE]->(:LangSmithResourceTag)
class LangSmithResourceTagToWorkspaceRel(CartographyRelSchema):
    """Links a resource tag to the workspace it belongs to."""

    target_node_label: str = "LangSmithWorkspace"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("WORKSPACE_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: LangSmithResourceTagToWorkspaceRelProperties = (
        LangSmithResourceTagToWorkspaceRelProperties()
    )


@dataclass(frozen=True)
class LangSmithResourceTagSchema(CartographyNodeSchema):
    """
    A workspace resource tag. Tags are the attributes that attribute-based access policies
    match on.

    Cartography doesn't ingest the tagging edges that attach these tags to individual
    projects, datasets, and prompts, because those resource types are outside this module's
    scope.
    """

    label: str = "LangSmithResourceTag"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(
        [TAG]
    )  # Tag label is used for ontology mapping
    properties: LangSmithResourceTagNodeProperties = (
        LangSmithResourceTagNodeProperties()
    )
    sub_resource_relationship: LangSmithResourceTagToWorkspaceRel = (
        LangSmithResourceTagToWorkspaceRel()
    )
