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
class OCIRegionNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("region_key")
    key: PropertyRef = PropertyRef("region_key", extra_index=True)
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef("region_name", extra_index=True)


@dataclass(frozen=True)
class OCIRegionToOCITenancyRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class OCIRegionToOCITenancyRel(CartographyRelSchema):
    target_node_label: str = "OCITenancy"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"ocid": PropertyRef("OCI_TENANCY_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: OCIRegionToOCITenancyRelProperties = (
        OCIRegionToOCITenancyRelProperties()
    )


# DEPRECATED: OCI_REGION_SUBSCRIPTION relationship for backward compatibility
@dataclass(frozen=True)
class OCIRegionSubscriptionRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


# DEPRECATED: OCI_REGION_SUBSCRIPTION relationship for backward compatibility
@dataclass(frozen=True)
class OCIRegionSubscriptionRel(CartographyRelSchema):
    """
    Deprecated: This relationship is kept for backward compatibility.
    """

    target_node_label: str = "OCITenancy"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"ocid": PropertyRef("OCI_TENANCY_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "OCI_REGION_SUBSCRIPTION"
    properties: OCIRegionSubscriptionRelProperties = (
        OCIRegionSubscriptionRelProperties()
    )


@dataclass(frozen=True)
class OCIRegionSchema(CartographyNodeSchema):
    label: str = "OCIRegion"
    properties: OCIRegionNodeProperties = OCIRegionNodeProperties()
    sub_resource_relationship: OCIRegionToOCITenancyRel = OCIRegionToOCITenancyRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [OCIRegionSubscriptionRel()],  # DEPRECATED: for backward compatibility
    )
