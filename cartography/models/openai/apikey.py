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
class OpenAIApiKeyNodeProperties(CartographyNodeProperties):
    object: PropertyRef = PropertyRef(
        "object",
        description='Object type, always "organization.project.api_key".',
    )
    name: PropertyRef = PropertyRef("name", description="API key name.")
    created_at: PropertyRef = PropertyRef(
        "created_at",
        description="Unix timestamp when the API key was created.",
    )
    last_used_at: PropertyRef = PropertyRef(
        "last_used_at",
        description="Unix timestamp when the API key was last used.",
    )
    id: PropertyRef = PropertyRef("id", description="OpenAI API key ID.")
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last update.",
    )


@dataclass(frozen=True)
class OpenAIApiKeyToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:OpenAIApiKey)<-[:RESOURCE]-(:OpenAIProject)
class OpenAIApiKeyToProjectRel(CartographyRelSchema):
    """The project contains the API key."""

    target_node_label: str = "OpenAIProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("project_id", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: OpenAIApiKeyToProjectRelProperties = (
        OpenAIApiKeyToProjectRelProperties()
    )


@dataclass(frozen=True)
class OpenAIApiKeyToUserRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# DEPRECATED: replaced by the canonical (:APIKey)-[:OWNED_BY]->(:UserAccount)
# edge (OpenAIApiKeyToUserOwnedByRel). Kept for backward compatibility, will be
# removed in v1.0.0.
# (:OpenAIUser)-[:OWNS]->(:OpenAIApiKey)
class OpenAIApiKeyToUserRel(CartographyRelSchema):
    """Deprecated compatibility edge for a user that owns an API key."""

    target_node_label: str = "OpenAIUser"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("owner_user_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "OWNS"
    properties: OpenAIApiKeyToUserRelProperties = OpenAIApiKeyToUserRelProperties()


@dataclass(frozen=True)
class OpenAIApiKeyToSARelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# DEPRECATED: replaced by the canonical (:APIKey)-[:OWNED_BY]->(:ServiceAccount)
# edge (OpenAIApiKeyToSAOwnedByRel). Kept for backward compatibility, will be
# removed in v1.0.0.
# (:OpenAIServiceAccount)-[:OWNS]->(:OpenAIApiKey)
class OpenAIApiKeyToSARel(CartographyRelSchema):
    """Deprecated compatibility edge for a service account that owns an API key."""

    target_node_label: str = "OpenAIServiceAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("owner_sa_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "OWNS"
    properties: OpenAIApiKeyToSARelProperties = OpenAIApiKeyToSARelProperties()


@dataclass(frozen=True)
class OpenAIApiKeyToUserOwnedByRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# Canonical ontology edge: (:APIKey)-[:OWNED_BY]->(:UserAccount)
class OpenAIApiKeyToUserOwnedByRel(CartographyRelSchema):
    """An API key is owned by a user account."""

    target_node_label: str = "OpenAIUser"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("owner_user_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "OWNED_BY"
    properties: OpenAIApiKeyToUserOwnedByRelProperties = (
        OpenAIApiKeyToUserOwnedByRelProperties()
    )


@dataclass(frozen=True)
class OpenAIApiKeyToSAOwnedByRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# Canonical ontology edge: (:APIKey)-[:OWNED_BY]->(:ServiceAccount)
class OpenAIApiKeyToSAOwnedByRel(CartographyRelSchema):
    """An API key is owned by a service account."""

    target_node_label: str = "OpenAIServiceAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("owner_sa_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "OWNED_BY"
    properties: OpenAIApiKeyToSAOwnedByRelProperties = (
        OpenAIApiKeyToSAOwnedByRelProperties()
    )


@dataclass(frozen=True)
class OpenAIApiKeySchema(CartographyNodeSchema):
    """An API key in an OpenAI project."""

    label: str = "OpenAIApiKey"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(
        ["APIKey"]
    )  # APIKey label is used for ontology mapping
    properties: OpenAIApiKeyNodeProperties = OpenAIApiKeyNodeProperties()
    sub_resource_relationship: OpenAIApiKeyToProjectRel = OpenAIApiKeyToProjectRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            OpenAIApiKeyToUserRel(),
            OpenAIApiKeyToSARel(),
            OpenAIApiKeyToUserOwnedByRel(),
            OpenAIApiKeyToSAOwnedByRel(),
        ],
    )
