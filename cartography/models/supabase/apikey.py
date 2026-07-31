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
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef("name", extra_index=True)
    # "legacy" (the old JWT anon / service_role keys), "publishable" or "secret".
    type: PropertyRef = PropertyRef("type")
    # A short non-secret identifying prefix, and a server-side hash. The key
    # material itself (`api_key`) is only returned with ?reveal=true, which this
    # module never requests, and is never stored.
    prefix: PropertyRef = PropertyRef("prefix")
    hash: PropertyRef = PropertyRef("hash")
    description: PropertyRef = PropertyRef("description")
    inserted_at: PropertyRef = PropertyRef("inserted_at")
    updated_at: PropertyRef = PropertyRef("updated_at")


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
    label: str = "SupabaseApiKey"
    properties: SupabaseApiKeyNodeProperties = SupabaseApiKeyNodeProperties()
    sub_resource_relationship: SupabaseApiKeyToProjectRel = SupabaseApiKeyToProjectRel()
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([API_KEY])
