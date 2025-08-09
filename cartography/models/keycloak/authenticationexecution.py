from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_source_node_matcher
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import OtherRelationships
from cartography.models.core.relationships import SourceNodeMatcher
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class KeycloakAuthenticationExecutionNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    display_name: PropertyRef = PropertyRef("displayName")
    requirement: PropertyRef = PropertyRef("requirement")
    description: PropertyRef = PropertyRef("description")
    configurable: PropertyRef = PropertyRef("configurable")
    authentication_flow: PropertyRef = PropertyRef("authenticationFlow")
    provider_id: PropertyRef = PropertyRef("providerId")
    flow_id: PropertyRef = PropertyRef("flowId")
    level: PropertyRef = PropertyRef("level")
    index: PropertyRef = PropertyRef("index")
    priority: PropertyRef = PropertyRef("priority")
    is_terminal_step: PropertyRef = PropertyRef("is_terminal_step")
    lastupdated: PropertyRef = PropertyRef("LASTUPDATED", set_in_kwargs=True)


@dataclass(frozen=True)
class KeycloakAuthenticationExecutionToRealmRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("LASTUPDATED", set_in_kwargs=True)


@dataclass(frozen=True)
# (:KeycloakAuthenticationExecution)<-[:RESOURCE]-(:KeycloakRealm)
class KeycloakAuthenticationExecutionToRealmRel(CartographyRelSchema):
    target_node_label: str = "KeycloakRealm"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"name": PropertyRef("REALM", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: KeycloakAuthenticationExecutionToRealmRelProperties = (
        KeycloakAuthenticationExecutionToRealmRelProperties()
    )


@dataclass(frozen=True)
class ExecutionToFlowRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("LASTUPDATED", set_in_kwargs=True)


@dataclass(frozen=True)
# (:KeycloakAuthenticationExecution)<-[:HAS_STEP]-(:KeycloakAuthenticationFlow)
class ExecutionToFlowRel(CartographyRelSchema):
    target_node_label: str = "KeycloakAuthenticationFlow"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "alias": PropertyRef("_parent_flow"),
            "realm": PropertyRef("REALM", set_in_kwargs=True),
        },
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS_STEP"
    properties: ExecutionToFlowRelProperties = ExecutionToFlowRelProperties()


@dataclass(frozen=True)
class ExecutionToExecutionRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("LASTUPDATED", set_in_kwargs=True)


@dataclass(frozen=True)
# (:KeycloakAuthenticationExecution)<-[:HAS_STEP]-(:KeycloakAuthenticationExecution)
class ExecutionToExecutionRel(CartographyRelSchema):
    target_node_label: str = "KeycloakAuthenticationExecution"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("_parent_subflow")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS_STEP"
    properties: ExecutionToExecutionRelProperties = ExecutionToExecutionRelProperties()


@dataclass(frozen=True)
class KeycloakAuthenticationExecutionSchema(CartographyNodeSchema):
    label: str = "KeycloakAuthenticationExecution"
    properties: KeycloakAuthenticationExecutionNodeProperties = (
        KeycloakAuthenticationExecutionNodeProperties()
    )
    sub_resource_relationship: KeycloakAuthenticationExecutionToRealmRel = (
        KeycloakAuthenticationExecutionToRealmRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [ExecutionToFlowRel(), ExecutionToExecutionRel()]
    )


# The following relationships are MatchLinks, they are used to modelize all the possible flows
@dataclass(frozen=True)
class ExecutionToExecutionStepRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("LASTUPDATED", set_in_kwargs=True)
    # Mandatory fields for MatchLinks
    _sub_resource_label: PropertyRef = PropertyRef(
        "_sub_resource_label", set_in_kwargs=True
    )
    _sub_resource_id: PropertyRef = PropertyRef("_sub_resource_id", set_in_kwargs=True)


@dataclass(frozen=True)
# (:KeycloakAuthenticationExecution)-[:NEXT_STEP]->(:KeycloakAuthenticationExecution)
class ExecutionToExecutionMatchLink(CartographyRelSchema):
    source_node_label: str = "KeycloakAuthenticationExecution"
    source_node_matcher: SourceNodeMatcher = make_source_node_matcher(
        {"id": PropertyRef("source")},
    )
    target_node_label: str = "KeycloakAuthenticationExecution"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("target")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "NEXT_STEP"
    properties: ExecutionToExecutionStepRelProperties = (
        ExecutionToExecutionStepRelProperties()
    )


@dataclass(frozen=True)
class ExecutionToFlowStepRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("LASTUPDATED", set_in_kwargs=True)
    # Mandatory fields for MatchLinks
    _sub_resource_label: PropertyRef = PropertyRef(
        "_sub_resource_label", set_in_kwargs=True
    )
    _sub_resource_id: PropertyRef = PropertyRef("_sub_resource_id", set_in_kwargs=True)


@dataclass(frozen=True)
# (:KeycloakAuthenticationFlow)-[:NEXT_STEP]->(:KeycloakAuthenticationExecution)
class ExecutionToFlowMatchLink(CartographyRelSchema):
    source_node_label: str = "KeycloakAuthenticationExecution"
    source_node_matcher: SourceNodeMatcher = make_source_node_matcher(
        {"id": PropertyRef("execution_id")},
    )
    target_node_label: str = "KeycloakAuthenticationFlow"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "alias": PropertyRef("flow_name"),
            "realm": PropertyRef(
                "realm"
            ),  # We need to pass the realm to match the flow correctly as aliases can be shared across realms
        },
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "NEXT_STEP"
    properties: ExecutionToFlowStepRelProperties = ExecutionToFlowStepRelProperties()
