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
class S1ApplicationVersionNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", extra_index=True)
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    application_name: PropertyRef = PropertyRef("application_name")
    application_vendor: PropertyRef = PropertyRef("application_vendor")
    version: PropertyRef = PropertyRef("version")


@dataclass(frozen=True)
class S1ApplicationVersionToAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:S1ApplicationVersion)<-[:RESOURCE]-(:S1Account)
class S1ApplicationVersionToAccount(CartographyRelSchema):
    target_node_label: str = "S1Account"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("S1_ACCOUNT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: S1ApplicationVersionToAccountRelProperties = (
        S1ApplicationVersionToAccountRelProperties()
    )


@dataclass(frozen=True)
class S1AgentToApplicationVersionRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    installeddatetime: PropertyRef = PropertyRef("installed_dt")
    installationpath: PropertyRef = PropertyRef("installation_path")


@dataclass(frozen=True)
# (:S1Agent)-[:HAS_INSTALLED]->(:S1ApplicationVersion)
class S1AgentToS1ApplicationVersion(CartographyRelSchema):
    target_node_label: str = "S1Agent"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"uuid": PropertyRef("agent_uuid")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS_INSTALLED"
    properties: S1AgentToApplicationVersionRelProperties = (
        S1AgentToApplicationVersionRelProperties()
    )


@dataclass(frozen=True)
class S1ApplicationVersionToApplicationRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:S1ApplicationVersion)<-[:VERSION]-(:S1Application)
class S1ApplicationVersionToApplication(CartographyRelSchema):
    target_node_label: str = "S1Application"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("application_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "VERSION"
    properties: S1ApplicationVersionToApplicationRelProperties = (
        S1ApplicationVersionToApplicationRelProperties()
    )


@dataclass(frozen=True)
class S1ApplicationVersionSchema(CartographyNodeSchema):
    label: str = "S1ApplicationVersion"
    properties: S1ApplicationVersionNodeProperties = (
        S1ApplicationVersionNodeProperties()
    )
    sub_resource_relationship: S1ApplicationVersionToAccount = (
        S1ApplicationVersionToAccount()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            S1AgentToS1ApplicationVersion(),
            S1ApplicationVersionToApplication(),
        ],
    )
