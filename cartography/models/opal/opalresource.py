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
class OpalResourceProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef('resource_id')
    app_id: PropertyRef = PropertyRef('app_id')
    name: PropertyRef = PropertyRef('name')
    admin_owner_id: PropertyRef = PropertyRef('admin_owner_id')
    description: PropertyRef = PropertyRef('description')
    remote_resource_id: PropertyRef = PropertyRef('remote_resource_id')
    remote_resource_name: PropertyRef = PropertyRef('remote_resource_name')
    resource_type: PropertyRef = PropertyRef('resource_type')
    max_duration: PropertyRef = PropertyRef('max_duration')
    recommended_duration: PropertyRef = PropertyRef('recommended_duration')
    require_manager_approval: PropertyRef = PropertyRef('require_manager_approval')
    require_support_ticket: PropertyRef = PropertyRef('require_support_ticket')
    require_mfa_to_approve: PropertyRef = PropertyRef('require_mfa_to_approve')
    require_mfa_to_request: PropertyRef = PropertyRef('require_mfa_to_request')
    require_mfa_to_connect: PropertyRef = PropertyRef('require_mfa_to_connect')
    is_requestable: PropertyRef = PropertyRef('is_requestable')
    parent_resource_id: PropertyRef = PropertyRef('parent_resource_id')
    remote_id: PropertyRef = PropertyRef('remote_id')
    remote_account_id: PropertyRef = PropertyRef('remote_account_id')
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)


@dataclass(frozen=True)
class OpalResourceToOktaRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)
    account_id: PropertyRef = PropertyRef('remote_account_id')


@dataclass(frozen=True)
class OpalResourceToOkta(CartographyRelSchema):
    target_node_label: str = 'OktaGroup'
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {'id': PropertyRef('remote_id')},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "PROVIDES_ACCESS_TO"
    properties: OpalResourceToOktaRelProperties = OpalResourceToOktaRelProperties()


@dataclass(frozen=True)
class OpalResourceToPermissionSetRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)
    account_id: PropertyRef = PropertyRef('remote_account_id')


@dataclass(frozen=True)
class OpalResourceToPermissionSet(CartographyRelSchema):
    target_node_label: str = 'AWSPermissionSet'
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {'arn': PropertyRef('remote_id')},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "PROVIDES_ACCOUNT_ACCESS"
    properties: OpalResourceToPermissionSetRelProperties = OpalResourceToPermissionSetRelProperties()


@dataclass(frozen=True)
class OpalResourceSchema(CartographyNodeSchema):
    label: str = 'OpalResource'
    properties: OpalResourceProperties = OpalResourceProperties()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            OpalResourceToPermissionSet(),
            OpalResourceToOkta(),
        ],
    )
