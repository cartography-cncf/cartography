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
class AWSSSOGroupProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("GroupId")
    display_name: PropertyRef = PropertyRef("DisplayName")
    description: PropertyRef = PropertyRef("Description")
    identity_store_id: PropertyRef = PropertyRef("IdentityStoreId")
    external_id: PropertyRef = PropertyRef("ExternalId", extra_index=True)
    region: PropertyRef = PropertyRef("Region", set_in_kwargs=True)
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AWSSSOGroupToAWSAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AWSSSOGroupToAWSAccountRel(CartographyRelSchema):
    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AWS_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: AWSSSOGroupToAWSAccountRelProperties = (
        AWSSSOGroupToAWSAccountRelProperties()
    )


@dataclass(frozen=True)
class AWSSSOGroupToPermissionSetRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AWSSSOGroupToPermissionSetRel(CartographyRelSchema):
    target_node_label: str = "AWSPermissionSet"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"arn": PropertyRef("AssignedPermissionSets", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "HAS_PERMISSION_SET"
    properties: AWSSSOGroupToPermissionSetRelProperties = (
        AWSSSOGroupToPermissionSetRelProperties()
    )


@dataclass(frozen=True)
class AWSSSOGroupSchema(CartographyNodeSchema):
    label: str = "AWSSSOGroup"
    properties: AWSSSOGroupProperties = AWSSSOGroupProperties()
    sub_resource_relationship: AWSSSOGroupToAWSAccountRel = AWSSSOGroupToAWSAccountRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            AWSSSOGroupToPermissionSetRel(),
        ]
    )
