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
class S3AclNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", description="The ID of this ACL")
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last time the node was updated",
    )
    owner: PropertyRef = PropertyRef(
        "owner", description="Canonical user ID of the S3 bucket owner."
    )
    ownerid: PropertyRef = PropertyRef(
        "ownerid",
        description="The ACL's owner ID as defined [here](https://docs.aws.amazon.com/AmazonS3/latest/API/API_control_S3ObjectOwner.html)",
    )
    type: PropertyRef = PropertyRef(
        "type",
        description="The type of the [grantee](https://docs.aws.amazon.com/AmazonS3/latest/API/API_Grantee.html).  Either ``CanonicalUser \\",
    )
    displayname: PropertyRef = PropertyRef(
        "displayname", description="Optional display name for the ACL"
    )
    granteeid: PropertyRef = PropertyRef(
        "granteeid",
        description="The ID of the grantee as defined [here](https://docs.aws.amazon.com/AmazonS3/latest/API/API_control_S3Grantee.html)",
    )
    uri: PropertyRef = PropertyRef(
        "uri", description="URI identifying the predefined S3 grantee group."
    )
    permission: PropertyRef = PropertyRef(
        "permission", description="Valid values: ``FULL_CONTROL \\"
    )


@dataclass(frozen=True)
class S3AclToAWSAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class S3AclToAWSAccountRel(CartographyRelSchema):
    "Represents a `RESOURCE` relationship from `AWSAccount` to `AWSS3Acl`."

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
    "Represents a `APPLIES_TO` relationship from `AWSS3Acl` to `AWSS3Bucket`."

    target_node_label: str = "AWSS3Bucket"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("bucket")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "APPLIES_TO"
    properties: S3AclToS3BucketRelProperties = S3AclToS3BucketRelProperties()


@dataclass(frozen=True)
class S3AclSchema(CartographyNodeSchema):
    "Represents an `AWSS3Acl` node in the AWS graph."

    label: str = "AWSS3Acl"
    # DEPRECATED: legacy S3Acl node label will be removed in v1.0.0.
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["S3Acl"])
    properties: S3AclNodeProperties = S3AclNodeProperties()
    sub_resource_relationship: S3AclToAWSAccountRel = S3AclToAWSAccountRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [S3AclToS3BucketRel()],
    )
