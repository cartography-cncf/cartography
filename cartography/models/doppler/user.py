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
class DopplerWorkplaceUserNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    access: PropertyRef = PropertyRef("access")
    email: PropertyRef = PropertyRef("email", extra_index=True)
    name: PropertyRef = PropertyRef("name")
    username: PropertyRef = PropertyRef("username")
    profile_image_url: PropertyRef = PropertyRef("profile_image_url")
    created_at: PropertyRef = PropertyRef("created_at")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class DopplerWorkplaceUserToWorkplaceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:DopplerWorkplace)-[:RESOURCE]->(:DopplerWorkplaceUser)
class DopplerWorkplaceUserToWorkplaceRel(CartographyRelSchema):
    target_node_label: str = "DopplerWorkplace"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("WORKPLACE_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: DopplerWorkplaceUserToWorkplaceRelProperties = (
        DopplerWorkplaceUserToWorkplaceRelProperties()
    )


@dataclass(frozen=True)
class DopplerWorkplaceUserSchema(CartographyNodeSchema):
    label: str = "DopplerWorkplaceUser"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(
        ["UserAccount"]
    )  # UserAccount label is used for ontology mapping
    properties: DopplerWorkplaceUserNodeProperties = (
        DopplerWorkplaceUserNodeProperties()
    )
    sub_resource_relationship: DopplerWorkplaceUserToWorkplaceRel = (
        DopplerWorkplaceUserToWorkplaceRel()
    )
