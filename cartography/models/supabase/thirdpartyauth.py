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
class SupabaseThirdPartyAuthIntegrationNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    type: PropertyRef = PropertyRef("type")
    # An external issuer whose JWTs this project accepts, so it is a trust edge
    # into the project's auth surface.
    oidc_issuer_url: PropertyRef = PropertyRef("oidc_issuer_url", extra_index=True)
    jwks_url: PropertyRef = PropertyRef("jwks_url")
    inserted_at: PropertyRef = PropertyRef("inserted_at")
    updated_at: PropertyRef = PropertyRef("updated_at")
    resolved_at: PropertyRef = PropertyRef("resolved_at")


@dataclass(frozen=True)
class SupabaseThirdPartyAuthIntegrationToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SupabaseProject)-[:RESOURCE]->(:SupabaseThirdPartyAuthIntegration)
class SupabaseThirdPartyAuthIntegrationToProjectRel(CartographyRelSchema):
    target_node_label: str = "SupabaseProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("PROJECT_REF", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: SupabaseThirdPartyAuthIntegrationToProjectRelProperties = (
        SupabaseThirdPartyAuthIntegrationToProjectRelProperties()
    )


@dataclass(frozen=True)
class SupabaseThirdPartyAuthIntegrationSchema(CartographyNodeSchema):
    label: str = "SupabaseThirdPartyAuthIntegration"
    properties: SupabaseThirdPartyAuthIntegrationNodeProperties = (
        SupabaseThirdPartyAuthIntegrationNodeProperties()
    )
    sub_resource_relationship: SupabaseThirdPartyAuthIntegrationToProjectRel = (
        SupabaseThirdPartyAuthIntegrationToProjectRel()
    )
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([IDENTITY_PROVIDER])
