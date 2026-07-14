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
    id: PropertyRef = PropertyRef(
        "id", description="The unique identifier of the authentication execution"
    )
    display_name: PropertyRef = PropertyRef(
        "displayName", description="The display name of the authentication execution"
    )
    requirement: PropertyRef = PropertyRef(
        "requirement",
        description="The requirement level (REQUIRED, OPTIONAL, ALTERNATIVE, DISABLED)",
    )
    description: PropertyRef = PropertyRef(
        "description", description="The description of the authentication execution"
    )
    configurable: PropertyRef = PropertyRef(
        "configurable", description="Whether this execution is configurable"
    )
    authentication_flow: PropertyRef = PropertyRef(
        "authenticationFlow",
        description="Whether this execution references an authentication flow",
    )
    provider_id: PropertyRef = PropertyRef(
        "providerId",
        description="The provider identifier for the authentication execution",
    )
    flow_id: PropertyRef = PropertyRef(
        "flowId", description="The flow identifier if this execution references a flow"
    )
    level: PropertyRef = PropertyRef(
        "level", description="The nesting level of the execution"
    )
    index: PropertyRef = PropertyRef(
        "index", description="The index position within the flow"
    )
    priority: PropertyRef = PropertyRef(
        "priority", description="The priority order of the execution"
    )
    is_terminal_step: PropertyRef = PropertyRef(
        "is_terminal_step",
        description="Whether the execution can be a terminal workflow step (inferred by Cartography)",
    )
    lastupdated: PropertyRef = PropertyRef(
        "LASTUPDATED",
        set_in_kwargs=True,
        description="Timestamp of the last time the node was updated",
    )


@dataclass(frozen=True)
class KeycloakAuthenticationExecutionToRealmRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("LASTUPDATED", set_in_kwargs=True)


@dataclass(frozen=True)
# (:KeycloakAuthenticationExecution)<-[:RESOURCE]-(:KeycloakRealm)
class KeycloakAuthenticationExecutionToRealmRel(CartographyRelSchema):
    """The realm contains the authentication execution."""

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
    """The authentication flow contains the execution as a step."""

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
    """The parent execution contains the subflow execution as a step."""

    target_node_label: str = "KeycloakAuthenticationExecution"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("_parent_subflow")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS_STEP"
    properties: ExecutionToExecutionRelProperties = ExecutionToExecutionRelProperties()


@dataclass(frozen=True)
class KeycloakAuthenticationExecutionSchema(CartographyNodeSchema):
    """Represents an individual authentication execution step within a Keycloak authentication flow. Authentication executions define specific authentication mechanisms, requirements, and their order within an authentication flow."""

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
    """The execution can continue to the next execution."""

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
    """The authentication flow starts with the execution."""

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
