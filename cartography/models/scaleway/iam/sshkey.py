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
class ScalewaySSHKeyProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", description="ID of the SSH key.")
    name: PropertyRef = PropertyRef("name", description="Name of the SSH key.")
    public_key: PropertyRef = PropertyRef(
        "public_key", description="Public key material."
    )
    fingerprint: PropertyRef = PropertyRef(
        "fingerprint", description="Fingerprint of the SSH key."
    )
    disabled: PropertyRef = PropertyRef(
        "disabled", description="Defines whether or not the SSH key is disabled."
    )
    created_at: PropertyRef = PropertyRef(
        "created_at", description="Date and time of SSH key creation."
    )
    updated_at: PropertyRef = PropertyRef(
        "updated_at", description="Date and time of last SSH key update."
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated", set_in_kwargs=True, description="Timestamp of the last update"
    )


@dataclass(frozen=True)
class ScalewaySSHKeyToOrganizationRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:ScalewayOrganization)-[:RESOURCE]->(:ScalewaySSHKey)
class ScalewaySSHKeyToOrganizationRel(CartographyRelSchema):
    """Connects `ScalewayOrganization` to `ScalewaySSHKey` through `RESOURCE`."""

    target_node_label: str = "ScalewayOrganization"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ORG_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: ScalewaySSHKeyToOrganizationRelProperties = (
        ScalewaySSHKeyToOrganizationRelProperties()
    )


@dataclass(frozen=True)
class ScalewaySSHKeyToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:ScalewayProject)-[:RESOURCE]->(:ScalewaySSHKey)
class ScalewaySSHKeyToProjectRel(CartographyRelSchema):
    """Connects `ScalewayProject` to `ScalewaySSHKey` through `RESOURCE`."""

    target_node_label: str = "ScalewayProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("project_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: ScalewaySSHKeyToProjectRelProperties = (
        ScalewaySSHKeyToProjectRelProperties()
    )


@dataclass(frozen=True)
class ScalewaySSHKeySchema(CartographyNodeSchema):
    """Represents an SSH key registered in Scaleway IAM."""

    label: str = "ScalewaySSHKey"
    properties: ScalewaySSHKeyProperties = ScalewaySSHKeyProperties()
    sub_resource_relationship: ScalewaySSHKeyToOrganizationRel = (
        ScalewaySSHKeyToOrganizationRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            ScalewaySSHKeyToProjectRel(),
        ]
    )
