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
class DatabricksAccountSettingNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    setting_name: PropertyRef = PropertyRef("setting_name", extra_index=True)
    value: PropertyRef = PropertyRef("value")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class DatabricksAccountSettingToAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:DatabricksAccount)-[:RESOURCE]->(:DatabricksAccountSetting)
class DatabricksAccountSettingToAccountRel(CartographyRelSchema):
    target_node_label: str = "DatabricksAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ACCOUNT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: DatabricksAccountSettingToAccountRelProperties = (
        DatabricksAccountSettingToAccountRelProperties()
    )


@dataclass(frozen=True)
class DatabricksAccountSettingSchema(CartographyNodeSchema):
    label: str = "DatabricksAccountSetting"
    properties: DatabricksAccountSettingNodeProperties = (
        DatabricksAccountSettingNodeProperties()
    )
    sub_resource_relationship: DatabricksAccountSettingToAccountRel = (
        DatabricksAccountSettingToAccountRel()
    )
