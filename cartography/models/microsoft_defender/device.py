from dataclasses import dataclass
from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import OtherRelationships

# ---------------------------------------------------------
# FIX: We define a reusable properties class first.
# This tells Cartography: "Relationships in this module have a 'lastupdated' field."
# ---------------------------------------------------------
@dataclass(frozen=True)
class MDERelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)

# ---------------------------------------------------------
# 1. Relationship: Device BELONGS_TO Tenant
# ---------------------------------------------------------
@dataclass(frozen=True)
class MDEDeviceToTenantRel(CartographyRelSchema):
    target_node_label: str = 'MDETenant'
    target_node_matcher: PropertyRef = make_target_node_matcher(
        {'id': PropertyRef('tenant_id', set_in_kwargs=True)}
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    # FIX: We instantiate our specific class here, not the base class
    properties: MDERelProperties = MDERelProperties()

# ---------------------------------------------------------
# 2. Relationship: AzureVM HAS_AGENT Device (The Bridge)
# ---------------------------------------------------------
@dataclass(frozen=True)
class MDEDeviceToAzureVMRel(CartographyRelSchema):
    target_node_label: str = 'AzureVirtualMachine'
    target_node_matcher: PropertyRef = make_target_node_matcher(
        {'id': PropertyRef('aad_device_id')}
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS_DEFENDER_AGENT"
    # FIX: Use the specific class here too
    properties: MDERelProperties = MDERelProperties()

# ---------------------------------------------------------
# 3. The Device Node Definition
# ---------------------------------------------------------
@dataclass(frozen=True)
class MDEDeviceProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef('id')
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)
    name: PropertyRef = PropertyRef('computerDnsName')
    risk_score: PropertyRef = PropertyRef('riskScore')
    health_status: PropertyRef = PropertyRef('healthStatus')
    os_platform: PropertyRef = PropertyRef('osPlatform')
    # This field is critical for the bridge logic above
    aad_device_id: PropertyRef = PropertyRef('aadDeviceId')

@dataclass(frozen=True)
class MDEDeviceSchema(CartographyNodeSchema):
    label: str = 'MDEDevice'
    properties: MDEDeviceProperties = MDEDeviceProperties()
    sub_resource_relationship: MDEDeviceToTenantRel = MDEDeviceToTenantRel()
    other_relationships: OtherRelationships = OtherRelationships([
        MDEDeviceToAzureVMRel()
    ])