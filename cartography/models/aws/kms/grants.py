from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties, CartographyNodeSchema
from cartography.models.core.relationships import (
    CartographyRelProperties,
    CartographyRelSchema,
    LinkDirection,
    make_target_node_matcher,
    OtherRelationships,
    TargetNodeMatcher,
)


@dataclass(frozen=True)
class KMSGrantNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("GrantId")
    grant_id: PropertyRef = PropertyRef("GrantId", extra_index=True)
    name: PropertyRef = PropertyRef("Name")
    grantee_principal: PropertyRef = PropertyRef("GranteePrincipal")
    creation_date: PropertyRef = PropertyRef("CreationDate")
    key_id: PropertyRef = PropertyRef("KeyId")
    issuing_account: PropertyRef = PropertyRef("IssuingAccount")
    operations: PropertyRef = PropertyRef("Operations")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class KMSGrantRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class KMSGrantToKMSKeyRel(CartographyRelSchema):
    target_node_label: str = "KMSKey"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher({"arn": PropertyRef("KeyId")})
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "APPLIED_ON"
    properties: KMSGrantRelProperties = KMSGrantRelProperties()


@dataclass(frozen=True)
class KMSGrantSchema(CartographyNodeSchema):
    label: str = "KMSGrant"
    properties: KMSGrantNodeProperties = KMSGrantNodeProperties()
    sub_resource_relationship: None = None #rel between grants and keys so no sub resource relationship necessary
    other_relationships: OtherRelationships = OtherRelationships([KMSGrantToKMSKeyRel()]) 