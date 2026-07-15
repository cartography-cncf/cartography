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
class GCPApiKeyNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id", extra_index=True, description="Stable identifier for this resource."
    )
    uid: PropertyRef = PropertyRef(
        "uid", description="The unique identifier of the key."
    )
    name: PropertyRef = PropertyRef("name", description="Same as id.")
    display_name: PropertyRef = PropertyRef(
        "displayName", description="Human-readable display name of the key."
    )
    create_time: PropertyRef = PropertyRef(
        "createTime", description="RFC 3339 timestamp when the key was created."
    )
    update_time: PropertyRef = PropertyRef(
        "updateTime", description="RFC 3339 timestamp when the key was last updated."
    )
    delete_time: PropertyRef = PropertyRef(
        "deleteTime",
        description="RFC 3339 timestamp when the key was deleted, if applicable.",
    )
    # Whether the key has any API/application restrictions. An unrestricted key
    # can call any enabled API from anywhere, so this is the security-relevant bit.
    restricted: PropertyRef = PropertyRef(
        "restricted",
        description="Whether the key has any API or application restrictions. Unrestricted keys are higher risk.",
    )
    restrictions: PropertyRef = PropertyRef(
        "restrictions",
        description="JSON-encoded restriction configuration (API targets, allowed referrers/IPs/apps), if any.",
    )
    etag: PropertyRef = PropertyRef("etag", description="The etag of the key.")
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="The timestamp of the last update.",
    )


@dataclass(frozen=True)
class GCPApiKeyToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last sync that observed this data.",
    )


@dataclass(frozen=True)
class GCPApiKeyToProjectRel(CartographyRelSchema):
    target_node_label: str = "GCPProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("PROJECT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: GCPApiKeyToProjectRelProperties = GCPApiKeyToProjectRelProperties()


@dataclass(frozen=True)
class GCPApiKeySchema(CartographyNodeSchema):
    """A Google Cloud Api Key resource."""

    label: str = "GCPApiKey"
    # APIKey label is used for ontology mapping. These are the real
    # apikeys.googleapis.com keys, distinct from GCPServiceAccountKey.
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["APIKey"])
    properties: GCPApiKeyNodeProperties = GCPApiKeyNodeProperties()
    sub_resource_relationship: GCPApiKeyToProjectRel = GCPApiKeyToProjectRel()
