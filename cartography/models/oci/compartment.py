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
class OCICompartmentNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    ocid: PropertyRef = PropertyRef("id", extra_index=True)
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef("name", extra_index=True)
    description: PropertyRef = PropertyRef("description")
    compartmentid: PropertyRef = PropertyRef("compartment_id")
    createdate: PropertyRef = PropertyRef("time_created")


@dataclass(frozen=True)
class OCICompartmentToOCITenancyRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class OCICompartmentToOCITenancyRel(CartographyRelSchema):
    target_node_label: str = "OCITenancy"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"ocid": PropertyRef("OCI_TENANCY_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: OCICompartmentToOCITenancyRelProperties = (
        OCICompartmentToOCITenancyRelProperties()
    )


# Relationship for nested compartments to link to parent compartment
@dataclass(frozen=True)
class OCICompartmentToParentCompartmentRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class OCICompartmentToParentCompartmentRel(CartographyRelSchema):
    target_node_label: str = "OCICompartment"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"ocid": PropertyRef("compartment_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "PARENT"
    properties: OCICompartmentToParentCompartmentRelProperties = (
        OCICompartmentToParentCompartmentRelProperties()
    )


# Deprecated: OCI_COMPARTMENT relationship for backward compatibility
@dataclass(frozen=True)
class OCICompartmentToParentRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


# Deprecated: OCI_COMPARTMENT relationship for backward compatibility (tenancy)
@dataclass(frozen=True)
class OCICompartmentToTenancyParentRel(CartographyRelSchema):
    """
    Deprecated: This relationship is kept for backward compatibility.
    Links root compartments to tenancy via compartment_id.
    For parent-child compartment traversal, use the PARENT relationship instead.
    """

    target_node_label: str = "OCITenancy"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"ocid": PropertyRef("compartment_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "OCI_COMPARTMENT"
    properties: OCICompartmentToParentRelProperties = (
        OCICompartmentToParentRelProperties()
    )


# OCI_COMPARTMENT relationship to parent compartment
@dataclass(frozen=True)
class OCICompartmentToCompartmentParentRel(CartographyRelSchema):
    """
    Links nested compartments to parent compartment via compartment_id.
    """

    target_node_label: str = "OCICompartment"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"ocid": PropertyRef("compartment_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "OCI_COMPARTMENT"
    properties: OCICompartmentToParentRelProperties = (
        OCICompartmentToParentRelProperties()
    )


@dataclass(frozen=True)
class OCICompartmentSchema(CartographyNodeSchema):
    label: str = "OCICompartment"
    properties: OCICompartmentNodeProperties = OCICompartmentNodeProperties()
    sub_resource_relationship: OCICompartmentToOCITenancyRel = (
        OCICompartmentToOCITenancyRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            OCICompartmentToParentCompartmentRel(),  # Parent-child compartment hierarchy
            OCICompartmentToTenancyParentRel(),  # Deprecated: replaced by RESOURCE
            OCICompartmentToCompartmentParentRel(),  # OCI_COMPARTMENT to parent compartment
        ],
    )
