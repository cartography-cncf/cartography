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
class SSOUserProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef('UserId', extra_index=True)
    user_name: PropertyRef = PropertyRef('UserName')
    identity_store_id: PropertyRef = PropertyRef('IdentityStoreId')
    external_id: PropertyRef = PropertyRef('ExternalId', extra_index=True)
    region: PropertyRef = PropertyRef('Region')
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)


@dataclass(frozen=True)
class SSOUserToOktaUserRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)


@dataclass(frozen=True)
class SSOUserToOktaUser(CartographyRelSchema):
    target_node_label: str = 'UserAccount'
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {'id': PropertyRef('ExternalId')},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "CAN_ASSUME_IDENTITY"
    properties: SSOUserToOktaUserRelProperties = SSOUserToOktaUserRelProperties()


@dataclass(frozen=True)
class AWSSSOUserToAwsAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)


@dataclass(frozen=True)
# (:IdentityCenter)<-[:RESOURCE]-(:AWSAccount)
class AWSSSOUserToAWSAccount(CartographyRelSchema):
    target_node_label: str = 'AWSAccount'
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {'id': PropertyRef('AWS_ID', set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: AWSSSOUserToAwsAccountRelProperties = AWSSSOUserToAwsAccountRelProperties()


@dataclass(frozen=True)
class AWSSSOUserSchema(CartographyNodeSchema):
    label: str = 'AWSSSOUser'
    properties: SSOUserProperties = SSOUserProperties()
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["UserAccount"])
    sub_resource_relationship: AWSSSOUserToAWSAccount = AWSSSOUserToAWSAccount()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            SSOUserToOktaUser(),
        ],
    )
