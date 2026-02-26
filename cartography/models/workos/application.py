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
class WorkOSApplicationNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    client_id: PropertyRef = PropertyRef("client_id", extra_index=True)
    name: PropertyRef = PropertyRef("name")
    description: PropertyRef = PropertyRef("description")
    application_type: PropertyRef = PropertyRef("application_type")
    redirect_uris: PropertyRef = PropertyRef("redirect_uris")
    uses_pkce: PropertyRef = PropertyRef("uses_pkce")
    is_first_party: PropertyRef = PropertyRef("is_first_party")
    was_dynamically_registered: PropertyRef = PropertyRef("was_dynamically_registered")
    scopes: PropertyRef = PropertyRef("scopes")
    created_at: PropertyRef = PropertyRef("created_at")
    updated_at: PropertyRef = PropertyRef("updated_at")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class WorkOSApplicationToEnvironmentRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:WorkOSEnvironment)-[:RESOURCE]->(:WorkOSApplication)
class WorkOSApplicationToEnvironmentRel(CartographyRelSchema):
    target_node_label: str = "WorkOSEnvironment"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("WORKOS_CLIENT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: WorkOSApplicationToEnvironmentRelProperties = (
        WorkOSApplicationToEnvironmentRelProperties()
    )


@dataclass(frozen=True)
class WorkOSApplicationToOrganizationRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:WorkOSApplication)-[:BELONGS_TO]->(:WorkOSOrganization)
class WorkOSApplicationToOrganizationRel(CartographyRelSchema):
    target_node_label: str = "WorkOSOrganization"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("organization_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "BELONGS_TO"
    properties: WorkOSApplicationToOrganizationRelProperties = (
        WorkOSApplicationToOrganizationRelProperties()
    )


@dataclass(frozen=True)
class WorkOSApplicationSchema(CartographyNodeSchema):
    label: str = "WorkOSApplication"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["ThirdPartyApp"])
    properties: WorkOSApplicationNodeProperties = WorkOSApplicationNodeProperties()
    sub_resource_relationship: WorkOSApplicationToEnvironmentRel = (
        WorkOSApplicationToEnvironmentRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        rels=[WorkOSApplicationToOrganizationRel()],
    )
