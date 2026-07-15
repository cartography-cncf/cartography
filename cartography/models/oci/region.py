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
    id: PropertyRef = PropertyRef("region_key", description="OCI region key.")
    key: PropertyRef = PropertyRef(
        "region_key", extra_index=True, description="OCI region key."
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last update.",
    )
    name: PropertyRef = PropertyRef(
        "region_name", extra_index=True, description="OCI region name."
    )


@dataclass(frozen=True)
class OCIRegionToOCITenancyRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class OCIRegionToOCITenancyRel(CartographyRelSchema):
    """An OCI tenancy contains a subscribed region as a managed resource."""

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
    """Deprecated compatibility edge from an OCI tenancy to a subscribed region."""

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
    """An OCI region subscribed by a tenancy."""

    label: str = "OCIRegion"
    properties: OCIRegionNodeProperties = OCIRegionNodeProperties()
    sub_resource_relationship: OCIRegionToOCITenancyRel = OCIRegionToOCITenancyRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [OCIRegionSubscriptionRel()],  # DEPRECATED: for backward compatibility
    )
