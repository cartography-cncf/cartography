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
class ScalewayApiKeyProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("access_key")
    description: PropertyRef = PropertyRef("description")
    created_at: PropertyRef = PropertyRef("created_at")
    updated_at: PropertyRef = PropertyRef("updated_at")
    expires_at: PropertyRef = PropertyRef("expires_at")
    default_project_id: PropertyRef = PropertyRef("default_project_id")
    editable: PropertyRef = PropertyRef("editable")
    deletable: PropertyRef = PropertyRef("deletable")
    managed: PropertyRef = PropertyRef("managed")
    creation_ip: PropertyRef = PropertyRef("creation_ip")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ScalewayApiKeyToUserProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:ScalewayUser)-[:HAS]->(:ScalewayApiKey)
class ScalewayApiKeyToUserRel(CartographyRelSchema):
    target_node_label: str = "ScalewayUser"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("user_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS"
    properties: ScalewayApiKeyToUserProperties = ScalewayApiKeyToUserProperties()


@dataclass(frozen=True)
class ScalewayApiKeyToApplicationProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:ScalewayApplication)-[:HAS]->(:ScalewayApiKey)
class ScalewayApiKeyToApplicationRel(CartographyRelSchema):
    target_node_label: str = "ScalewayApplication"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("application_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS"
    properties: ScalewayApiKeyToApplicationProperties = (
        ScalewayApiKeyToApplicationProperties()
    )


@dataclass(frozen=True)
class ScalewayApiKeyToOrganizationRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:ScalewayOrganization)-[:RESOURCE]->(:ScalewayApiKey)
class ScalewayApiKeyToOrganizationRel(CartographyRelSchema):
    target_node_label: str = "ScalewayOrganization"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ORG_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: ScalewayApiKeyToOrganizationRelProperties = (
        ScalewayApiKeyToOrganizationRelProperties()
    )


@dataclass(frozen=True)
class ScalewayApiKeySchema(CartographyNodeSchema):
    label: str = "ScalewayApiKey"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(
        ["APIKey"]
    )  # APIKey label is used for ontology mapping
    properties: ScalewayApiKeyProperties = ScalewayApiKeyProperties()
    sub_resource_relationship: ScalewayApiKeyToOrganizationRel = (
        ScalewayApiKeyToOrganizationRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            ScalewayApiKeyToUserRel(),
            ScalewayApiKeyToApplicationRel(),
        ]
    )
