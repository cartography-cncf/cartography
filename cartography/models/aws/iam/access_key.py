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
class AccountAccessKeyNodeProperties(CartographyNodeProperties):
    # Required unique identifier
    id: PropertyRef = PropertyRef("accesskeyid")
    accesskeyid: PropertyRef = PropertyRef("accesskeyid", extra_index=True)

    # Automatic fields (set by cartography)
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)

    # Business fields from AWS IAM access keys
    createdate: PropertyRef = PropertyRef("createdate")
    status: PropertyRef = PropertyRef("status")
    lastuseddate: PropertyRef = PropertyRef("lastuseddate")
    lastusedservice: PropertyRef = PropertyRef("lastusedservice")
    lastusedregion: PropertyRef = PropertyRef("lastusedregion")


@dataclass(frozen=True)
class AWSUserToAccountAccessKeyRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AWSUserToAccountAccessKeyRel(CartographyRelSchema):
    target_node_label: str = "AccountAccessKey"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "accesskeyid": PropertyRef("accesskeyid"),
        }
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "AWS_ACCESS_KEY"
    properties: AWSUserToAccountAccessKeyRelProperties = (
        AWSUserToAccountAccessKeyRelProperties()
    )


@dataclass(frozen=True)
class AccountAccessKeyToAWSUserRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AccountAccessKeyToAWSUserRel(CartographyRelSchema):
    target_node_label: str = "AWSUser"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "arn": PropertyRef("user_arn"),
        }
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "AWS_ACCESS_KEY"
    properties: AccountAccessKeyToAWSUserRelProperties = (
        AccountAccessKeyToAWSUserRelProperties()
    )


@dataclass(frozen=True)
class AccountAccessKeyToAWSAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AccountAccessKeyToAWSAccountRel(CartographyRelSchema):
    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef("AWS_ID", set_in_kwargs=True),
        }
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: AccountAccessKeyToAWSAccountRelProperties = (
        AccountAccessKeyToAWSAccountRelProperties()
    )


@dataclass(frozen=True)
class AccountAccessKeySchema(CartographyNodeSchema):
    label: str = "AccountAccessKey"
    properties: AccountAccessKeyNodeProperties = AccountAccessKeyNodeProperties()
    sub_resource_relationship: AccountAccessKeyToAWSAccountRel = (
        AccountAccessKeyToAWSAccountRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            AccountAccessKeyToAWSUserRel(),
            AccountAccessKeyToAWSAccountRel(),
        ]
    )
