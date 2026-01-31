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
class OCIGroupNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    ocid: PropertyRef = PropertyRef("id", extra_index=True)
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef("name")
    description: PropertyRef = PropertyRef("description")
    compartmentid: PropertyRef = PropertyRef("compartment_id")
    createdate: PropertyRef = PropertyRef("time_created")


@dataclass(frozen=True)
class OCIGroupToOCITenancyRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class OCIGroupToOCITenancyRel(CartographyRelSchema):
    target_node_label: str = "OCITenancy"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"ocid": PropertyRef("OCI_TENANCY_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: OCIGroupToOCITenancyRelProperties = OCIGroupToOCITenancyRelProperties()


@dataclass(frozen=True)
class OCIGroupToOCIUserRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class OCIGroupToOCIUserRel(CartographyRelSchema):
    """
    Relationship: (OCIUser)-[:MEMBER_OCID_GROUP]->(OCIGroup)
    """

    target_node_label: str = "OCIUser"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"ocid": PropertyRef("user_ids", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "MEMBER_OCID_GROUP"
    properties: OCIGroupToOCIUserRelProperties = OCIGroupToOCIUserRelProperties()


@dataclass(frozen=True)
class OCIGroupSchema(CartographyNodeSchema):
    label: str = "OCIGroup"
    properties: OCIGroupNodeProperties = OCIGroupNodeProperties()
    sub_resource_relationship: OCIGroupToOCITenancyRel = OCIGroupToOCITenancyRel()


@dataclass(frozen=True)
class OCIGroupWithMembersSchema(CartographyNodeSchema):
    """
    Schema for loading groups with user memberships.
    This is used when we want to load the group-user relationships.
    """

    label: str = "OCIGroup"
    properties: OCIGroupNodeProperties = OCIGroupNodeProperties()
    sub_resource_relationship: OCIGroupToOCITenancyRel = OCIGroupToOCITenancyRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [OCIGroupToOCIUserRel()],
    )
