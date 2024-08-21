from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class SnipeitUserNodeProperties(CartographyNodeProperties):
    """
    Ref: https://snipe-it.readme.io/reference/users
    """
    # Common properties
    id: PropertyRef = PropertyRef('id')
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)

    # SnipeIT specific properties
    company: PropertyRef = PropertyRef('company_id.name', extra_index=True)
    email: PropertyRef = PropertyRef('email', extra_index=True)
    username: PropertyRef = PropertyRef('username')


@dataclass(frozen=True)
class SnipeitTenantToSnipeitUserRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)


@dataclass(frozen=True)
# (:SnipeitTenant)-[:HAS_USER]->(:SnipeitUser)
class SnipeitTenantToSnipeitUserRel(CartographyRelSchema):
    target_node_label: str = 'SnipeitTenant'
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {'id': PropertyRef('TENANT_ID', set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS_USER"
    properties: SnipeitTenantToSnipeitUserRelProperties = SnipeitTenantToSnipeitUserRelProperties()


@dataclass(frozen=True)
class SnipeitUserSchema(CartographyNodeSchema):
    label: str = 'SnipeitUser'  # The label of the node
    properties: SnipeitUserNodeProperties = SnipeitUserNodeProperties()  # An object representing all properties
    sub_resource_relationship: SnipeitTenantToSnipeitUserRel = SnipeitTenantToSnipeitUserRel()
