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
    identity_store_id: PropertyRef = PropertyRef('IdentityStoreId')
    arn: PropertyRef = PropertyRef('InstanceArn')
    created_date: PropertyRef = PropertyRef('CreatedDate')
    id: PropertyRef = PropertyRef('InstanceArn')
    status: PropertyRef = PropertyRef('Status')
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)


@dataclass(frozen=True)
class IdentityCenterToAwsAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)


@dataclass(frozen=True)
# (:IdentityCenter)<-[:RESOURCE]-(:AWSAccount)
class IdentityCenterToAWSAccount(CartographyRelSchema):
    target_node_label: str = 'AWSAccount'
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {'id': PropertyRef('AWS_ID', set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: IdentityCenterToAwsAccountRelProperties = IdentityCenterToAwsAccountRelProperties()


@dataclass(frozen=True)
class AWSIdentityCenterInstanceSchema(CartographyNodeSchema):
    label: str = 'AWSIdentityCenter'
    properties: IdentityCenterInstanceProperties = IdentityCenterInstanceProperties()
    sub_resource_relationship: IdentityCenterToAWSAccount = IdentityCenterToAWSAccount()
