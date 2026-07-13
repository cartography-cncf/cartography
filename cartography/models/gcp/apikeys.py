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
class GCPApiKeyNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", extra_index=True)
    uid: PropertyRef = PropertyRef("uid")
    name: PropertyRef = PropertyRef("name")
    display_name: PropertyRef = PropertyRef("displayName")
    create_time: PropertyRef = PropertyRef("createTime")
    update_time: PropertyRef = PropertyRef("updateTime")
    delete_time: PropertyRef = PropertyRef("deleteTime")
    # Whether the key has any API/application restrictions. An unrestricted key
    # can call any enabled API from anywhere, so this is the security-relevant bit.
    restricted: PropertyRef = PropertyRef("restricted")
    restrictions: PropertyRef = PropertyRef("restrictions")
    etag: PropertyRef = PropertyRef("etag")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GCPApiKeyToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GCPApiKeyToProjectRel(CartographyRelSchema):
    target_node_label: str = "GCPProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("PROJECT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: GCPApiKeyToProjectRelProperties = GCPApiKeyToProjectRelProperties()


@dataclass(frozen=True)
class GCPApiKeySchema(CartographyNodeSchema):
    label: str = "GCPApiKey"
    # APIKey label is used for ontology mapping. These are the real
    # apikeys.googleapis.com keys, distinct from GCPServiceAccountKey.
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["APIKey"])
    properties: GCPApiKeyNodeProperties = GCPApiKeyNodeProperties()
    sub_resource_relationship: GCPApiKeyToProjectRel = GCPApiKeyToProjectRel()
