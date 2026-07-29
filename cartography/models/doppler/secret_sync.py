from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import OtherRelationships
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class DopplerSecretSyncNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("slug")
    enabled: PropertyRef = PropertyRef("enabled")
    last_synced_at: PropertyRef = PropertyRef("last_synced_at")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class DopplerSecretSyncToWorkplaceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:DopplerWorkplace)-[:RESOURCE]->(:DopplerSecretSync)
class DopplerSecretSyncToWorkplaceRel(CartographyRelSchema):
    target_node_label: str = "DopplerWorkplace"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("WORKPLACE_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: DopplerSecretSyncToWorkplaceRelProperties = (
        DopplerSecretSyncToWorkplaceRelProperties()
    )


@dataclass(frozen=True)
class DopplerSecretSyncToIntegrationRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:DopplerSecretSync)-[:USES]->(:DopplerIntegration)
class DopplerSecretSyncToIntegrationRel(CartographyRelSchema):
    target_node_label: str = "DopplerIntegration"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("integration_slug")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "USES"
    properties: DopplerSecretSyncToIntegrationRelProperties = (
        DopplerSecretSyncToIntegrationRelProperties()
    )


@dataclass(frozen=True)
class DopplerSecretSyncToConfigRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:DopplerSecretSync)-[:SYNCS]->(:DopplerConfig)
class DopplerSecretSyncToConfigRel(CartographyRelSchema):
    target_node_label: str = "DopplerConfig"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("config_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "SYNCS"
    properties: DopplerSecretSyncToConfigRelProperties = (
        DopplerSecretSyncToConfigRelProperties()
    )


@dataclass(frozen=True)
class DopplerSecretSyncSchema(CartographyNodeSchema):
    label: str = "DopplerSecretSync"
    properties: DopplerSecretSyncNodeProperties = DopplerSecretSyncNodeProperties()
    sub_resource_relationship: DopplerSecretSyncToWorkplaceRel = (
        DopplerSecretSyncToWorkplaceRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [DopplerSecretSyncToIntegrationRel(), DopplerSecretSyncToConfigRel()],
    )
