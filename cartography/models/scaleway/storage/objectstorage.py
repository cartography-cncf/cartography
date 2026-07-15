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


@dataclass(frozen=True)
class ScalewayObjectStorageBucketNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", description="Bucket name (globally unique).")
    name: PropertyRef = PropertyRef("name", description="Bucket name.")
    region: PropertyRef = PropertyRef(
        "region",
        description="Region the bucket lives in (`fr-par`, `nl-ams`, `pl-waw`, `it-mil`).",
    )
    endpoint: PropertyRef = PropertyRef(
        "endpoint", description="Public S3 endpoint URL of the bucket."
    )
    creation_date: PropertyRef = PropertyRef(
        "creation_date", description="Bucket creation date."
    )
    tags: PropertyRef = PropertyRef("tags", description="Bucket tags (`key=value`).")
    versioning_status: PropertyRef = PropertyRef(
        "versioning_status",
        description="Versioning status (`Enabled`, `Suspended`, or unset).",
    )
    # Public-exposure signals (mirrors AWS S3 anonymous_access / GCP acl_public).
    # `public` is the combined tri-state (null = unknown, both sources unreadable).
    acl_public: PropertyRef = PropertyRef(
        "acl_public",
        description="True if the bucket ACL grants access to `AllUsers` / `AuthenticatedUsers` (null if the ACL could not be read).",
    )
    anonymous_access: PropertyRef = PropertyRef(
        "anonymous_access",
        extra_index=True,
        description="True if the bucket policy grants anonymous (internet) access (null if the policy could not be read).",
    )
    anonymous_actions: PropertyRef = PropertyRef(
        "anonymous_actions",
        description="Actions granted to anonymous principals by the bucket policy.",
    )
    public: PropertyRef = PropertyRef(
        "public",
        extra_index=True,
        description="Combined public-exposure signal: `acl_public` OR `anonymous_access`; null when both sources were unreadable.",
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated", set_in_kwargs=True, description="Timestamp of the last update"
    )


@dataclass(frozen=True)
class ScalewayObjectStorageBucketToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:ScalewayProject)-[:RESOURCE]->(:ScalewayObjectStorageBucket)
class ScalewayObjectStorageBucketToProjectRel(CartographyRelSchema):
    """Connects `ScalewayProject` to `ScalewayObjectStorageBucket` through `RESOURCE`."""

    target_node_label: str = "ScalewayProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("PROJECT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: ScalewayObjectStorageBucketToProjectRelProperties = (
        ScalewayObjectStorageBucketToProjectRelProperties()
    )


@dataclass(frozen=True)
class ScalewayObjectStorageBucketSchema(CartographyNodeSchema):
    """An Object Storage bucket is an S3-compatible container for objects. Scaleway Object
    Storage is not exposed by the Scaleway Python SDK, so it is collected through the
    regional S3-compatible endpoints.
    """

    label: str = "ScalewayObjectStorageBucket"
    properties: ScalewayObjectStorageBucketNodeProperties = (
        ScalewayObjectStorageBucketNodeProperties()
    )
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["ObjectStorage"])
    sub_resource_relationship: ScalewayObjectStorageBucketToProjectRel = (
        ScalewayObjectStorageBucketToProjectRel()
    )
