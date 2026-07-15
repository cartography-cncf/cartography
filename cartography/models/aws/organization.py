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
    id: PropertyRef = PropertyRef("id", description="The AWS Organization ID.")
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last time the node was updated.",
    )
    arn: PropertyRef = PropertyRef(
        "arn", extra_index=True, description="The AWS Organization ARN."
    )
    feature_set: PropertyRef = PropertyRef(
        "feature_set",
        description="The feature set of the organization, such as `ALL` or `CONSOLIDATED_BILLING`.",
    )
    management_account_arn: PropertyRef = PropertyRef(
        "management_account_arn",
        description="The ARN of the organization's management account.",
    )
    management_account_id: PropertyRef = PropertyRef(
        "management_account_id",
        extra_index=True,
        description="The ID of the organization's management account.",
    )
    management_account_email: PropertyRef = PropertyRef(
        "management_account_email",
        description="The email address of the organization's management account.",
    )


@dataclass(frozen=True)
class AWSOrganizationSchema(CartographyNodeSchema):
    "Represents an `AWSOrganization` node in the AWS graph."

    label: str = "AWSOrganization"
    properties: AWSOrganizationNodeProperties = AWSOrganizationNodeProperties()
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["Tenant"])


@dataclass(frozen=True)
class AWSOrganizationRootToOrganizationRel(CartographyRelSchema):
    "Represents a `RESOURCE` relationship from `AWSOrganization` to `AWSOrganizationRoot`."

    target_node_label: str = "AWSOrganization"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ORG_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: AWSOrganizationRelProperties = AWSOrganizationRelProperties()


@dataclass(frozen=True)
class AWSOrganizationRootToOrganizationParentRel(CartographyRelSchema):
    "Represents a `PARENT` relationship from `AWSOrganizationRoot` to `AWSOrganization`."

    target_node_label: str = "AWSOrganization"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ORG_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "PARENT"
    properties: AWSOrganizationRelProperties = AWSOrganizationRelProperties()


