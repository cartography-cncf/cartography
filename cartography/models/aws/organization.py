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
class AWSOrganizationToAWSAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AWSOrganizationToSyncingAWSAccountRel(CartographyRelSchema):
    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AWS_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: AWSOrganizationToAWSAccountRelProperties = (
        AWSOrganizationToAWSAccountRelProperties()
    )


@dataclass(frozen=True)
class AWSMemberAWSAccountToOrganizationParentRel(CartographyRelSchema):
    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("account_ids", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "PARENT"
    properties: AWSOrganizationToAWSAccountRelProperties = (
        AWSOrganizationToAWSAccountRelProperties()
    )


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
    sub_resource_relationship: AWSOrganizationToSyncingAWSAccountRel = (
        AWSOrganizationToSyncingAWSAccountRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [AWSMemberAWSAccountToOrganizationParentRel()],
    )


@dataclass(frozen=True)
class AWSAccountNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef("name")
    inscope: PropertyRef = PropertyRef("inscope", set_in_kwargs=True)


@dataclass(frozen=True)
class AWSAccountSchema(CartographyNodeSchema):
    label: str = "AWSAccount"
    properties: AWSAccountNodeProperties = AWSAccountNodeProperties()
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["Tenant"])
    scoped_cleanup: bool = False


@dataclass(frozen=True)
class AWSOrganizationAccountNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef("name")
    arn: PropertyRef = PropertyRef("arn", extra_index=True)
    email: PropertyRef = PropertyRef("email")
    state: PropertyRef = PropertyRef("state")
    status: PropertyRef = PropertyRef("status")
    joined_method: PropertyRef = PropertyRef("joined_method")
    joined_timestamp: PropertyRef = PropertyRef("joined_timestamp")
    org_id: PropertyRef = PropertyRef("org_id", extra_index=True)
    inscope: PropertyRef = PropertyRef("inscope", set_in_kwargs=True)


@dataclass(frozen=True)
class AWSOrganizationAccountSchema(CartographyNodeSchema):
    label: str = "AWSAccount"
    properties: AWSOrganizationAccountNodeProperties = (
        AWSOrganizationAccountNodeProperties()
    )
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["Tenant"])
    scoped_cleanup: bool = False


@dataclass(frozen=True)
class AWSAccountOrganizationIdNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    org_id: PropertyRef = PropertyRef("org_id", extra_index=True)


@dataclass(frozen=True)
class AWSAccountOrganizationIdSchema(CartographyNodeSchema):
    label: str = "AWSAccount"
    properties: AWSAccountOrganizationIdNodeProperties = (
        AWSAccountOrganizationIdNodeProperties()
    )
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["Tenant"])
    scoped_cleanup: bool = False
