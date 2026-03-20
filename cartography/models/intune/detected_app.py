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
class IntuneDetectedAppNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    display_name: PropertyRef = PropertyRef("display_name")
    version: PropertyRef = PropertyRef("version")
    size_in_byte: PropertyRef = PropertyRef("size_in_byte")
    device_count: PropertyRef = PropertyRef("device_count")
    publisher: PropertyRef = PropertyRef("publisher")
    platform: PropertyRef = PropertyRef("platform")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class IntuneDetectedAppRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


# (:IntuneDetectedApp)<-[:RESOURCE]-(:IntuneTenant)
@dataclass(frozen=True)
class IntuneDetectedAppToTenantRel(CartographyRelSchema):
    target_node_label: str = "EntraTenant"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("TENANT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: IntuneDetectedAppRelProperties = IntuneDetectedAppRelProperties()


# (:IntuneManagedDevice)-[:HAS_APP]->(:IntuneDetectedApp)
@dataclass(frozen=True)
class IntuneDetectedAppToManagedDeviceRel(CartographyRelSchema):
    target_node_label: str = "IntuneManagedDevice"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("device_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS_APP"
    properties: IntuneDetectedAppRelProperties = IntuneDetectedAppRelProperties()


@dataclass(frozen=True)
class IntuneDetectedAppSchema(CartographyNodeSchema):
    label: str = "IntuneDetectedApp"
    properties: IntuneDetectedAppNodeProperties = IntuneDetectedAppNodeProperties()
    sub_resource_relationship: IntuneDetectedAppToTenantRel = (
        IntuneDetectedAppToTenantRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            IntuneDetectedAppToManagedDeviceRel(),
        ],
    )
