from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_source_node_matcher
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import MatchLinkSubResource
from cartography.models.core.relationships import OtherRelationships
from cartography.models.core.relationships import SourceNodeMatcher
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class IntuneDetectedAppNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    application_id: PropertyRef = PropertyRef("application_id")
    display_name: PropertyRef = PropertyRef("display_name")
    version: PropertyRef = PropertyRef("version")
    device_count: PropertyRef = PropertyRef("device_count")
    publisher: PropertyRef = PropertyRef("publisher")
    platform: PropertyRef = PropertyRef("platform")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class IntuneDetectedAppRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class IntuneManagedDeviceHasAppRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    _sub_resource_label: PropertyRef = PropertyRef(
        "_sub_resource_label",
        set_in_kwargs=True,
    )
    _sub_resource_id: PropertyRef = PropertyRef("_sub_resource_id", set_in_kwargs=True)


# (:IntuneDetectedApp)<-[:RESOURCE]-(:EntraTenant)
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
class IntuneManagedDeviceToDetectedAppMatchLink(CartographyRelSchema):
    target_node_label: str = "IntuneManagedDevice"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("device_id")},
    )
    source_node_label: str = "IntuneDetectedApp"
    source_node_matcher: SourceNodeMatcher = make_source_node_matcher(
        {"id": PropertyRef("app_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS_APP"
    properties: IntuneManagedDeviceHasAppRelProperties = (
        IntuneManagedDeviceHasAppRelProperties()
    )
    source_node_sub_resource: MatchLinkSubResource = MatchLinkSubResource(
        target_node_label="EntraTenant",
        target_node_matcher=make_target_node_matcher(
            {"id": PropertyRef("_sub_resource_id", set_in_kwargs=True)},
        ),
        direction=LinkDirection.INWARD,
        rel_label="RESOURCE",
    )
    target_node_sub_resource: MatchLinkSubResource = MatchLinkSubResource(
        target_node_label="EntraTenant",
        target_node_matcher=make_target_node_matcher(
            {"id": PropertyRef("_sub_resource_id", set_in_kwargs=True)},
        ),
        direction=LinkDirection.INWARD,
        rel_label="RESOURCE",
    )


@dataclass(frozen=True)
class IntuneDetectedAppSchema(CartographyNodeSchema):
    label: str = "IntuneDetectedApp"
    properties: IntuneDetectedAppNodeProperties = IntuneDetectedAppNodeProperties()
    sub_resource_relationship: IntuneDetectedAppToTenantRel = (
        IntuneDetectedAppToTenantRel()
    )
    other_relationships: OtherRelationships = OtherRelationships([])
