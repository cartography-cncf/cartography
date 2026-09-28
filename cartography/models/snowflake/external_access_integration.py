from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import OtherRelationships
from cartography.models.core.relationships import TargetNodeMatcher
from cartography.models.snowflake.extra_labels import SNOWFLAKE_SECURABLE


@dataclass(frozen=True)
class SnowflakeExternalAccessIntegrationNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id",
        description="Account-scoped identifier for the external access integration.",
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef(
        "name", extra_index=True, description="The external access integration name."
    )
    enabled: PropertyRef = PropertyRef(
        "enabled",
        description=(
            "Whether UDFs and procedures may make outbound network calls through the "
            "integration."
        ),
    )
    allowed_network_rules: PropertyRef = PropertyRef(
        "allowed_network_rules",
        description="Qualified names of the egress network rules the integration permits.",
    )
    allowed_authentication_secrets: PropertyRef = PropertyRef(
        "allowed_authentication_secrets",
        description="Qualified names of the secrets handler code may read through the integration.",
    )
    allowed_api_authentication_integrations: PropertyRef = PropertyRef(
        "allowed_api_authentication_integrations",
        description="Names of the security integrations that may mint OAuth tokens for the calls.",
    )
    comment: PropertyRef = PropertyRef(
        "comment", description="External access integration comment."
    )
    created_on: PropertyRef = PropertyRef(
        "created_on", description="When the external access integration was created."
    )


@dataclass(frozen=True)
class SnowflakeExternalAccessIntegrationToAccountRelProperties(
    CartographyRelProperties
):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SnowflakeAccount)-[:RESOURCE]->(:SnowflakeExternalAccessIntegration)
class SnowflakeExternalAccessIntegrationToAccountRel(CartographyRelSchema):
    """A Snowflake account contains the external access integration as a resource."""

    target_node_label: str = "SnowflakeAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ACCOUNT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: SnowflakeExternalAccessIntegrationToAccountRelProperties = (
        SnowflakeExternalAccessIntegrationToAccountRelProperties()
    )


@dataclass(frozen=True)
class SnowflakeExternalAccessIntegrationToNetworkRuleRelProperties(
    CartographyRelProperties
):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SnowflakeExternalAccessIntegration)-[:ALLOWS]->(:SnowflakeNetworkRule)
class SnowflakeExternalAccessIntegrationToNetworkRuleRel(CartographyRelSchema):
    """A Snowflake external access integration permits the egress described by this network rule."""

    target_node_label: str = "SnowflakeNetworkRule"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("allowed_network_rule_ids", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "ALLOWS"
    properties: SnowflakeExternalAccessIntegrationToNetworkRuleRelProperties = (
        SnowflakeExternalAccessIntegrationToNetworkRuleRelProperties()
    )


@dataclass(frozen=True)
class SnowflakeExternalAccessIntegrationToSecretRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SnowflakeExternalAccessIntegration)-[:ALLOWS_SECRET]->(:SnowflakeSecret)
class SnowflakeExternalAccessIntegrationToSecretRel(CartographyRelSchema):
    """A Snowflake external access integration lets handler code read this secret."""

    target_node_label: str = "SnowflakeSecret"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("allowed_secret_ids", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "ALLOWS_SECRET"
    properties: SnowflakeExternalAccessIntegrationToSecretRelProperties = (
        SnowflakeExternalAccessIntegrationToSecretRelProperties()
    )


@dataclass(frozen=True)
class SnowflakeExternalAccessIntegrationToAuthIntegrationRelProperties(
    CartographyRelProperties
):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SnowflakeExternalAccessIntegration)-[:ALLOWS_AUTH_INTEGRATION]->(:SnowflakeSecurityIntegration)
class SnowflakeExternalAccessIntegrationToAuthIntegrationRel(CartographyRelSchema):
    """A Snowflake external access integration may mint tokens through this security integration."""

    target_node_label: str = "SnowflakeSecurityIntegration"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("allowed_auth_integration_ids", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "ALLOWS_AUTH_INTEGRATION"
    properties: SnowflakeExternalAccessIntegrationToAuthIntegrationRelProperties = (
        SnowflakeExternalAccessIntegrationToAuthIntegrationRelProperties()
    )


@dataclass(frozen=True)
class SnowflakeExternalAccessIntegrationSchema(CartographyNodeSchema):
    """Represents a Snowflake external access integration: the allow-list that lets UDF and procedure code call out to the internet."""

    label: str = "SnowflakeExternalAccessIntegration"
    properties: SnowflakeExternalAccessIntegrationNodeProperties = (
        SnowflakeExternalAccessIntegrationNodeProperties()
    )
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([SNOWFLAKE_SECURABLE])
    sub_resource_relationship: SnowflakeExternalAccessIntegrationToAccountRel = (
        SnowflakeExternalAccessIntegrationToAccountRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            SnowflakeExternalAccessIntegrationToNetworkRuleRel(),
            SnowflakeExternalAccessIntegrationToSecretRel(),
            SnowflakeExternalAccessIntegrationToAuthIntegrationRel(),
        ],
    )
