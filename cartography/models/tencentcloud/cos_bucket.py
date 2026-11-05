from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import TargetNodeMatcher
from cartography.models.ontology.labels import OBJECT_STORAGE


@dataclass(frozen=True)
class TencentCloudCOSBucketNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id",
        description="Full bucket name, `<name>-<APPID>`. Bucket names are globally unique.",
    )
    name: PropertyRef = PropertyRef(
        "name", extra_index=True, description="Full bucket name, `<name>-<APPID>`."
    )
    region: PropertyRef = PropertyRef(
        "region", extra_index=True, description="Region the bucket is in."
    )
    bucket_type: PropertyRef = PropertyRef(
        "bucket_type", description="Bucket type reported by COS, e.g. `cos`, `ofs`."
    )
    creation_date: PropertyRef = PropertyRef(
        "creation_date", description="Time the bucket was created."
    )
    anonymous_access: PropertyRef = PropertyRef(
        "anonymous_access",
        extra_index=True,
        description=(
            "`True` when the bucket ACL grants any permission to all users. Unset when the "
            "ACL could not be read. Bucket policies are not evaluated."
        ),
    )
    anonymous_actions: PropertyRef = PropertyRef(
        "anonymous_actions",
        description="Permissions the bucket ACL grants to all users, e.g. `READ`, `WRITE`.",
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class TencentCloudCOSBucketToAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:TencentCloudAccount)-[:RESOURCE]->(:TencentCloudCOSBucket)
class TencentCloudCOSBucketToAccountRel(CartographyRelSchema):
    """Connects a `TencentCloudAccount` to its COS buckets."""

    target_node_label: str = "TencentCloudAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ACCOUNT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: TencentCloudCOSBucketToAccountRelProperties = (
        TencentCloudCOSBucketToAccountRelProperties()
    )


@dataclass(frozen=True)
class TencentCloudCOSBucketSchema(CartographyNodeSchema):
    """A Cloud Object Storage (COS) bucket."""

    label: str = "TencentCloudCOSBucket"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([OBJECT_STORAGE])
    properties: TencentCloudCOSBucketNodeProperties = (
        TencentCloudCOSBucketNodeProperties()
    )
    sub_resource_relationship: TencentCloudCOSBucketToAccountRel = (
        TencentCloudCOSBucketToAccountRel()
    )
