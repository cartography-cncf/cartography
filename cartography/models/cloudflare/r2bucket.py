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
class CloudflareR2BucketNodeProperties(CartographyNodeProperties):
    # The R2 API does not assign bucket IDs, and a bucket name is only unique
    # within one jurisdiction of one account: jurisdictions are separate
    # namespaces, so the same account can hold a `default` and an `eu` bucket
    # under the same name. Both qualify the graph ID.
    id: PropertyRef = PropertyRef(
        "id",
        description="Bucket ID, built as `<account_id>/<jurisdiction>/<bucket name>`.",
    )
    name: PropertyRef = PropertyRef(
        "name",
        extra_index=True,
        description="Bucket name.",
    )
    location: PropertyRef = PropertyRef(
        "location",
        description="Location hint of the bucket, such as `weur` or `enam`.",
    )
    jurisdiction: PropertyRef = PropertyRef(
        "jurisdiction",
        description="Jurisdiction the bucket objects are guaranteed to be stored in.",
    )
    storage_class: PropertyRef = PropertyRef(
        "storage_class",
        description="Default storage class applied to newly uploaded objects.",
    )
    creation_date: PropertyRef = PropertyRef(
        "creation_date",
        description="Timestamp when the bucket was created.",
    )
    public: PropertyRef = PropertyRef(
        "public",
        description=(
            "Whether the bucket is reachable from the internet through its managed "
            "r2.dev domain or an enabled custom domain."
        ),
    )
    r2_dev_enabled: PropertyRef = PropertyRef(
        "r2_dev_enabled",
        description="Whether the bucket is served on its managed r2.dev domain.",
    )
    public_domains: PropertyRef = PropertyRef(
        "public_domains",
        description=(
            "Hostnames serving the bucket publicly, including the managed r2.dev "
            "domain and any enabled custom domain."
        ),
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class CloudflareR2BucketToAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:CloudflareR2Bucket)<-[:RESOURCE]-(:CloudflareAccount)
class CloudflareR2BucketToAccountRel(CartographyRelSchema):
    """The account contains the R2 bucket."""

    target_node_label: str = "CloudflareAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("account_id", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: CloudflareR2BucketToAccountRelProperties = (
        CloudflareR2BucketToAccountRelProperties()
    )


@dataclass(frozen=True)
class CloudflareR2BucketToZoneRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:CloudflareZone)-[:HAS_R2_CUSTOM_DOMAIN]->(:CloudflareR2Bucket)
class CloudflareR2BucketToZoneRel(CartographyRelSchema):
    """The DNS zone hosts an enabled custom domain serving the R2 bucket."""

    target_node_label: str = "CloudflareZone"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("zone_ids", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS_R2_CUSTOM_DOMAIN"
    properties: CloudflareR2BucketToZoneRelProperties = (
        CloudflareR2BucketToZoneRelProperties()
    )


@dataclass(frozen=True)
class CloudflareR2BucketSchema(CartographyNodeSchema):
    """An R2 object storage bucket in Cloudflare."""

    label: str = "CloudflareR2Bucket"
    properties: CloudflareR2BucketNodeProperties = CloudflareR2BucketNodeProperties()
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([OBJECT_STORAGE])
    sub_resource_relationship: CloudflareR2BucketToAccountRel = (
        CloudflareR2BucketToAccountRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            CloudflareR2BucketToZoneRel(),
        ],
    )
