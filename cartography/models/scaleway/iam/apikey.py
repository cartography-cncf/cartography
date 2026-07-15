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
    id: PropertyRef = PropertyRef(
        "access_key", description="Access key of the API key."
    )
    description: PropertyRef = PropertyRef(
        "description", description="Description of API key."
    )
    created_at: PropertyRef = PropertyRef(
        "created_at", description="Date and time of API key creation."
    )
    updated_at: PropertyRef = PropertyRef(
        "updated_at", description="Date and time of last API key update."
    )
    expires_at: PropertyRef = PropertyRef(
        "expires_at", description="Date and time of API key expiration."
    )
    default_project_id: PropertyRef = PropertyRef(
        "default_project_id",
        description="Default Project ID specified for this API key.",
    )
    editable: PropertyRef = PropertyRef(
        "editable", description="Defines whether or not the API key is editable."
    )
    deletable: PropertyRef = PropertyRef(
        "deletable", description="Defines whether or not the API key is deletable."
    )
    managed: PropertyRef = PropertyRef(
        "managed", description="Defines whether or not the API key is managed."
    )
    creation_ip: PropertyRef = PropertyRef(
        "creation_ip", description="IP address of the device that created the API key."
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated", set_in_kwargs=True, description="Timestamp of the last update"
    )


@dataclass(frozen=True)
class ScalewayApiKeyToUserRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# DEPRECATED: replaced by the canonical (:APIKey)-[:OWNED_BY]->(:UserAccount)
# edge (ScalewayApiKeyToUserOwnedByRel). Kept for backward compatibility, will
# be removed in v1.0.0.
# (:ScalewayUser)-[:HAS]->(:ScalewayApiKey)
class ScalewayApiKeyToUserRel(CartographyRelSchema):
    """Connects `ScalewayUser` to `ScalewayApiKey` through `HAS`."""

    target_node_label: str = "ScalewayUser"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("user_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS"
    properties: ScalewayApiKeyToUserRelProperties = ScalewayApiKeyToUserRelProperties()


@dataclass(frozen=True)
class ScalewayApiKeyToApplicationRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# DEPRECATED: replaced by the canonical (:APIKey)-[:OWNED_BY]->(:ServiceAccount)
# edge (ScalewayApiKeyToApplicationOwnedByRel). Kept for backward compatibility,
# will be removed in v1.0.0.
# (:ScalewayApplication)-[:HAS]->(:ScalewayApiKey)
class ScalewayApiKeyToApplicationRel(CartographyRelSchema):
    """Connects `ScalewayApplication` to `ScalewayApiKey` through `HAS`."""

    target_node_label: str = "ScalewayApplication"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("application_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS"
    properties: ScalewayApiKeyToApplicationRelProperties = (
        ScalewayApiKeyToApplicationRelProperties()
    )


@dataclass(frozen=True)
class ScalewayApiKeyToUserOwnedByRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# Canonical ontology edge: (:APIKey)-[:OWNED_BY]->(:UserAccount)
class ScalewayApiKeyToUserOwnedByRel(CartographyRelSchema):
    """Connects `ScalewayApiKey` to `ScalewayUser` through `OWNED_BY`."""

    target_node_label: str = "ScalewayUser"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("user_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "OWNED_BY"
    properties: ScalewayApiKeyToUserOwnedByRelProperties = (
        ScalewayApiKeyToUserOwnedByRelProperties()
    )


@dataclass(frozen=True)
class ScalewayApiKeyToApplicationOwnedByRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# Canonical ontology edge: (:APIKey)-[:OWNED_BY]->(:ServiceAccount)
class ScalewayApiKeyToApplicationOwnedByRel(CartographyRelSchema):
    """Connects `ScalewayApiKey` to `ScalewayApplication` through `OWNED_BY`."""

    target_node_label: str = "ScalewayApplication"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("application_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "OWNED_BY"
    properties: ScalewayApiKeyToApplicationOwnedByRelProperties = (
        ScalewayApiKeyToApplicationOwnedByRelProperties()
    )


@dataclass(frozen=True)
class ScalewayApiKeyToOrganizationRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:ScalewayOrganization)-[:RESOURCE]->(:ScalewayApiKey)
class ScalewayApiKeyToOrganizationRel(CartographyRelSchema):
    """Connects `ScalewayOrganization` to `ScalewayApiKey` through `RESOURCE`."""

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
    """Represents an ApiKey in Scaleway."""

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
            ScalewayApiKeyToUserOwnedByRel(),
            ScalewayApiKeyToApplicationOwnedByRel(),
        ]
    )
