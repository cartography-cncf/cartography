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
class WorkOSAPIKeyNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    name: PropertyRef = PropertyRef("name")
    obfuscated_value: PropertyRef = PropertyRef("obfuscated_value")
    permissions: PropertyRef = PropertyRef("permissions")
    created_at: PropertyRef = PropertyRef("created_at")
    updated_at: PropertyRef = PropertyRef("updated_at")
    last_used_at: PropertyRef = PropertyRef("last_used_at")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class WorkOSAPIKeyToEnvironmentRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:WorkOSEnvironment)-[:RESOURCE]->(:WorkOSAPIKey)
class WorkOSAPIKeyToEnvironmentRel(CartographyRelSchema):
    target_node_label: str = "WorkOSEnvironment"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("WORKOS_CLIENT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: WorkOSAPIKeyToEnvironmentRelProperties = (
        WorkOSAPIKeyToEnvironmentRelProperties()
    )


@dataclass(frozen=True)
class WorkOSAPIKeyToOrganizationRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:WorkOSOrganization)-[:OWNS]->(:WorkOSAPIKey)
class WorkOSAPIKeyToOrganizationRel(CartographyRelSchema):
    target_node_label: str = "WorkOSOrganization"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("org_owner_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "OWNS"
    properties: WorkOSAPIKeyToOrganizationRelProperties = (
        WorkOSAPIKeyToOrganizationRelProperties()
    )


@dataclass(frozen=True)
class WorkOSAPIKeyToUserRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:WorkOSUser)-[:OWNS]->(:WorkOSAPIKey)
class WorkOSAPIKeyToUserRel(CartographyRelSchema):
    target_node_label: str = "WorkOSUser"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("user_owner_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "OWNS"
    properties: WorkOSAPIKeyToUserRelProperties = WorkOSAPIKeyToUserRelProperties()


@dataclass(frozen=True)
class WorkOSAPIKeySchema(CartographyNodeSchema):
    label: str = "WorkOSAPIKey"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["APIKey"])
    properties: WorkOSAPIKeyNodeProperties = WorkOSAPIKeyNodeProperties()
    sub_resource_relationship: WorkOSAPIKeyToEnvironmentRel = (
        WorkOSAPIKeyToEnvironmentRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        rels=[WorkOSAPIKeyToOrganizationRel(), WorkOSAPIKeyToUserRel()],
    )
