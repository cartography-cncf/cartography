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
class SSMInstancePatchNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef('Id')
    instance_id: PropertyRef = PropertyRef('_instance_id', extra_index=True)
    region: PropertyRef = PropertyRef('Region', set_in_kwargs=True)
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)
    title: PropertyRef = PropertyRef('Title', extra_index=True)
    kb_id: PropertyRef = PropertyRef('KBId', extra_index=True)
    classification: PropertyRef = PropertyRef('Classification')
    severity: PropertyRef = PropertyRef('Severity')
    state: PropertyRef = PropertyRef('State')
    installed_time: PropertyRef = PropertyRef('InstalledTime')
    cve_ids: PropertyRef = PropertyRef('CVEIds')


@dataclass(frozen=True)
class SSMInstancePatchToAWSAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)


@dataclass(frozen=True)
class SSMInstancePatchToAWSAccount(CartographyRelSchema):
    target_node_label: str = 'AWSAccount'
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {'id': PropertyRef('AWS_ID', set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: SSMInstancePatchToAWSAccountRelProperties = SSMInstancePatchToAWSAccountRelProperties()


@dataclass(frozen=True)
class SSMInstancePatchToEC2InstanceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)


@dataclass(frozen=True)
class SSMInstancePatchToEC2Instance(CartographyRelSchema):
    target_node_label: str = 'EC2Instance'
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {'id': PropertyRef('_instance_id')},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS_PATCH"
    properties: SSMInstancePatchToEC2InstanceRelProperties = SSMInstancePatchToEC2InstanceRelProperties()


@dataclass(frozen=True)
class SSMInstancePatchSchema(CartographyNodeSchema):
    label: str = 'SSMInstancePatch'
    properties: SSMInstancePatchNodeProperties = SSMInstancePatchNodeProperties()
    sub_resource_relationship: SSMInstancePatchToAWSAccount = SSMInstancePatchToAWSAccount()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            SSMInstancePatchToEC2Instance(),
        ],
    )
