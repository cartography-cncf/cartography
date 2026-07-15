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
class GCPCloudArmorPolicyNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "partial_uri", description="Stable identifier for this resource."
    )
    partial_uri: PropertyRef = PropertyRef("partial_uri", description="Same as `id`.")
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last time the node was updated.",
    )
    name: PropertyRef = PropertyRef(
        "name", extra_index=True, description="The name of the security policy."
    )
    self_link: PropertyRef = PropertyRef(
        "self_link", description="Server-defined URL for the resource."
    )
    project_id: PropertyRef = PropertyRef(
        "project_id", description="The project ID that this policy belongs to."
    )
    description: PropertyRef = PropertyRef(
        "description", description="An optional description of this security policy."
    )
    policy_type: PropertyRef = PropertyRef(
        "policy_type",
        description="The type of the security policy (e.g., `CLOUD_ARMOR`).",
    )
    creation_timestamp: PropertyRef = PropertyRef(
        "creation_timestamp", description="Creation timestamp of the resource."
    )


@dataclass(frozen=True)
class GCPCloudArmorPolicyToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last sync that observed this data.",
    )


@dataclass(frozen=True)
class GCPCloudArmorPolicyToProjectRel(CartographyRelSchema):
    target_node_label: str = "GCPProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef("PROJECT_ID", set_in_kwargs=True),
        },
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: GCPCloudArmorPolicyToProjectRelProperties = (
        GCPCloudArmorPolicyToProjectRelProperties()
    )


@dataclass(frozen=True)
class GCPCloudArmorPolicySchema(CartographyNodeSchema):
    """Representation of a GCP [Cloud Armor Security Policy](https://cloud.google.com/compute/docs/reference/rest/v1/securityPolicies). Cloud Armor policies provide DDoS protection and WAF capabilities for backend services."""

    label: str = "GCPCloudArmorPolicy"
    properties: GCPCloudArmorPolicyNodeProperties = GCPCloudArmorPolicyNodeProperties()
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["NetworkAccessControl"])
    sub_resource_relationship: GCPCloudArmorPolicyToProjectRel = (
        GCPCloudArmorPolicyToProjectRel()
    )
