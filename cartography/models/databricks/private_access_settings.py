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
class DatabricksPrivateAccessSettingsNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id",
        description="Account-scoped Databricks private access settings ID.",
    )
    private_access_settings_id: PropertyRef = PropertyRef(
        "private_access_settings_id",
        extra_index=True,
        description="Databricks private access settings ID.",
    )
    private_access_settings_name: PropertyRef = PropertyRef(
        "private_access_settings_name",
        extra_index=True,
        description="Private access settings name.",
    )
    public_access_enabled: PropertyRef = PropertyRef(
        "public_access_enabled",
        description="Whether public access is enabled.",
    )
    private_access_level: PropertyRef = PropertyRef(
        "private_access_level",
        description="Level of private access allowed for the workspace.",
    )
    region: PropertyRef = PropertyRef(
        "region",
        description="AWS region for the private access settings.",
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class DatabricksPrivateAccessSettingsToAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:DatabricksAccount)-[:RESOURCE]->(:DatabricksPrivateAccessSettings)
class DatabricksPrivateAccessSettingsToAccountRel(CartographyRelSchema):
    """A Databricks account owns an account-level resource."""

    target_node_label: str = "DatabricksAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ACCOUNT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: DatabricksPrivateAccessSettingsToAccountRelProperties = (
        DatabricksPrivateAccessSettingsToAccountRelProperties()
    )


@dataclass(frozen=True)
class DatabricksPrivateAccessSettingsSchema(CartographyNodeSchema):
    """A Databricks account PrivateLink access settings object."""

    label: str = "DatabricksPrivateAccessSettings"
    properties: DatabricksPrivateAccessSettingsNodeProperties = (
        DatabricksPrivateAccessSettingsNodeProperties()
    )
    sub_resource_relationship: DatabricksPrivateAccessSettingsToAccountRel = (
        DatabricksPrivateAccessSettingsToAccountRel()
    )
