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


@dataclass(frozen=True)
class WorkOSApplicationClientSecretNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    secret_hint: PropertyRef = PropertyRef("secret_hint")
    last_used_at: PropertyRef = PropertyRef("last_used_at")
    created_at: PropertyRef = PropertyRef("created_at")
    updated_at: PropertyRef = PropertyRef("updated_at")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class WorkOSApplicationClientSecretToEnvironmentRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:WorkOSEnvironment)-[:RESOURCE]->(:WorkOSApplicationClientSecret)
class WorkOSApplicationClientSecretToEnvironmentRel(CartographyRelSchema):
    target_node_label: str = "WorkOSEnvironment"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("WORKOS_CLIENT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: WorkOSApplicationClientSecretToEnvironmentRelProperties = (
        WorkOSApplicationClientSecretToEnvironmentRelProperties()
    )


@dataclass(frozen=True)
class WorkOSApplicationClientSecretToApplicationRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:WorkOSApplication)-[:HAS_SECRET]->(:WorkOSApplicationClientSecret)
class WorkOSApplicationClientSecretToApplicationRel(CartographyRelSchema):
    target_node_label: str = "WorkOSApplication"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("application_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS_SECRET"
    properties: WorkOSApplicationClientSecretToApplicationRelProperties = (
        WorkOSApplicationClientSecretToApplicationRelProperties()
    )


@dataclass(frozen=True)
class WorkOSApplicationClientSecretSchema(CartographyNodeSchema):
    label: str = "WorkOSApplicationClientSecret"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["APIKey"])
    properties: WorkOSApplicationClientSecretNodeProperties = (
        WorkOSApplicationClientSecretNodeProperties()
    )
    sub_resource_relationship: WorkOSApplicationClientSecretToEnvironmentRel = (
        WorkOSApplicationClientSecretToEnvironmentRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        rels=[WorkOSApplicationClientSecretToApplicationRel()],
    )
