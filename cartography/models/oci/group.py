from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import OtherRelationships
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class OCIGroupNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", description="OCI group OCID.")
    ocid: PropertyRef = PropertyRef(
        "id", extra_index=True, description="OCI group OCID."
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last update.",
    )
    name: PropertyRef = PropertyRef("name", description="Group name.")
    description: PropertyRef = PropertyRef(
        "description", description="Group description."
    )
    compartmentid: PropertyRef = PropertyRef(
        "compartment_id", description="OCID of the tenancy containing the group."
    )
    createdate: PropertyRef = PropertyRef(
        "time_created", description="Date and time when the group was created."
    )


@dataclass(frozen=True)
class OCIGroupToOCITenancyRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class OCIGroupToOCITenancyRel(CartographyRelSchema):
    """An OCI tenancy contains a group as a managed resource."""

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
# DEPRECATED: replaced by the canonical (:UserAccount)-[:MEMBER_OF]->(:UserGroup)
# edge (OCIGroupToOCIUserMemberOfRel). Kept for backward compatibility, will be
# removed in v1.0.0.
class OCIGroupToOCIUserRel(CartographyRelSchema):
    """Deprecated compatibility edge from an OCI user to an OCI group."""

    target_node_label: str = "OCIUser"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"ocid": PropertyRef("user_ids", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "MEMBER_OCID_GROUP"
    properties: OCIGroupToOCIUserRelProperties = OCIGroupToOCIUserRelProperties()


@dataclass(frozen=True)
class OCIGroupToOCIUserMemberOfRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# Canonical ontology edge: (:UserAccount)-[:MEMBER_OF]->(:UserGroup)
class OCIGroupToOCIUserMemberOfRel(CartographyRelSchema):
    """Canonical edge from an OCI user account to an OCI user group."""

    target_node_label: str = "OCIUser"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"ocid": PropertyRef("user_ids", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "MEMBER_OF"
    properties: OCIGroupToOCIUserMemberOfRelProperties = (
        OCIGroupToOCIUserMemberOfRelProperties()
    )


@dataclass(frozen=True)
class OCIGroupSchema(CartographyNodeSchema):
    """An OCI user group with the UserGroup label."""

    label: str = "OCIGroup"
    properties: OCIGroupNodeProperties = OCIGroupNodeProperties()
    sub_resource_relationship: OCIGroupToOCITenancyRel = OCIGroupToOCITenancyRel()
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["UserGroup"])


@dataclass(frozen=True)
class OCIGroupWithMembersSchema(CartographyNodeSchema):
    """An OCI user group with the UserGroup label."""

    label: str = "OCIGroup"
    properties: OCIGroupNodeProperties = OCIGroupNodeProperties()
    sub_resource_relationship: OCIGroupToOCITenancyRel = OCIGroupToOCITenancyRel()
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["UserGroup"])
    other_relationships: OtherRelationships = OtherRelationships(
        [OCIGroupToOCIUserRel(), OCIGroupToOCIUserMemberOfRel()],
    )
