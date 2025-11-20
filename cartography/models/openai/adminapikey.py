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
class OpenAIAdminApiKeyNodeProperties(CartographyNodeProperties):
    object: PropertyRef = PropertyRef("object")
    id: PropertyRef = PropertyRef("id")
    name: PropertyRef = PropertyRef("name")
    created_at: PropertyRef = PropertyRef("created_at")
    last_used_at: PropertyRef = PropertyRef("last_used_at")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class OpenAIAdminApiKeyToOrganizationRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:OpenAIOrganization)-[:RESOURCE]->(:OpenAIAdminApiKey)
class OpenAIAdminApiKeyToOrganizationRel(CartographyRelSchema):
    target_node_label: str = "OpenAIOrganization"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ORG_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: OpenAIAdminApiKeyToOrganizationRelProperties = (
        OpenAIAdminApiKeyToOrganizationRelProperties()
    )


@dataclass(frozen=True)
class OpenAIAdminApiKeyToUserRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:OpenAIUser)-[:OWNS]->(:OpenAIAdminApiKey)
class OpenAIAdminApiKeyToUserRel(CartographyRelSchema):
    target_node_label: str = "OpenAIUser"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("owner_user_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "OWNS"
    properties: OpenAIAdminApiKeyToUserRelProperties = (
        OpenAIAdminApiKeyToUserRelProperties()
    )


@dataclass(frozen=True)
class OpenAIAdminApiKeyToSARelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:OpenAIServiceAccount)-[:OWNS]->(:OpenAIAdminApiKey)
class OpenAIAdminApiKeyToSARel(CartographyRelSchema):
    target_node_label: str = "OpenAIServiceAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("owner_sa_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "OWNS"
    properties: OpenAIAdminApiKeyToSARelProperties = (
        OpenAIAdminApiKeyToSARelProperties()
    )


@dataclass(frozen=True)
class OpenAIAdminApiKeySchema(CartographyNodeSchema):
    label: str = "OpenAIAdminApiKey"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(
        ["APIKey"]
    )  # APIKey label is used for ontology mapping
    properties: OpenAIAdminApiKeyNodeProperties = OpenAIAdminApiKeyNodeProperties()
    sub_resource_relationship: OpenAIAdminApiKeyToOrganizationRel = (
        OpenAIAdminApiKeyToOrganizationRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [OpenAIAdminApiKeyToUserRel(), OpenAIAdminApiKeyToSARel()],
    )
