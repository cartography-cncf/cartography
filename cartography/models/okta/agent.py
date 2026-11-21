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
class OktaAgentNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id",
        description="Unique Okta agent ID, generated when the agent is installed.",
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last sync that observed this resource.",
    )
    name: PropertyRef = PropertyRef(
        "name",
        extra_index=True,
        description="Agent name, usually the host name of the server it runs on.",
    )
    type: PropertyRef = PropertyRef(
        "type",
        extra_index=True,
        description=(
            "Agent type, as Okta reports it: `AD`, `IWA`, `LDAP`, `MFA`, `OPP`, "
            "`OPS`, `RUM`, or `Radius`."
        ),
    )
    version: PropertyRef = PropertyRef(
        "version",
        description="Version of the installed agent, such as `5.26.3`.",
    )
    is_latest_ga_version: PropertyRef = PropertyRef(
        "is_latest_ga_version",
        description="Whether the agent runs the latest generally available version.",
    )
    is_hidden: PropertyRef = PropertyRef(
        "is_hidden",
        description="Whether the agent is hidden from the Okta Admin Console.",
    )
    operational_status: PropertyRef = PropertyRef(
        "operational_status",
        description=(
            "Operational status of the agent: `OPERATIONAL`, `DEGRADED`, "
            "`DISRUPTED`, or `INACTIVE`."
        ),
    )
    last_connection: PropertyRef = PropertyRef(
        "last_connection",
        description="Time when the agent last connected to Okta.",
    )
    update_status: PropertyRef = PropertyRef(
        "update_status",
        description=(
            "Status of the agent's latest update, such as `Scheduled`, "
            "`InProgress`, `Success`, or `Failed`."
        ),
    )
    update_message: PropertyRef = PropertyRef(
        "update_message",
        description="Message about the agent's latest update.",
    )
    pool_id: PropertyRef = PropertyRef(
        "pool_id",
        description="ID of the agent pool that the agent belongs to.",
    )


@dataclass(frozen=True)
class OktaAgentToOrganizationRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last sync that observed this relationship.",
    )


@dataclass(frozen=True)
class OktaAgentToOrganizationRel(CartographyRelSchema):
    """An Okta organization has a customer-managed agent."""

    target_node_label: str = "OktaOrganization"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("OKTA_ORG_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: OktaAgentToOrganizationRelProperties = (
        OktaAgentToOrganizationRelProperties()
    )


@dataclass(frozen=True)
class OktaAgentPoolToAgentRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last sync that observed this relationship.",
    )


@dataclass(frozen=True)
class OktaAgentPoolToAgentRel(CartographyRelSchema):
    """An agent pool contains an agent."""

    target_node_label: str = "OktaAgentPool"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("pool_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS_AGENT"
    properties: OktaAgentPoolToAgentRelProperties = OktaAgentPoolToAgentRelProperties()


@dataclass(frozen=True)
class OktaAgentSchema(CartographyNodeSchema):
    """
    A customer-managed Okta agent installed on one of your servers, such as the
    Active Directory, LDAP, RADIUS, or On-Premises Provisioning agent. Use its
    `type` and `version` to find agents that a security advisory affects.
    Requires the `okta.agentPools.read` scope; check `agents_synced` on
    `OktaOrganization` before reading a missing agent as absent.
    """

    label: str = "OktaAgent"
    properties: OktaAgentNodeProperties = OktaAgentNodeProperties()
    sub_resource_relationship: OktaAgentToOrganizationRel = OktaAgentToOrganizationRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [OktaAgentPoolToAgentRel()],
    )
