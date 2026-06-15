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
class AnthropicApiKeyNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    name: PropertyRef = PropertyRef("name")
    status: PropertyRef = PropertyRef("status")
    created_at: PropertyRef = PropertyRef("created_at")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AnthropicApiKeyToOrganizationRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:AnthropicOrganization)-[:RESOURCE]->(:AnthropicApiKey)
class AnthropicApiKeyToOrganizationRel(CartographyRelSchema):
    target_node_label: str = "AnthropicOrganization"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ORG_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: AnthropicApiKeyToOrganizationRelProperties = (
        AnthropicApiKeyToOrganizationRelProperties()
    )


@dataclass(frozen=True)
class AnthropicApiKeyToUserRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# DEPRECATED: replaced by the canonical (:APIKey)-[:OWNED_BY]->(:UserAccount)
# edge (AnthropicApiKeyToUserOwnedByRel). Kept for backward compatibility, will
# be removed in v1.0.0.
# (:AnthropicUser)-[:OWNS]->(:AnthropicApiKey)
class AnthropicApiKeyToUserRel(CartographyRelSchema):
    target_node_label: str = "AnthropicUser"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("created_by.id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "OWNS"
    properties: AnthropicApiKeyToUserRelProperties = (
        AnthropicApiKeyToUserRelProperties()
    )


@dataclass(frozen=True)
class AnthropicApiKeyToUserOwnedByRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# Canonical ontology edge: (:APIKey)-[:OWNED_BY]->(:UserAccount)
class AnthropicApiKeyToUserOwnedByRel(CartographyRelSchema):
    target_node_label: str = "AnthropicUser"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("created_by.id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "OWNED_BY"
    properties: AnthropicApiKeyToUserOwnedByRelProperties = (
        AnthropicApiKeyToUserOwnedByRelProperties()
    )


@dataclass(frozen=True)
class AnthropicApiKeyToWorkspaceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:AnthropicWorkspace)-[:CONTAINS]->(:AnthropicApiKey)
class AnthropicApiKeyToWorkspaceRel(CartographyRelSchema):
    target_node_label: str = "AnthropicWorkspace"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("workspace_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "CONTAINS"
    properties: AnthropicApiKeyToWorkspaceRelProperties = (
        AnthropicApiKeyToWorkspaceRelProperties()
    )


@dataclass(frozen=True)
class AnthropicApiKeySchema(CartographyNodeSchema):
    label: str = "AnthropicApiKey"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(
        ["APIKey"]
    )  # APIKey label is used for ontology mapping
    properties: AnthropicApiKeyNodeProperties = AnthropicApiKeyNodeProperties()
    sub_resource_relationship: AnthropicApiKeyToOrganizationRel = (
        AnthropicApiKeyToOrganizationRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            AnthropicApiKeyToUserRel(),
            AnthropicApiKeyToUserOwnedByRel(),
            AnthropicApiKeyToWorkspaceRel(),
        ],
    )
