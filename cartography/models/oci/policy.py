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
class OCIPolicyNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    ocid: PropertyRef = PropertyRef("id", extra_index=True)
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef("name")
    description: PropertyRef = PropertyRef("description")
    compartmentid: PropertyRef = PropertyRef("compartment_id")
    statements: PropertyRef = PropertyRef("statements")
    createdate: PropertyRef = PropertyRef("time_created")
    updatedate: PropertyRef = PropertyRef("version_date")


@dataclass(frozen=True)
class OCIPolicyToOCITenancyRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class OCIPolicyToOCITenancyRel(CartographyRelSchema):
    target_node_label: str = "OCITenancy"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"ocid": PropertyRef("OCI_TENANCY_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: OCIPolicyToOCITenancyRelProperties = (
        OCIPolicyToOCITenancyRelProperties()
    )


# DEPRECATED: OCI_POLICY relationship for backward compatibility
@dataclass(frozen=True)
class OCIPolicyToParentRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


# DEPRECATED: OCI_POLICY relationship for backward compatibility (tenancy)
@dataclass(frozen=True)
class OCIPolicyToTenancyParentRel(CartographyRelSchema):
    """
    DEPRECATED: This relationship is kept for backward compatibility.
    Links policies to tenancy via compartment_id (for policies at tenancy level).
    """

    target_node_label: str = "OCITenancy"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"ocid": PropertyRef("compartment_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "OCI_POLICY"
    properties: OCIPolicyToParentRelProperties = OCIPolicyToParentRelProperties()


# OCI_POLICY relationship to parent compartment
@dataclass(frozen=True)
class OCIPolicyToCompartmentParentRel(CartographyRelSchema):
    """
    Links policies to compartment via compartment_id (for policies at compartment level).
    """

    target_node_label: str = "OCICompartment"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"ocid": PropertyRef("compartment_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "OCI_POLICY"
    properties: OCIPolicyToParentRelProperties = OCIPolicyToParentRelProperties()


@dataclass(frozen=True)
class OCIPolicyRefNodeProperties(CartographyNodeProperties):
    """
    Node properties for policy references schema.
    Uses 'ocid' as data source since data comes from Neo4j queries.
    """

    id: PropertyRef = PropertyRef("ocid")
    ocid: PropertyRef = PropertyRef("ocid", extra_index=True)
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef("name")
    compartmentid: PropertyRef = PropertyRef("compartmentid")
    statements: PropertyRef = PropertyRef("statements")


@dataclass(frozen=True)
class OCIPolicyToGroupRefRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class OCIPolicyToGroupRefRel(CartographyRelSchema):
    """
    Relationship: (OCIPolicy)-[:OCI_POLICY_REFERENCE]->(OCIGroup)
    Derived from parsing policy statements that reference groups.
    """

    target_node_label: str = "OCIGroup"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"ocid": PropertyRef("referenced_group_ids", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "OCI_POLICY_REFERENCE"
    properties: OCIPolicyToGroupRefRelProperties = OCIPolicyToGroupRefRelProperties()


@dataclass(frozen=True)
class OCIPolicyToCompartmentRefRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class OCIPolicyToCompartmentRefRel(CartographyRelSchema):
    """
    Relationship: (OCIPolicy)-[:OCI_POLICY_REFERENCE]->(OCICompartment)
    Derived from parsing policy statements that reference compartments.
    """

    target_node_label: str = "OCICompartment"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"ocid": PropertyRef("referenced_compartment_ids", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "OCI_POLICY_REFERENCE"
    properties: OCIPolicyToCompartmentRefRelProperties = (
        OCIPolicyToCompartmentRefRelProperties()
    )


@dataclass(frozen=True)
class OCIPolicySchema(CartographyNodeSchema):
    label: str = "OCIPolicy"
    properties: OCIPolicyNodeProperties = OCIPolicyNodeProperties()
    sub_resource_relationship: OCIPolicyToOCITenancyRel = OCIPolicyToOCITenancyRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            OCIPolicyToTenancyParentRel(),  # Deprecated: replaced by RESOURCE
            OCIPolicyToCompartmentParentRel(),  # OCI_POLICY to parent compartment
        ],
    )


@dataclass(frozen=True)
class OCIPolicyWithReferencesSchema(CartographyNodeSchema):
    """
    Schema for loading policies with their semantic references to groups and compartments.
    Used when syncing policy references derived from parsing policy statements.
    Uses OCIPolicyRefNodeProperties since data comes from Neo4j queries (with 'ocid' field).
    """

    label: str = "OCIPolicy"
    properties: OCIPolicyRefNodeProperties = OCIPolicyRefNodeProperties()
    sub_resource_relationship: OCIPolicyToOCITenancyRel = OCIPolicyToOCITenancyRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            OCIPolicyToGroupRefRel(),
            OCIPolicyToCompartmentRefRel(),
        ],
    )
