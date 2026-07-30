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
from cartography.models.ontology.labels import THIRD_PARTY_APP


# --- Node Definitions ---
@dataclass(frozen=True)
class NetlifyServiceInstanceNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    site_id: PropertyRef = PropertyRef("site_id")
    # The add-on's slug is its stable identifier and doubles as the ThirdPartyApp client_id:
    # Netlify add-ons are identified by slug, not by an OAuth client id.
    service_slug: PropertyRef = PropertyRef("service_slug", extra_index=True)
    service_name: PropertyRef = PropertyRef("service_name")
    service_path: PropertyRef = PropertyRef("service_path")
    url: PropertyRef = PropertyRef("url")
    created_at: PropertyRef = PropertyRef("created_at")
    updated_at: PropertyRef = PropertyRef("updated_at")


# --- Relationship Definitions ---
@dataclass(frozen=True)
class NetlifyServiceInstanceToNetlifyAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:NetlifyAccount)-[:RESOURCE]->(:NetlifyServiceInstance)
class NetlifyServiceInstanceToNetlifyAccountRel(CartographyRelSchema):
    target_node_label: str = "NetlifyAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("NETLIFY_ACCOUNT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: NetlifyServiceInstanceToNetlifyAccountRelProperties = (
        NetlifyServiceInstanceToNetlifyAccountRelProperties()
    )


@dataclass(frozen=True)
class NetlifyServiceInstanceToSiteRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:NetlifySite)-[:HAS_SERVICE_INSTANCE]->(:NetlifyServiceInstance)
class NetlifyServiceInstanceToSiteRel(CartographyRelSchema):
    target_node_label: str = "NetlifySite"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("site_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS_SERVICE_INSTANCE"
    properties: NetlifyServiceInstanceToSiteRelProperties = (
        NetlifyServiceInstanceToSiteRelProperties()
    )


# --- Main Schema ---
@dataclass(frozen=True)
class NetlifyServiceInstanceSchema(CartographyNodeSchema):
    """
    A third-party add-on installed on a Netlify site.

    The instance's `config` and `env` objects are not ingested: they hold the add-on's
    provisioned credentials, and `auth_url` is a pre-authenticated sign-in link.
    """

    label: str = "NetlifyServiceInstance"
    properties: NetlifyServiceInstanceNodeProperties = (
        NetlifyServiceInstanceNodeProperties()
    )
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([THIRD_PARTY_APP])
    sub_resource_relationship: NetlifyServiceInstanceToNetlifyAccountRel = (
        NetlifyServiceInstanceToNetlifyAccountRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [NetlifyServiceInstanceToSiteRel()],
    )
