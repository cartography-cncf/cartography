from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import OtherRelationships
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class FlyAccessTokenNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", description="Fly token ID.")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef(
        "name", extra_index=True, description="Token name."
    )
    expires_at: PropertyRef = PropertyRef(
        "expires_at", description="Token expiration timestamp."
    )
    revoked_at: PropertyRef = PropertyRef(
        "revoked_at", description="Token revocation timestamp, if revoked."
    )
    revoked: PropertyRef = PropertyRef(
        "revoked", description="Whether the token is revoked."
    )
    user_id: PropertyRef = PropertyRef(
        "user_id", description="ID of the user who created the token, if returned."
    )
    user_name: PropertyRef = PropertyRef(
        "user_name", description="Name of the user who created the token, if returned."
    )
    user_email: PropertyRef = PropertyRef(
        "user_email",
        description="Email of the user who created the token, if returned.",
    )


@dataclass(frozen=True)
class FlyAccessTokenRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:FlyOrganization)-[:RESOURCE]->(:FlyAccessToken)
class FlyAccessTokenToOrganizationRel(CartographyRelSchema):
    """Connects `FlyOrganization` to `FlyAccessToken` through `RESOURCE`."""

    target_node_label: str = "FlyOrganization"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ORGANIZATION_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: FlyAccessTokenRelProperties = FlyAccessTokenRelProperties()


@dataclass(frozen=True)
# (:FlyApp)-[:RESOURCE]->(:FlyAccessToken)
class FlyAccessTokenToAppRel(CartographyRelSchema):
    """Connects `FlyApp` to `FlyAccessToken` through `RESOURCE`."""

    target_node_label: str = "FlyApp"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("APP_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: FlyAccessTokenRelProperties = FlyAccessTokenRelProperties()


@dataclass(frozen=True)
# (:FlyAccessToken)-[:CREATED_BY]->(:FlyUser)
class FlyAccessTokenToUserRel(CartographyRelSchema):
    """Connects `FlyAccessToken` to the Fly user who created it."""

    target_node_label: str = "FlyUser"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("user_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "CREATED_BY"
    properties: FlyAccessTokenRelProperties = FlyAccessTokenRelProperties()


@dataclass(frozen=True)
class FlyOrganizationAccessTokenSchema(CartographyNodeSchema):
    """Represents Fly.io organization access token metadata."""

    label: str = "FlyAccessToken"
    properties: FlyAccessTokenNodeProperties = FlyAccessTokenNodeProperties()
    sub_resource_relationship: FlyAccessTokenToOrganizationRel = (
        FlyAccessTokenToOrganizationRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [FlyAccessTokenToUserRel()],
    )


@dataclass(frozen=True)
class FlyAppAccessTokenSchema(CartographyNodeSchema):
    """Represents Fly.io app access token metadata."""

    label: str = "FlyAccessToken"
    properties: FlyAccessTokenNodeProperties = FlyAccessTokenNodeProperties()
    sub_resource_relationship: FlyAccessTokenToAppRel = FlyAccessTokenToAppRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [FlyAccessTokenToUserRel()],
    )
