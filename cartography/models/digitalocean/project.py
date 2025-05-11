from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class DOProjectNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    account_id: PropertyRef = PropertyRef("ACCOUNT_ID", set_in_kwargs=True)
    name: PropertyRef = PropertyRef("name")
    owner_uuid: PropertyRef = PropertyRef("owner_uuid")
    description: PropertyRef = PropertyRef("description")
    environment: PropertyRef = PropertyRef("environment")
    is_default: PropertyRef = PropertyRef("is_default")
    created_at: PropertyRef = PropertyRef("created_at")
    updated_at: PropertyRef = PropertyRef("updated_at")


@dataclass(frozen=True)
class DOProjectToAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:DOAccount)<-[:RESOURCE]-(:DOProject)
class DOProjectToAccountRel(CartographyRelSchema):
    target_node_label: str = "DOAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ACCOUNT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "RESOURCE"
    properties: DOProjectToAccountRelProperties = DOProjectToAccountRelProperties()


@dataclass(frozen=True)
class DOProjectSchema(CartographyNodeSchema):
    label: str = "DOProject"
    properties: DOProjectNodeProperties = DOProjectNodeProperties()
    sub_resource_relationship: DOProjectToAccountRel = DOProjectToAccountRel()
