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
    id: PropertyRef = PropertyRef("id", description="OCI compartment OCID.")
    ocid: PropertyRef = PropertyRef(
        "id", extra_index=True, description="OCI compartment OCID."
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last update.",
    )
    name: PropertyRef = PropertyRef(
        "name", extra_index=True, description="Compartment name."
    )
    description: PropertyRef = PropertyRef(
        "description", description="Compartment description."
    )
    compartmentid: PropertyRef = PropertyRef(
        "compartment_id", description="OCID of the parent compartment or tenancy."
    )
    createdate: PropertyRef = PropertyRef(
        "time_created", description="Date and time when the compartment was created."
    )


@dataclass(frozen=True)
class OCICompartmentToOCITenancyRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class OCICompartmentToOCITenancyRel(CartographyRelSchema):
    """An OCI tenancy contains a compartment as a managed resource."""

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
    """An OCI compartment points to its parent compartment."""

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
    """Deprecated compatibility edge from an OCI tenancy to a root compartment."""

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
    """Compatibility edge from a parent OCI compartment to a nested compartment."""

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
    """An OCI compartment linked to its tenancy and parent hierarchy."""

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
