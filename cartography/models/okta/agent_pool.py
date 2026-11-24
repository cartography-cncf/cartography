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
class OktaAgentPoolNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", description="Unique Okta agent pool ID.")
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last sync that observed this resource.",
    )
    name: PropertyRef = PropertyRef("name", description="Agent pool name.")
    type: PropertyRef = PropertyRef(
        "type",
        description=(
            "Type of the agents in the pool, as Okta reports it: `AD`, `IWA`, "
            "`LDAP`, `MFA`, `OPP`, `OPS`, `RUM`, or `Radius`."
        ),
    )
    operational_status: PropertyRef = PropertyRef(
        "operational_status",
        description=(
            "Operational status of the pool: `OPERATIONAL`, `DEGRADED`, "
            "`DISRUPTED`, or `INACTIVE`."
        ),
    )
    disrupted_agents: PropertyRef = PropertyRef(
        "disrupted_agents",
        description="Number of agents in the pool that are disrupted.",
    )
    inactive_agents: PropertyRef = PropertyRef(
        "inactive_agents",
        description="Number of agents in the pool that are inactive.",
    )


@dataclass(frozen=True)
class OktaAgentPoolToOrganizationRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last sync that observed this relationship.",
    )


@dataclass(frozen=True)
class OktaAgentPoolToOrganizationRel(CartographyRelSchema):
    """An Okta organization has an agent pool."""

    target_node_label: str = "OktaOrganization"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("OKTA_ORG_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: OktaAgentPoolToOrganizationRelProperties = (
        OktaAgentPoolToOrganizationRelProperties()
    )


@dataclass(frozen=True)
class OktaAgentPoolSchema(CartographyNodeSchema):
    """
    A pool of customer-managed Okta agents of one type, such as the Active
    Directory, LDAP, RADIUS, or On-Premises Provisioning agents installed on
    your own servers. Requires the `okta.agentPools.read` scope. Okta Access
    Gateway appliances are not agents and are not listed.
    """

    label: str = "OktaAgentPool"
    properties: OktaAgentPoolNodeProperties = OktaAgentPoolNodeProperties()
    sub_resource_relationship: OktaAgentPoolToOrganizationRel = (
        OktaAgentPoolToOrganizationRel()
    )
