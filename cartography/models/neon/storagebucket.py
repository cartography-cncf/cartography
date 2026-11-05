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
from cartography.models.ontology.labels import OBJECT_STORAGE


@dataclass(frozen=True)
class NeonStorageBucketNodeProperties(CartographyNodeProperties):
    # Buckets branch with the database: a child branch lists its parent's buckets
    # and serves its own copy of their objects from its own S3 endpoint, so the
    # node is per branch.
    id: PropertyRef = PropertyRef(
        "id", description="Synthesised as `<branch id>/<bucket name>`"
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef(
        "name", extra_index=True, description="Name of the bucket"
    )
    branch_id: PropertyRef = PropertyRef(
        "branch_id", description="Id of the branch serving this copy of the bucket"
    )
    access_level: PropertyRef = PropertyRef(
        "access_level",
        description="`public_read` lets anyone read objects without credentials, `private` requires a credential",
    )
    public: PropertyRef = PropertyRef(
        "public",
        description="`True` when `access_level` is `public_read`",
    )
    exposed_internet: PropertyRef = PropertyRef(
        "exposed_internet",
        extra_index=True,
        description="`True` when the bucket is `public_read`, meaning every object is readable without authentication",
    )
    exposed_internet_type: PropertyRef = PropertyRef(
        "exposed_internet_type",
        extra_index=True,
        description="How it is exposed. Always `direct`, since objects are served from the branch's own S3 endpoint",
    )
    s3_endpoint: PropertyRef = PropertyRef(
        "s3_endpoint",
        description="The branch's S3-compatible endpoint URL. Objects are addressed path-style as `<s3_endpoint>/<bucket>/<key>`",
    )
    url: PropertyRef = PropertyRef(
        "url",
        extra_index=True,
        description="The bucket's base URL, `<s3_endpoint>/<bucket>`. For a `public_read` bucket every object under it is readable without credentials",
    )
    region: PropertyRef = PropertyRef(
        "region", description="The S3 signing region of the branch's storage"
    )
    created_at: PropertyRef = PropertyRef(
        "created_at", description="When the bucket was created"
    )


@dataclass(frozen=True)
class NeonStorageBucketToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:NeonProject)-[:RESOURCE]->(:NeonStorageBucket)
class NeonStorageBucketToProjectRel(CartographyRelSchema):
    target_node_label: str = "NeonProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("PROJECT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: NeonStorageBucketToProjectRelProperties = (
        NeonStorageBucketToProjectRelProperties()
    )


@dataclass(frozen=True)
class NeonStorageBucketToBranchRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:NeonBranch)-[:CONTAINS]->(:NeonStorageBucket)
class NeonStorageBucketToBranchRel(CartographyRelSchema):
    target_node_label: str = "NeonBranch"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("branch_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "CONTAINS"
    properties: NeonStorageBucketToBranchRelProperties = (
        NeonStorageBucketToBranchRelProperties()
    )


@dataclass(frozen=True)
class NeonStorageBucketSchema(CartographyNodeSchema):
    """Represents a Neon Object Storage bucket as served by one branch."""

    label: str = "NeonStorageBucket"
    properties: NeonStorageBucketNodeProperties = NeonStorageBucketNodeProperties()
    sub_resource_relationship: NeonStorageBucketToProjectRel = (
        NeonStorageBucketToProjectRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            NeonStorageBucketToBranchRel(),
        ],
    )
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([OBJECT_STORAGE])
