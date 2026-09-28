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
from cartography.models.ontology.labels import API_KEY


@dataclass(frozen=True)
class SupabaseApiKeyNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id",
        description="Synthesised as `<project ref>/<key id>`. The prefix is required because the API returns `anon` and `service_role` as the ids of the legacy keys, which are identical in every project; without it two projects would share one node. When the API returns no id at all, the key type is used in its place",
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef(
        "name", extra_index=True, description="Name of the key"
    )
    # "legacy" (the old JWT anon / service_role keys), "publishable" or "secret".
    type: PropertyRef = PropertyRef(
        "type", description="`legacy`, `publishable` or `secret`"
    )
    # A short non-secret identifying prefix, and a server-side hash. The key
    # material itself (`api_key`) is only returned with ?reveal=true, which this
    # module never requests, and is never stored.
    prefix: PropertyRef = PropertyRef(
        "prefix", description="Non-secret identifying prefix of the key"
    )
    hash: PropertyRef = PropertyRef("hash", description="Server-side hash of the key")
    description: PropertyRef = PropertyRef(
        "description", description="Description of the key"
    )
    inserted_at: PropertyRef = PropertyRef(
        "inserted_at", description="When the key was created"
    )
    updated_at: PropertyRef = PropertyRef(
        "updated_at", description="When the key was last changed"
    )


@dataclass(frozen=True)
class SupabaseApiKeyToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SupabaseProject)-[:RESOURCE]->(:SupabaseApiKey)
class SupabaseApiKeyToProjectRel(CartographyRelSchema):
    target_node_label: str = "SupabaseProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("PROJECT_REF", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: SupabaseApiKeyToProjectRelProperties = (
        SupabaseApiKeyToProjectRelProperties()
    )


@dataclass(frozen=True)
class SupabaseApiKeySchema(CartographyNodeSchema):
    """Represents a project API key. The key material is never stored. Cartography lists keys without the `reveal` parameter, though note the endpoint returns the value regardless; it is dropped during transformation and this node has no property to hold it."""

    label: str = "SupabaseApiKey"
    properties: SupabaseApiKeyNodeProperties = SupabaseApiKeyNodeProperties()
    sub_resource_relationship: SupabaseApiKeyToProjectRel = SupabaseApiKeyToProjectRel()
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([API_KEY])
