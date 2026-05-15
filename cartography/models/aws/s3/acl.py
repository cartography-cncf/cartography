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
class S3AclNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    owner: PropertyRef = PropertyRef("owner")
    ownerid: PropertyRef = PropertyRef("ownerid")
    type: PropertyRef = PropertyRef("type")
    displayname: PropertyRef = PropertyRef("displayname")
    granteeid: PropertyRef = PropertyRef("granteeid")
    uri: PropertyRef = PropertyRef("uri")
    permission: PropertyRef = PropertyRef("permission")


@dataclass(frozen=True)
class S3AclToAWSAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class S3AclToAWSAccountRel(CartographyRelSchema):
    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AWS_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: S3AclToAWSAccountRelProperties = S3AclToAWSAccountRelProperties()


@dataclass(frozen=True)
class S3AclToS3BucketRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class S3AclToS3BucketRel(CartographyRelSchema):
    target_node_label: str = "S3Bucket"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("bucket")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "APPLIES_TO"
    properties: S3AclToS3BucketRelProperties = S3AclToS3BucketRelProperties()


@dataclass(frozen=True)
class S3AclSchema(CartographyNodeSchema):
    label: str = "S3Acl"
    properties: S3AclNodeProperties = S3AclNodeProperties()
    sub_resource_relationship: S3AclToAWSAccountRel = S3AclToAWSAccountRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [S3AclToS3BucketRel()],
    )
