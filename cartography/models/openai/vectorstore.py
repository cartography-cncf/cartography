from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class OpenAIVectorStoreNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    object: PropertyRef = PropertyRef("object")
    created_at: PropertyRef = PropertyRef("created_at")
    name: PropertyRef = PropertyRef("name")
    usage_bytes: PropertyRef = PropertyRef("usage_bytes")
    file_counts_in_progress: PropertyRef = PropertyRef("file_counts.in_progress")
    file_counts_completed: PropertyRef = PropertyRef("file_counts.completed")
    file_counts_failed: PropertyRef = PropertyRef("file_counts.failed")
    file_counts_cancelled: PropertyRef = PropertyRef("file_counts.cancelled")
    file_counts_total: PropertyRef = PropertyRef("file_counts.total")
    status: PropertyRef = PropertyRef("status")
    expires_at: PropertyRef = PropertyRef("expires_at")
    last_active_at: PropertyRef = PropertyRef("last_active_at")
    expires_after_id: PropertyRef = PropertyRef("expires_after.id")
    metadata_id: PropertyRef = PropertyRef("metadata.id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class OpenAIVectorStoreToOrganizationRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:OpenAIOrganization)<-[:RESOURCE]->(:OpenAIVectorStore)
class OpenAIVectorStoreToOrganizationRel(CartographyRelSchema):
    target_node_label: str = "OpenAIOrganization"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ORG_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: OpenAIVectorStoreToOrganizationRelProperties = (
        OpenAIVectorStoreToOrganizationRelProperties()
    )


@dataclass(frozen=True)
class OpenAIVectorStoreSchema(CartographyNodeSchema):
    label: str = "OpenAIVectorStore"
    properties: OpenAIVectorStoreNodeProperties = OpenAIVectorStoreNodeProperties()
    sub_resource_relationship: OpenAIVectorStoreToOrganizationRel = (
        OpenAIVectorStoreToOrganizationRel()
    )
