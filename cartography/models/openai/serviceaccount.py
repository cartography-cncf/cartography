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


@dataclass(frozen=True)
class OpenAIServiceAccountNodeProperties(CartographyNodeProperties):
    object: PropertyRef = PropertyRef(
        "object",
        description='Object type, always "organization.project.service_account".',
    )
    id: PropertyRef = PropertyRef("id", description="OpenAI service account ID.")
    name: PropertyRef = PropertyRef("name", description="Service account name.")
    role: PropertyRef = PropertyRef(
        "role",
        description="Project role: owner or member.",
    )
    created_at: PropertyRef = PropertyRef(
        "created_at",
        description="Unix timestamp when the service account was created.",
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last update.",
    )


@dataclass(frozen=True)
class OpenAIServiceAccountToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:OpenAIServiceAccount)<-[:RESOURCE]-(:OpenAIProject)
class OpenAIServiceAccountToProjectRel(CartographyRelSchema):
    """The project contains the service account."""

    target_node_label: str = "OpenAIProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("project_id", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: OpenAIServiceAccountToProjectRelProperties = (
        OpenAIServiceAccountToProjectRelProperties()
    )


@dataclass(frozen=True)
class OpenAIServiceAccountSchema(CartographyNodeSchema):
    """A service account in an OpenAI project."""

    label: str = "OpenAIServiceAccount"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["ServiceAccount"])
    properties: OpenAIServiceAccountNodeProperties = (
        OpenAIServiceAccountNodeProperties()
    )
    sub_resource_relationship: OpenAIServiceAccountToProjectRel = (
        OpenAIServiceAccountToProjectRel()
    )
