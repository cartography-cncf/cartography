from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_source_node_matcher
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import OtherRelationships
from cartography.models.core.relationships import SourceNodeMatcher
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class AzureVirtualMachineProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef("name")
    location: PropertyRef = PropertyRef("location")
    resourcegroup: PropertyRef = PropertyRef("resource_group")
    type: PropertyRef = PropertyRef("type")
    plan: PropertyRef = PropertyRef("plan.product")
    size: PropertyRef = PropertyRef("hardware_profile.vm_size")
    license_type: PropertyRef = PropertyRef("license_type")
    computer_name: PropertyRef = PropertyRef("os_profile.computer_name")
    identity_type: PropertyRef = PropertyRef("identity.type")
    identity_principal_ids: PropertyRef = PropertyRef("identity_principal_ids")
    zones: PropertyRef = PropertyRef("zones")
    ultra_ssd_enabled: PropertyRef = PropertyRef(
        "additional_capabilities.ultra_ssd_enabled"
    )
    priority: PropertyRef = PropertyRef("priority")
    eviction_policy: PropertyRef = PropertyRef("eviction_policy")


@dataclass(frozen=True)
class AzureVirtualMachineToSubscriptionRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:AzureSubscription)-[:RESOURCE]->(:AzureVirtualMachine)
class AzureVirtualMachineToSubscriptionRel(CartographyRelSchema):
    target_node_label: str = "AzureSubscription"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AZURE_SUBSCRIPTION_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: AzureVirtualMachineToSubscriptionRelProperties = (
        AzureVirtualMachineToSubscriptionRelProperties()
    )


@dataclass(frozen=True)
class AzureVirtualMachineToServicePrincipalRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# Canonical ontology edge: (:AzureVirtualMachine)-[:RUNS_AS]->(:EntraServicePrincipal).
# The VM's managed identity (system- or user-assigned) surfaces in Entra as a
# service principal whose object id equals the identity's principalId.
class AzureVirtualMachineToServicePrincipalRel(CartographyRelSchema):
    target_node_label: str = "EntraServicePrincipal"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("identity_principal_ids", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "RUNS_AS"
    properties: AzureVirtualMachineToServicePrincipalRelProperties = (
        AzureVirtualMachineToServicePrincipalRelProperties()
    )


@dataclass(frozen=True)
class AzureVirtualMachineSchema(CartographyNodeSchema):
    label: str = "AzureVirtualMachine"
    properties: AzureVirtualMachineProperties = AzureVirtualMachineProperties()
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["ComputeInstance"])
    sub_resource_relationship: AzureVirtualMachineToSubscriptionRel = (
        AzureVirtualMachineToSubscriptionRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            AzureVirtualMachineToServicePrincipalRel(),
        ],
    )


@dataclass(frozen=True)
class AzureVirtualMachineToRoleAssumesRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    _sub_resource_label: PropertyRef = PropertyRef(
        "_sub_resource_label", set_in_kwargs=True
    )
    _sub_resource_id: PropertyRef = PropertyRef("_sub_resource_id", set_in_kwargs=True)


@dataclass(frozen=True)
# Canonical ontology edge: (:AzureVirtualMachine)-[:ASSUMES]->(:AzureRoleDefinition).
# The VM runs with the permissions of the role definitions assigned to its
# managed identity. Assembled by joining the identity principalId to
# AzureRoleAssignment -> AzureRoleDefinition after the RBAC sync, so it is loaded
# as a MatchLink rather than a direct edge on the node.
class AzureVirtualMachineToRoleAssumesMatchLink(CartographyRelSchema):
    rel_label: str = "ASSUMES"
    direction: LinkDirection = LinkDirection.OUTWARD
    properties: AzureVirtualMachineToRoleAssumesRelProperties = (
        AzureVirtualMachineToRoleAssumesRelProperties()
    )
    target_node_label: str = "AzureRoleDefinition"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("role_definition_id")},
    )
    source_node_label: str = "AzureVirtualMachine"
    source_node_matcher: SourceNodeMatcher = make_source_node_matcher(
        {"id": PropertyRef("workload_id")},
    )
