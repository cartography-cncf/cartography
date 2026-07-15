from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class AWSPolicyStatementNodeProperties(CartographyNodeProperties):
    # Required unique identifier
    id: PropertyRef = PropertyRef(
        "id",
        description="The unique identifier for a statement. <br>If the statement has an Sid the id will be calculated as _AWSPolicy.id_/statements/_Sid_. <br>If the statement has no Sid the id will be calculated as  _AWSPolicy.id_/statements/_index of statement in statement list_",
    )

    # Automatic fields (set by cartography)
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last time the node was updated",
    )

    # Business fields from AWS IAM policy statements
    effect: PropertyRef = PropertyRef(
        "Effect", description='"Allow" or "Deny" - the effect of this statement'
    )
    action: PropertyRef = PropertyRef(
        "Action",
        description="(array) The permissions allowed or denied by the statement. Can contain wildcards",
    )
    notaction: PropertyRef = PropertyRef(
        "NotAction",
        description="(array) The permissions explicitly not matched by the statement",
    )
    resource: PropertyRef = PropertyRef(
        "Resource",
        description="(array) The resources the statement is applied to. Can contain wildcards",
    )
    notresource: PropertyRef = PropertyRef(
        "NotResource",
        description="(array) The resources explicitly not matched by the statement",
    )
    condition: PropertyRef = PropertyRef(
        "Condition", description="Conditions under which the statement applies"
    )
    sid: PropertyRef = PropertyRef(
        "Sid",
        description="Statement ID - an optional identifier for the policy statement",
    )


@dataclass(frozen=True)
class AWSPolicyStatementToAWSPolicyRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AWSPolicyStatementToAWSPolicyRel(CartographyRelSchema):
    "Represents a `STATEMENT` relationship from `AWSPolicy` to `AWSPolicyStatement`."

    target_node_label: str = "AWSPolicy"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef("POLICY_ID", set_in_kwargs=True),
        }
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "STATEMENT"
    properties: AWSPolicyStatementToAWSPolicyRelProperties = (
        AWSPolicyStatementToAWSPolicyRelProperties()
    )


@dataclass(frozen=True)
class AWSPolicyStatementSchema(CartographyNodeSchema):
    "Represents an `AWSPolicyStatement` node in the AWS graph."

    label: str = "AWSPolicyStatement"
    properties: AWSPolicyStatementNodeProperties = AWSPolicyStatementNodeProperties()
    sub_resource_relationship: AWSPolicyStatementToAWSPolicyRel = (
        AWSPolicyStatementToAWSPolicyRel()
    )
