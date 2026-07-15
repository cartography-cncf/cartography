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
class GCPNicAccessConfigNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "access_config_id",
        description="A partial resource URI representing this AccessConfig.  Note: GCP does not define a partial resource URI for AccessConfigs, so we create one so we can uniquely identify GCP network interface access configs.  Has the form `projects/{project_name}/zones/{zone_name}/instances/{instance_name}/networkinterfaces/{network interface name}/accessconfigs/{access config type}`.",
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last time the node was updated.",
    )
    type: PropertyRef = PropertyRef(
        "type",
        description='The type of configuration. GCP docs say: "The default and only option is ONE_TO_ONE_NAT.".',
    )
    name: PropertyRef = PropertyRef(
        "name",
        description="The name of this access configuration. The default and recommended name is External NAT, but you can use any arbitrary string, such as My external IP or Network Access.",
    )
    public_ip: PropertyRef = PropertyRef(
        "natIP", description="The external IP associated with this instance."
    )
    set_public_ptr: PropertyRef = PropertyRef(
        "setPublicPtr",
        description="Specifies whether a public DNS 'PTR' record should be created to map the external IP address of the instance to a DNS domain name.",
    )
    public_ptr_domain_name: PropertyRef = PropertyRef(
        "publicPtrDomainName",
        description="The DNS domain name for the public PTR record. You can set this field only if the setPublicPtr field is enabled.",
    )
    network_tier: PropertyRef = PropertyRef(
        "networkTier",
        description="This signifies the networking tier used for configuring this access configuration and can only take the following values: PREMIUM, STANDARD.",
    )


@dataclass(frozen=True)
class GCPNicAccessConfigToNicRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last sync that observed this data.",
    )


@dataclass(frozen=True)
class GCPNicAccessConfigToNicRel(CartographyRelSchema):
    target_node_label: str = "GCPNetworkInterface"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef("nic_id"),
        }
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: GCPNicAccessConfigToNicRelProperties = (
        GCPNicAccessConfigToNicRelProperties()
    )


@dataclass(frozen=True)
class GCPNicAccessConfigToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last sync that observed this data.",
    )


@dataclass(frozen=True)
class GCPNicAccessConfigToProjectRel(CartographyRelSchema):
    target_node_label: str = "GCPProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef("PROJECT_ID", set_in_kwargs=True),
        }
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: GCPNicAccessConfigToProjectRelProperties = (
        GCPNicAccessConfigToProjectRelProperties()
    )


@dataclass(frozen=True)
class GCPNicAccessConfigSchema(CartographyNodeSchema):
    """Representation of the AccessConfig object on a GCP Instance's [network interface](https://cloud.google.com/compute/docs/reference/rest/v1/instances/list) (scroll down to the fields on "networkInterface")."""

    label: str = "GCPNicAccessConfig"
    properties: GCPNicAccessConfigNodeProperties = GCPNicAccessConfigNodeProperties()
    sub_resource_relationship: GCPNicAccessConfigToProjectRel = (
        GCPNicAccessConfigToProjectRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            GCPNicAccessConfigToNicRel(),
        ]
    )
