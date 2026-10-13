from dataclasses import dataclass

from cartography.models.aws.iam.policy_statement import AWSPolicyStatementNodeProperties
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
class AWSServiceControlPolicyRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AWSServiceControlPolicyNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id",
        description="Cartography ID for this policy, formatted as `{org_id}/{policy_id}` because AWS managed policies such as `p-FullAWSAccess` share the same ID and ARN across organizations.",
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    policy_id: PropertyRef = PropertyRef(
        "policy_id",
        extra_index=True,
        description="The raw AWS Organizations policy ID.",
    )
    arn: PropertyRef = PropertyRef(
        "arn",
        extra_index=True,
        description="The AWS Organizations policy ARN.",
    )
    name: PropertyRef = PropertyRef("name", description="The policy name.")
    description: PropertyRef = PropertyRef(
        "description", description="The policy description."
    )
    aws_managed: PropertyRef = PropertyRef(
        "aws_managed",
        description="True if the policy is managed by AWS, such as `FullAWSAccess`.",
    )
    content: PropertyRef = PropertyRef(
        "content",
        description="The policy document as returned by AWS Organizations, as a JSON string.",
    )
    org_id: PropertyRef = PropertyRef(
        "org_id", extra_index=True, description="The AWS Organization ID."
    )


@dataclass(frozen=True)
class AWSServiceControlPolicyToOrganizationRel(CartographyRelSchema):
    target_node_label: str = "AWSOrganization"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ORG_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: AWSServiceControlPolicyRelProperties = (
        AWSServiceControlPolicyRelProperties()
    )


@dataclass(frozen=True)
class AWSServiceControlPolicyAppliesToRootRel(CartographyRelSchema):
    target_node_label: str = "AWSOrganizationRoot"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("target_root_ids", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "APPLIES_TO"
    properties: AWSServiceControlPolicyRelProperties = (
        AWSServiceControlPolicyRelProperties()
    )


@dataclass(frozen=True)
class AWSServiceControlPolicyAppliesToOURel(CartographyRelSchema):
    target_node_label: str = "AWSOrganizationalUnit"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("target_ou_ids", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "APPLIES_TO"
    properties: AWSServiceControlPolicyRelProperties = (
        AWSServiceControlPolicyRelProperties()
    )


@dataclass(frozen=True)
class AWSServiceControlPolicyAppliesToAccountRel(CartographyRelSchema):
    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("target_account_ids", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "APPLIES_TO"
    properties: AWSServiceControlPolicyRelProperties = (
        AWSServiceControlPolicyRelProperties()
    )


@dataclass(frozen=True)
class AWSServiceControlPolicySchema(CartographyNodeSchema):
    """Representation of an AWS Organizations [service control policy](https://docs.aws.amazon.com/organizations/latest/userguide/orgs_manage_policies_scps.html)."""

    label: str = "AWSServiceControlPolicy"
    properties: AWSServiceControlPolicyNodeProperties = (
        AWSServiceControlPolicyNodeProperties()
    )
    sub_resource_relationship: AWSServiceControlPolicyToOrganizationRel = (
        AWSServiceControlPolicyToOrganizationRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            AWSServiceControlPolicyAppliesToRootRel(),
            AWSServiceControlPolicyAppliesToOURel(),
            AWSServiceControlPolicyAppliesToAccountRel(),
        ],
    )


@dataclass(frozen=True)
class AWSServiceControlPolicyStatementNodeProperties(AWSPolicyStatementNodeProperties):
    id: PropertyRef = PropertyRef(
        "id",
        description="The statement ID, formatted as `{AWSServiceControlPolicy.id}/statement/{Sid}`, or `{AWSServiceControlPolicy.id}/statement/{index}` when the statement has no Sid.",
    )


@dataclass(frozen=True)
class AWSServiceControlPolicyStatementToOrganizationRel(CartographyRelSchema):
    target_node_label: str = "AWSOrganization"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ORG_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: AWSServiceControlPolicyRelProperties = (
        AWSServiceControlPolicyRelProperties()
    )


@dataclass(frozen=True)
class AWSServiceControlPolicyStatementToPolicyRel(CartographyRelSchema):
    target_node_label: str = "AWSServiceControlPolicy"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("policy_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "STATEMENT"
    properties: AWSServiceControlPolicyRelProperties = (
        AWSServiceControlPolicyRelProperties()
    )


@dataclass(frozen=True)
class AWSServiceControlPolicyStatementSchema(CartographyNodeSchema):
    """A statement in an AWS Organizations service control policy."""

    label: str = "AWSServiceControlPolicyStatement"
    properties: AWSServiceControlPolicyStatementNodeProperties = (
        AWSServiceControlPolicyStatementNodeProperties()
    )
    # Scoped to the organization rather than the policy so that one cleanup
    # pass also removes the statements of policies deleted since the last sync.
    sub_resource_relationship: AWSServiceControlPolicyStatementToOrganizationRel = (
        AWSServiceControlPolicyStatementToOrganizationRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [AWSServiceControlPolicyStatementToPolicyRel()],
    )
