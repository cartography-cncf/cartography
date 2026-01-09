from dataclasses import dataclass
from dataclasses import field  # <--- Added missing import
from typing import Dict

from cartography.models.core.common import PropertyRef
from cartography.models.core.common import TargetNodeMatcher
from cartography.models.core.common import make_target_node_matcher
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.relationships import CartographyRelSchema


@dataclass(frozen=True)
class MDEDeviceNodeSchema(CartographyNodeSchema):
    label: str = 'MDEDevice'
    # Fixed: Changed 'dataclass_field' to 'field'
    attributes: Dict[str, PropertyRef] = field(default_factory=lambda: {
        'id': PropertyRef('id'),
        'computer_name': PropertyRef('computerDnsName'),
        'aad_device_id': PropertyRef('aadDeviceId'),
        'risk_score': PropertyRef('riskScore'),
        'os_platform': PropertyRef('osPlatform'),
        'health_status': PropertyRef('healthStatus'),
        'lastupdated': PropertyRef('lastupdated'),
    })


@dataclass(frozen=True)
class MDEDeviceToTenantRel(CartographyRelSchema):
    target_node_label: str = 'MDETenant'
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {'id': PropertyRef('tenant_id')},
    )
    rel_label: str = "RESOURCE"
    direction: str = "IN"


@dataclass(frozen=True)
class MDEDeviceToAzureVMRel(CartographyRelSchema):
    target_node_label: str = 'AzureVirtualMachine'
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {'externalid': PropertyRef('aad_device_id')},
    )
    rel_label: str = "HAS_MDE_AGENT"
