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
from cartography.models.ontology.labels import IDENTITY_PROVIDER


@dataclass(frozen=True)
class SupabaseSSOProviderNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", description="The provider id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    entity_id: PropertyRef = PropertyRef(
        "entity_id",
        extra_index=True,
        description="The SAML entity id, which is also the trust identifier",
    )
    metadata_url: PropertyRef = PropertyRef(
        "metadata_url", description="URL of the provider's SAML metadata"
    )
    name_id_format: PropertyRef = PropertyRef(
        "name_id_format", description="The requested SAML NameID format"
    )
    # The email domains routed to this identity provider.
    domains: PropertyRef = PropertyRef(
        "domains", description="Email domains routed to this provider"
    )
    created_at: PropertyRef = PropertyRef(
        "created_at", description="When the provider was configured"
    )
    updated_at: PropertyRef = PropertyRef(
        "updated_at", description="When the provider was last changed"
    )


@dataclass(frozen=True)
class SupabaseSSOProviderToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SupabaseProject)-[:RESOURCE]->(:SupabaseSSOProvider)
class SupabaseSSOProviderToProjectRel(CartographyRelSchema):
    target_node_label: str = "SupabaseProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("PROJECT_REF", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: SupabaseSSOProviderToProjectRelProperties = (
        SupabaseSSOProviderToProjectRelProperties()
    )


@dataclass(frozen=True)
class SupabaseSSOProviderSchema(CartographyNodeSchema):
    """Represents a SAML identity provider configured for a project's auth service."""

    label: str = "SupabaseSSOProvider"
    properties: SupabaseSSOProviderNodeProperties = SupabaseSSOProviderNodeProperties()
    sub_resource_relationship: SupabaseSSOProviderToProjectRel = (
        SupabaseSSOProviderToProjectRel()
    )
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([IDENTITY_PROVIDER])
