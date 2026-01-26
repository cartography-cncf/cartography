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


# Deprecated: OCI_COMPARTMENT relationship for backward compatibility
@dataclass(frozen=True)
class OCICompartmentToParentRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


# Deprecated: OCI_COMPARTMENT relationship for backward compatibility
@dataclass(frozen=True)
class OCICompartmentToParentRel(CartographyRelSchema):
    """
    Deprecated: This relationship is kept for backward compatibility.
    The parent can be either an OCITenancy or an OCICompartment (for nested compartments).
    We use the compartment_id field which points to the parent's OCID.
    """

    target_node_label: str = "OCITenancy"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"ocid": PropertyRef("OCI_TENANCY_ID", set_in_kwargs=True)},
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
        [OCICompartmentToParentRel()],  # Deprecated: for backward compatibility
    )
