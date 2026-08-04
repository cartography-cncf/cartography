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
from cartography.models.ontology.labels import FUNCTION


@dataclass(frozen=True)
class CloudflareWorkerScriptNodeProperties(CartographyNodeProperties):
    # The Workers API identifies a script by its name, which is only unique
    # within an account, so the graph ID is qualified with the account ID.
    id: PropertyRef = PropertyRef(
        "id",
        description="Script ID, built as `<account_id>/<script name>`.",
    )
    name: PropertyRef = PropertyRef(
        "name",
        extra_index=True,
        description="Script name.",
    )
    tag: PropertyRef = PropertyRef(
        "tag",
        description="Immutable Cloudflare ID of the script.",
    )
    etag: PropertyRef = PropertyRef(
        "etag",
        description="Hash of the script content.",
    )
    created_on: PropertyRef = PropertyRef(
        "created_on",
        description="Timestamp when the script was created.",
    )
    modified_on: PropertyRef = PropertyRef(
        "modified_on",
        description="Timestamp when the script was last modified.",
    )
    usage_model: PropertyRef = PropertyRef(
        "usage_model",
        description="Usage model billed for the script invocations.",
    )
    logpush: PropertyRef = PropertyRef(
        "logpush",
        description="Whether Logpush is turned on for the script.",
    )
    compatibility_date: PropertyRef = PropertyRef(
        "compatibility_date",
        description="Workers runtime version the script targets.",
    )
    compatibility_flags: PropertyRef = PropertyRef(
        "compatibility_flags",
        description="Runtime feature flags enabled or disabled for the script.",
    )
    has_assets: PropertyRef = PropertyRef(
        "has_assets",
        description="Whether the script serves static assets.",
    )
    has_modules: PropertyRef = PropertyRef(
        "has_modules",
        description="Whether the script uses ES modules.",
    )
    placement_mode: PropertyRef = PropertyRef(
        "placement_mode",
        description="Placement mode of the script, such as `smart` or `targeted`.",
    )
    last_deployed_from: PropertyRef = PropertyRef(
        "last_deployed_from",
        description="Client most recently used to deploy the script.",
    )
    observability_enabled: PropertyRef = PropertyRef(
        "observability.enabled",
        description="Whether observability is enabled for the script.",
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class CloudflareWorkerScriptToAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:CloudflareWorkerScript)<-[:RESOURCE]-(:CloudflareAccount)
class CloudflareWorkerScriptToAccountRel(CartographyRelSchema):
    """The account contains the Worker script."""

    target_node_label: str = "CloudflareAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("account_id", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: CloudflareWorkerScriptToAccountRelProperties = (
        CloudflareWorkerScriptToAccountRelProperties()
    )


@dataclass(frozen=True)
class CloudflareWorkerScriptSchema(CartographyNodeSchema):
    """A Worker script deployed in Cloudflare."""

    label: str = "CloudflareWorkerScript"
    properties: CloudflareWorkerScriptNodeProperties = (
        CloudflareWorkerScriptNodeProperties()
    )
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([FUNCTION])
    sub_resource_relationship: CloudflareWorkerScriptToAccountRel = (
        CloudflareWorkerScriptToAccountRel()
    )
