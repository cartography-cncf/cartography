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
class WorkOSUserNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    email: PropertyRef = PropertyRef("email", extra_index=True)
    first_name: PropertyRef = PropertyRef("first_name")
    last_name: PropertyRef = PropertyRef("last_name")
    email_verified: PropertyRef = PropertyRef("email_verified")
    profile_picture_url: PropertyRef = PropertyRef("profile_picture_url")
    last_sign_in_at: PropertyRef = PropertyRef("last_sign_in_at")
    created_at: PropertyRef = PropertyRef("created_at")
    updated_at: PropertyRef = PropertyRef("updated_at")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class WorkOSUserToEnvironmentRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:WorkOSEnvironment)-[:RESOURCE]->(:WorkOSUser)
class WorkOSUserToEnvironmentRel(CartographyRelSchema):
    target_node_label: str = "WorkOSEnvironment"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("WORKOS_CLIENT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: WorkOSUserToEnvironmentRelProperties = (
        WorkOSUserToEnvironmentRelProperties()
    )


@dataclass(frozen=True)
class WorkOSUserSchema(CartographyNodeSchema):
    label: str = "WorkOSUser"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["UserAccount"])
    properties: WorkOSUserNodeProperties = WorkOSUserNodeProperties()
    sub_resource_relationship: WorkOSUserToEnvironmentRel = WorkOSUserToEnvironmentRel()
