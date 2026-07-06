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


@dataclass(frozen=True)
class CircleCIGroupNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef("name", extra_index=True)
    description: PropertyRef = PropertyRef("description")


@dataclass(frozen=True)
class CircleCIGroupToOrganizationRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:CircleCIOrganization)-[:RESOURCE]->(:CircleCIGroup)
class CircleCIGroupToOrganizationRel(CartographyRelSchema):
    target_node_label: str = "CircleCIOrganization"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ORG_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: CircleCIGroupToOrganizationRelProperties = (
        CircleCIGroupToOrganizationRelProperties()
    )


@dataclass(frozen=True)
class CircleCIGroupSchema(CartographyNodeSchema):
    label: str = "CircleCIGroup"
    properties: CircleCIGroupNodeProperties = CircleCIGroupNodeProperties()
    # UserGroup label maps this node into the ontology alongside other org groups
    # (GitLabGroup, EntraGroup, GoogleWorkspaceGroup, ...).
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["UserGroup"])
    sub_resource_relationship: CircleCIGroupToOrganizationRel = (
        CircleCIGroupToOrganizationRel()
    )
