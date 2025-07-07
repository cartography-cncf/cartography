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
class S3AccountPublicAccessBlockNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    account_id: PropertyRef = PropertyRef("account_id")
    region: PropertyRef = PropertyRef("region", set_in_kwargs=True)
    block_public_acls: PropertyRef = PropertyRef("block_public_acls")
    ignore_public_acls: PropertyRef = PropertyRef("ignore_public_acls")
    block_public_policy: PropertyRef = PropertyRef("block_public_policy")
    restrict_public_buckets: PropertyRef = PropertyRef("restrict_public_buckets")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class S3AccountPublicAccessBlockRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class S3AccountPublicAccessBlockToAWSAccountRel(CartographyRelSchema):
    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AWS_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: S3AccountPublicAccessBlockRelProperties = (
        S3AccountPublicAccessBlockRelProperties()
    )


@dataclass(frozen=True)
class S3AccountPublicAccessBlockSchema(CartographyNodeSchema):
    label: str = "S3AccountPublicAccessBlock"
    properties: S3AccountPublicAccessBlockNodeProperties = (
        S3AccountPublicAccessBlockNodeProperties()
    )
    sub_resource_relationship: S3AccountPublicAccessBlockToAWSAccountRel = (
        S3AccountPublicAccessBlockToAWSAccountRel()
    )
