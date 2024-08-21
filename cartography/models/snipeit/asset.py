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
class SnipeitAssetNodeProperties(CartographyNodeProperties):
    """
    https://snipe-it.readme.io/reference/hardware-list
    """
    # Common properties
    id: PropertyRef = PropertyRef('id')
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)

    # SnipeIT specific properties
    asset_tag: PropertyRef = PropertyRef('asset_tag')
    assigned_to: PropertyRef = PropertyRef('assigned_to.email')
    category: PropertyRef = PropertyRef('category.name')
    company: PropertyRef = PropertyRef('company.name')
    manufacturer: PropertyRef = PropertyRef('manufacturer.name')
    model: PropertyRef = PropertyRef('model.name')
    serial: PropertyRef = PropertyRef('serial', extra_index=True)


###
# (:SnipeitAsset)<-[:ASSET]-(:SnipeitTenant)
###
@dataclass(frozen=True)
class SnipeitTenantToSnipeitAssetRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)


@dataclass(frozen=True)
class SnipeitTenantToSnipeitAssetRel(CartographyRelSchema):
    target_node_label: str = 'SnipeitTenant'
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {'id': PropertyRef('TENANT_ID', set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS_ASSET"
    properties: SnipeitTenantToSnipeitAssetRelProperties = SnipeitTenantToSnipeitAssetRelProperties()


###
# (:SnipeitUser)-[:HAS_CHECKED_OUT]->(:SnipeitAsset)
###
@dataclass(frozen=True)
class SnipeitUserToSnipeitAssetProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)


@dataclass(frozen=True)
class SnipeitUserToSnipeitAssetRel(CartographyRelSchema):
    target_node_label: str = 'SnipeitUser'
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {'email': PropertyRef('assigned_to.email')},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS_CHECKED_OUT"
    properties: SnipeitUserToSnipeitAssetProperties = SnipeitUserToSnipeitAssetProperties()


###
@dataclass(frozen=True)
class SnipeitAssetSchema(CartographyNodeSchema):
    label: str = 'SnipeitAsset'  # The label of the node
    properties: SnipeitAssetNodeProperties = SnipeitAssetNodeProperties()  # An object representing all properties
    sub_resource_relationship: SnipeitTenantToSnipeitAssetRel = SnipeitTenantToSnipeitAssetRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            SnipeitUserToSnipeitAssetRel(),
        ],
    )
