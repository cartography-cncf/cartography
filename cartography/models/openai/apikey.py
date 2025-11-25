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
    object: PropertyRef = PropertyRef("object")
    name: PropertyRef = PropertyRef("name")
    created_at: PropertyRef = PropertyRef("created_at")
    last_used_at: PropertyRef = PropertyRef("last_used_at")
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class OpenAIApiKeyToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:OpenAIApiKey)<-[:RESOURCE]-(:OpenAIProject)
class OpenAIApiKeyToProjectRel(CartographyRelSchema):
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
# (:OpenAIUser)-[:OWNS]->(:OpenAIApiKey)
class OpenAIApiKeyToUserRel(CartographyRelSchema):
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
# (:OpenAIServiceAccount)-[:OWNS]->(:OpenAIApiKey)
class OpenAIApiKeyToSARel(CartographyRelSchema):
    target_node_label: str = "OpenAIServiceAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("owner_sa_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "OWNS"
    properties: OpenAIApiKeyToSARelProperties = OpenAIApiKeyToSARelProperties()


@dataclass(frozen=True)
class OpenAIApiKeySchema(CartographyNodeSchema):
    label: str = "OpenAIApiKey"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(
        ["APIKey"]
    )  # APIKey label is used for ontology mapping
    properties: OpenAIApiKeyNodeProperties = OpenAIApiKeyNodeProperties()
    sub_resource_relationship: OpenAIApiKeyToProjectRel = OpenAIApiKeyToProjectRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [OpenAIApiKeyToUserRel(), OpenAIApiKeyToSARel()],
    )