@dataclass(frozen=True)
class AWSOrganizationRootToChildOURel(CartographyRelSchema):
    "Represents a `RESOURCE` relationship from `AWSOrganizationRoot` to `AWSOrganizationalUnit`."

    target_node_label: str = "AWSOrganizationalUnit"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("child_ou_ids", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "RESOURCE"
    properties: AWSOrganizationRelProperties = AWSOrganizationRelProperties()


@dataclass(frozen=True)
class AWSOrganizationRootToChildAWSAccountResourceRel(CartographyRelSchema):
    "Represents a `RESOURCE` relationship from `AWSOrganizationRoot` to `AWSAccount`."

    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("account_ids", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "RESOURCE"
    properties: AWSOrganizationRelProperties = AWSOrganizationRelProperties()


@dataclass(frozen=True)
class AWSAccountToOrganizationRootParentRel(CartographyRelSchema):
    "Represents a `PARENT` relationship from `AWSAccount` to `AWSOrganizationRoot`."

    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("account_ids", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "PARENT"
    properties: AWSOrganizationRelProperties = AWSOrganizationRelProperties()


@dataclass(frozen=True)
class AWSOrganizationRootNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id",
        description="Cartography ID for this root, formatted as `{org_id}/{root_id}` because AWS root IDs are unique only within an organization.",
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last time the node was updated.",
    )
    root_id: PropertyRef = PropertyRef(
        "root_id", extra_index=True, description="The raw AWS Organizations root ID."
    )
    arn: PropertyRef = PropertyRef(
        "arn", extra_index=True, description="The AWS Organizations root ARN."
    )
    name: PropertyRef = PropertyRef(
        "name", description="The AWS Organizations root name."
    )
    org_id: PropertyRef = PropertyRef(
        "org_id", extra_index=True, description="The AWS Organization ID."
    )


@dataclass(frozen=True)
class AWSOrganizationRootSchema(CartographyNodeSchema):
    "Represents an `AWSOrganizationRoot` node in the AWS graph."

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
    "Represents a `RESOURCE` relationship from `AWSOrganizationRoot` to `AWSOrganizationalUnit`."

    target_node_label: str = "AWSOrganizationRoot"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ROOT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: AWSOrganizationRelProperties = AWSOrganizationRelProperties()


@dataclass(frozen=True)
class AWSOrganizationalUnitToRootParentRel(CartographyRelSchema):
    "Represents a `PARENT` relationship from `AWSOrganizationalUnit` to `AWSOrganizationRoot`."

    target_node_label: str = "AWSOrganizationRoot"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("parent_root_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "PARENT"
    properties: AWSOrganizationRelProperties = AWSOrganizationRelProperties()


@dataclass(frozen=True)
class AWSOrganizationalUnitToOUParentRel(CartographyRelSchema):
    "Represents a `PARENT` relationship from `AWSOrganizationalUnit` to `AWSOrganizationalUnit`."

    target_node_label: str = "AWSOrganizationalUnit"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("parent_ou_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "PARENT"
    properties: AWSOrganizationRelProperties = AWSOrganizationRelProperties()


@dataclass(frozen=True)
class AWSOrganizationalUnitToChildOURel(CartographyRelSchema):
    "Represents a `RESOURCE` relationship from `AWSOrganizationalUnit` to `AWSOrganizationalUnit`."

    target_node_label: str = "AWSOrganizationalUnit"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("child_ou_ids", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "RESOURCE"
    properties: AWSOrganizationRelProperties = AWSOrganizationRelProperties()


@dataclass(frozen=True)
class AWSOrganizationalUnitToChildAWSAccountResourceRel(CartographyRelSchema):
    "Represents a `RESOURCE` relationship from `AWSOrganizationalUnit` to `AWSAccount`."

    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("account_ids", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "RESOURCE"
    properties: AWSOrganizationRelProperties = AWSOrganizationRelProperties()


@dataclass(frozen=True)
class AWSAccountToOrganizationalUnitParentRel(CartographyRelSchema):
    "Represents a `PARENT` relationship from `AWSAccount` to `AWSOrganizationalUnit`."

    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("account_ids", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "PARENT"
    properties: AWSOrganizationRelProperties = AWSOrganizationRelProperties()


@dataclass(frozen=True)
class AWSOrganizationalUnitNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id",
        description="Cartography ID for this organizational unit, formatted as `{org_id}/{ou_id}` because AWS organizational unit IDs are unique only within an organization.",
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last time the node was updated.",
    )
    ou_id: PropertyRef = PropertyRef(
        "ou_id",
        extra_index=True,
        description="The raw AWS Organizations organizational unit ID.",
    )
    arn: PropertyRef = PropertyRef(
        "arn",
        extra_index=True,
        description="The AWS Organizations organizational unit ARN.",
    )
    name: PropertyRef = PropertyRef(
        "name", description="The AWS Organizations organizational unit name."
    )
    org_id: PropertyRef = PropertyRef(
        "org_id", extra_index=True, description="The AWS Organization ID."
    )
    root_id: PropertyRef = PropertyRef(
        "root_id",
        extra_index=True,
        description="The Cartography root ID that scopes the organizational unit, formatted as `{org_id}/{root_id}`.",
    )
    parent_root_id: PropertyRef = PropertyRef(
        "parent_root_id",
        description="The Cartography parent root ID, when the organizational unit is directly under a root.",
    )
    parent_ou_id: PropertyRef = PropertyRef(
        "parent_ou_id",
        description="The Cartography parent organizational unit ID, when the organizational unit is nested under another organizational unit.",
    )


@dataclass(frozen=True)
class AWSOrganizationalUnitSchema(CartographyNodeSchema):
    "Represents an `AWSOrganizationalUnit` node in the AWS graph."

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
