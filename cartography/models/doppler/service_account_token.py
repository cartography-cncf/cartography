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
class DopplerServiceAccountTokenNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("slug")
    name: PropertyRef = PropertyRef("name")
    created_at: PropertyRef = PropertyRef("created_at")
    expires_at: PropertyRef = PropertyRef("expires_at")
    last_seen_at: PropertyRef = PropertyRef("last_seen_at")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class DopplerServiceAccountTokenToWorkplaceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:DopplerWorkplace)-[:RESOURCE]->(:DopplerServiceAccountToken)
class DopplerServiceAccountTokenToWorkplaceRel(CartographyRelSchema):
    target_node_label: str = "DopplerWorkplace"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("WORKPLACE_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: DopplerServiceAccountTokenToWorkplaceRelProperties = (
        DopplerServiceAccountTokenToWorkplaceRelProperties()
    )


@dataclass(frozen=True)
class DopplerServiceAccountTokenToAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:DopplerServiceAccount)-[:HAS_TOKEN]->(:DopplerServiceAccountToken)
class DopplerServiceAccountTokenToAccountRel(CartographyRelSchema):
    target_node_label: str = "DopplerServiceAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("service_account_slug")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS_TOKEN"
    properties: DopplerServiceAccountTokenToAccountRelProperties = (
        DopplerServiceAccountTokenToAccountRelProperties()
    )


@dataclass(frozen=True)
class DopplerServiceAccountTokenSchema(CartographyNodeSchema):
    label: str = "DopplerServiceAccountToken"
    properties: DopplerServiceAccountTokenNodeProperties = (
        DopplerServiceAccountTokenNodeProperties()
    )
    sub_resource_relationship: DopplerServiceAccountTokenToWorkplaceRel = (
        DopplerServiceAccountTokenToWorkplaceRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [DopplerServiceAccountTokenToAccountRel()],
    )
