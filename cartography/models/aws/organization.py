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
class AWSOrganizationRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AWSOrganizationNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    arn: PropertyRef = PropertyRef("arn", extra_index=True)
    feature_set: PropertyRef = PropertyRef("feature_set")
    management_account_arn: PropertyRef = PropertyRef("management_account_arn")
    management_account_id: PropertyRef = PropertyRef(
        "management_account_id",
        extra_index=True,
    )
    management_account_email: PropertyRef = PropertyRef("management_account_email")


@dataclass(frozen=True)
class AWSOrganizationSchema(CartographyNodeSchema):
    label: str = "AWSOrganization"
    properties: AWSOrganizationNodeProperties = AWSOrganizationNodeProperties()
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["Tenant"])


@dataclass(frozen=True)
class AWSOrganizationRootToOrganizationRel(CartographyRelSchema):
    target_node_label: str = "AWSOrganization"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ORG_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: AWSOrganizationRelProperties = AWSOrganizationRelProperties()


@dataclass(frozen=True)
class AWSOrganizationRootToOrganizationParentRel(CartographyRelSchema):
    target_node_label: str = "AWSOrganization"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ORG_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "PARENT"
    properties: AWSOrganizationRelProperties = AWSOrganizationRelProperties()


@dataclass(frozen=True)
class AWSOrganizationRootToChildOURel(CartographyRelSchema):
    target_node_label: str = "AWSOrganizationalUnit"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("child_ou_ids", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "RESOURCE"
    properties: AWSOrganizationRelProperties = AWSOrganizationRelProperties()


@dataclass(frozen=True)
class AWSOrganizationRootToChildAWSAccountResourceRel(CartographyRelSchema):
    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("account_ids", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "RESOURCE"
    properties: AWSOrganizationRelProperties = AWSOrganizationRelProperties()


@dataclass(frozen=True)
class AWSAccountToOrganizationRootParentRel(CartographyRelSchema):
    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("account_ids", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "PARENT"
    properties: AWSOrganizationRelProperties = AWSOrganizationRelProperties()


@dataclass(frozen=True)
class AWSOrganizationRootNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    root_id: PropertyRef = PropertyRef("root_id", extra_index=True)
    arn: PropertyRef = PropertyRef("arn", extra_index=True)
    name: PropertyRef = PropertyRef("name")
    org_id: PropertyRef = PropertyRef("org_id", extra_index=True)


@dataclass(frozen=True)
class AWSOrganizationRootSchema(CartographyNodeSchema):
    label: str = "AWSOrganizationRoot"
    properties: AWSOrganizationRootNodeProperties = AWSOrganizationRootNodeProperties()
    sub_resource_relationship: AWSOrganizationRootToOrganizationRel = (
        AWSOrganizationRootToOrganizationRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            AWSOrganizationRootToOrganizationParentRel(),
            AWSOrganizationRootToChildOURel(),
            AWSOrganizationRootToChildAWSAccountResourceRel(),
            AWSAccountToOrganizationRootParentRel(),
        ],
    )


@dataclass(frozen=True)
class AWSOrganizationalUnitToRootRel(CartographyRelSchema):
    target_node_label: str = "AWSOrganizationRoot"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ROOT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: AWSOrganizationRelProperties = AWSOrganizationRelProperties()


@dataclass(frozen=True)
class AWSOrganizationalUnitToRootParentRel(CartographyRelSchema):
    target_node_label: str = "AWSOrganizationRoot"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("parent_root_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "PARENT"
    properties: AWSOrganizationRelProperties = AWSOrganizationRelProperties()


@dataclass(frozen=True)
class AWSOrganizationalUnitToOUParentRel(CartographyRelSchema):
    target_node_label: str = "AWSOrganizationalUnit"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("parent_ou_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "PARENT"
    properties: AWSOrganizationRelProperties = AWSOrganizationRelProperties()


@dataclass(frozen=True)
class AWSOrganizationalUnitToChildOURel(CartographyRelSchema):
    target_node_label: str = "AWSOrganizationalUnit"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("child_ou_ids", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "RESOURCE"
    properties: AWSOrganizationRelProperties = AWSOrganizationRelProperties()


@dataclass(frozen=True)
class AWSOrganizationalUnitToChildAWSAccountResourceRel(CartographyRelSchema):
    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("account_ids", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "RESOURCE"
    properties: AWSOrganizationRelProperties = AWSOrganizationRelProperties()


@dataclass(frozen=True)
class AWSAccountToOrganizationalUnitParentRel(CartographyRelSchema):
    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("account_ids", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "PARENT"
    properties: AWSOrganizationRelProperties = AWSOrganizationRelProperties()


@dataclass(frozen=True)
class AWSOrganizationalUnitNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    ou_id: PropertyRef = PropertyRef("ou_id", extra_index=True)
    arn: PropertyRef = PropertyRef("arn", extra_index=True)
    name: PropertyRef = PropertyRef("name")
    org_id: PropertyRef = PropertyRef("org_id", extra_index=True)
    root_id: PropertyRef = PropertyRef("root_id", extra_index=True)
    parent_root_id: PropertyRef = PropertyRef("parent_root_id")
    parent_ou_id: PropertyRef = PropertyRef("parent_ou_id")


@dataclass(frozen=True)
class AWSOrganizationalUnitSchema(CartographyNodeSchema):
    label: str = "AWSOrganizationalUnit"
    properties: AWSOrganizationalUnitNodeProperties = (
        AWSOrganizationalUnitNodeProperties()
    )
    sub_resource_relationship: AWSOrganizationalUnitToRootRel = (
        AWSOrganizationalUnitToRootRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            AWSOrganizationalUnitToRootParentRel(),
            AWSOrganizationalUnitToOUParentRel(),
            AWSOrganizationalUnitToChildOURel(),
            AWSOrganizationalUnitToChildAWSAccountResourceRel(),
            AWSAccountToOrganizationalUnitParentRel(),
        ],
    )
