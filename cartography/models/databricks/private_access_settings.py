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
    id: PropertyRef = PropertyRef("id")
    private_access_settings_id: PropertyRef = PropertyRef(
        "private_access_settings_id", extra_index=True
    )
    private_access_settings_name: PropertyRef = PropertyRef(
        "private_access_settings_name", extra_index=True
    )
    public_access_enabled: PropertyRef = PropertyRef("public_access_enabled")
    private_access_level: PropertyRef = PropertyRef("private_access_level")
    region: PropertyRef = PropertyRef("region")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class DatabricksPrivateAccessSettingsToAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:DatabricksAccount)-[:RESOURCE]->(:DatabricksPrivateAccessSettings)
class DatabricksPrivateAccessSettingsToAccountRel(CartographyRelSchema):
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
    label: str = "DatabricksPrivateAccessSettings"
    properties: DatabricksPrivateAccessSettingsNodeProperties = (
        DatabricksPrivateAccessSettingsNodeProperties()
    )
    sub_resource_relationship: DatabricksPrivateAccessSettingsToAccountRel = (
        DatabricksPrivateAccessSettingsToAccountRel()
    )
