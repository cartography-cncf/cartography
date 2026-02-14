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
class SantaObservedApplicationVersionNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", extra_index=True)
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    version: PropertyRef = PropertyRef("version")
    source_name: PropertyRef = PropertyRef("source_name")
    last_seen: PropertyRef = PropertyRef("last_seen")


@dataclass(frozen=True)
class SantaObservedApplicationVersionRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SantaObservedApplication)-[:VERSION]->(:SantaObservedApplicationVersion)
class SantaObservedApplicationToVersionRel(CartographyRelSchema):
    target_node_label: str = "SantaObservedApplication"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("application_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "VERSION"
    properties: SantaObservedApplicationVersionRelProperties = (
        SantaObservedApplicationVersionRelProperties()
    )


@dataclass(frozen=True)
# (:SantaMachine)-[:OBSERVED_EXECUTION]->(:SantaObservedApplicationVersion)
class SantaMachineObservedExecutionRel(CartographyRelSchema):
    target_node_label: str = "SantaMachine"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("machine_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "OBSERVED_EXECUTION"
    properties: SantaObservedApplicationVersionRelProperties = (
        SantaObservedApplicationVersionRelProperties()
    )


@dataclass(frozen=True)
# (:SantaUser)-[:EXECUTED]->(:SantaObservedApplicationVersion)
class SantaUserExecutedRel(CartographyRelSchema):
    target_node_label: str = "SantaUser"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("executed_by_user_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "EXECUTED"
    properties: SantaObservedApplicationVersionRelProperties = (
        SantaObservedApplicationVersionRelProperties()
    )


@dataclass(frozen=True)
class SantaObservedApplicationVersionSchema(CartographyNodeSchema):
    label: str = "SantaObservedApplicationVersion"
    scoped_cleanup: bool = False
    properties: SantaObservedApplicationVersionNodeProperties = (
        SantaObservedApplicationVersionNodeProperties()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        rels=[
            SantaObservedApplicationToVersionRel(),
            SantaMachineObservedExecutionRel(),
            SantaUserExecutedRel(),
        ],
    )
