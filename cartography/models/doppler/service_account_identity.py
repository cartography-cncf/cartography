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
class DopplerServiceAccountIdentityNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("slug")
    name: PropertyRef = PropertyRef("name")
    method: PropertyRef = PropertyRef("method")
    ttl_seconds: PropertyRef = PropertyRef("ttl_seconds")
    created_at: PropertyRef = PropertyRef("created_at")
    last_seen_at: PropertyRef = PropertyRef("last_seen_at")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class DopplerServiceAccountIdentityToWorkplaceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:DopplerWorkplace)-[:RESOURCE]->(:DopplerServiceAccountIdentity)
class DopplerServiceAccountIdentityToWorkplaceRel(CartographyRelSchema):
    target_node_label: str = "DopplerWorkplace"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("WORKPLACE_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: DopplerServiceAccountIdentityToWorkplaceRelProperties = (
        DopplerServiceAccountIdentityToWorkplaceRelProperties()
    )


@dataclass(frozen=True)
class DopplerServiceAccountIdentityToAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:DopplerServiceAccount)-[:HAS_IDENTITY]->(:DopplerServiceAccountIdentity)
class DopplerServiceAccountIdentityToAccountRel(CartographyRelSchema):
    target_node_label: str = "DopplerServiceAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("service_account_slug")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS_IDENTITY"
    properties: DopplerServiceAccountIdentityToAccountRelProperties = (
        DopplerServiceAccountIdentityToAccountRelProperties()
    )


@dataclass(frozen=True)
class DopplerServiceAccountIdentitySchema(CartographyNodeSchema):
    label: str = "DopplerServiceAccountIdentity"
    properties: DopplerServiceAccountIdentityNodeProperties = (
        DopplerServiceAccountIdentityNodeProperties()
    )
    sub_resource_relationship: DopplerServiceAccountIdentityToWorkplaceRel = (
        DopplerServiceAccountIdentityToWorkplaceRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [DopplerServiceAccountIdentityToAccountRel()],
    )
