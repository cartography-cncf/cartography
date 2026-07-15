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
class IdentityCenterInstanceProperties(CartographyNodeProperties):
    identity_store_id: PropertyRef = PropertyRef(
        "IdentityStoreId",
        description="The identity store ID of the Identity Center instance",
    )
    arn: PropertyRef = PropertyRef(
        "InstanceArn",
        description="The Amazon Resource Name (ARN) of the Identity Center instance",
    )
    created_date: PropertyRef = PropertyRef(
        "CreatedDate", description="The date the Identity Center instance was created"
    )
    id: PropertyRef = PropertyRef(
        "InstanceArn", description="Unique identifier for the Identity Center instance"
    )
    status: PropertyRef = PropertyRef(
        "Status", description="The status of the Identity Center instance"
    )
    region: PropertyRef = PropertyRef(
        "Region",
        set_in_kwargs=True,
        description="The AWS region where the Identity Center instance is located",
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last time the node was updated",
    )


@dataclass(frozen=True)
class IdentityCenterToAWSAccountRelRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:IdentityCenter)<-[:RESOURCE]-(:AWSAccount)
class IdentityCenterToAWSAccountRel(CartographyRelSchema):
    "Represents a `RESOURCE` relationship from `AWSAccount` to `AWSIdentityCenter`."

    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AWS_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: IdentityCenterToAWSAccountRelRelProperties = (
        IdentityCenterToAWSAccountRelRelProperties()
    )


@dataclass(frozen=True)
class AWSIdentityCenterInstanceSchema(CartographyNodeSchema):
    "Represents an `AWSIdentityCenter` node in the AWS graph."

    label: str = "AWSIdentityCenter"
    properties: IdentityCenterInstanceProperties = IdentityCenterInstanceProperties()
    sub_resource_relationship: IdentityCenterToAWSAccountRel = (
        IdentityCenterToAWSAccountRel()
    )
