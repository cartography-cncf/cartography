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
from cartography.models.ontology.labels import API_KEY


@dataclass(frozen=True)
class TencentCloudCAMAccessKeyNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id", description="SecretId of the API key. The SecretKey is never read."
    )
    status: PropertyRef = PropertyRef(
        "status", description="Key status: `Active` or `Inactive`."
    )
    description: PropertyRef = PropertyRef(
        "description", description="Free-form description of the key."
    )
    create_time: PropertyRef = PropertyRef(
        "create_time", description="Time the key was created."
    )
    last_used_date: PropertyRef = PropertyRef(
        "last_used_date",
        description="Last date the key was used to call an API. Tencent Cloud reports it with a one-day delay.",
    )
    user_uin: PropertyRef = PropertyRef(
        "user_uin", description="UIN of the CAM sub-user that owns the key."
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class TencentCloudCAMAccessKeyToAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:TencentCloudAccount)-[:RESOURCE]->(:TencentCloudCAMAccessKey)
class TencentCloudCAMAccessKeyToAccountRel(CartographyRelSchema):
    """Connects a `TencentCloudAccount` to the API keys of its CAM sub-users."""

    target_node_label: str = "TencentCloudAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ACCOUNT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: TencentCloudCAMAccessKeyToAccountRelProperties = (
        TencentCloudCAMAccessKeyToAccountRelProperties()
    )


@dataclass(frozen=True)
class TencentCloudCAMAccessKeyToUserRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:TencentCloudCAMAccessKey)-[:OWNED_BY]->(:TencentCloudCAMUser)
class TencentCloudCAMAccessKeyToUserRel(CartographyRelSchema):
    """Connects an API key to the CAM sub-user it authenticates as."""

    target_node_label: str = "TencentCloudCAMUser"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("user_uin")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "OWNED_BY"
    properties: TencentCloudCAMAccessKeyToUserRelProperties = (
        TencentCloudCAMAccessKeyToUserRelProperties()
    )


@dataclass(frozen=True)
class TencentCloudCAMAccessKeySchema(CartographyNodeSchema):
    """A long-lived API key (SecretId/SecretKey pair) belonging to a CAM sub-user."""

    label: str = "TencentCloudCAMAccessKey"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([API_KEY])
    properties: TencentCloudCAMAccessKeyNodeProperties = (
        TencentCloudCAMAccessKeyNodeProperties()
    )
    sub_resource_relationship: TencentCloudCAMAccessKeyToAccountRel = (
        TencentCloudCAMAccessKeyToAccountRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [TencentCloudCAMAccessKeyToUserRel()],
    )
