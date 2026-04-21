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


@dataclass(frozen=True)
class SocketDevFixNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    purl: PropertyRef = PropertyRef("purl")
    fixed_version: PropertyRef = PropertyRef("fixed_version")
    update_type: PropertyRef = PropertyRef("update_type")
    vulnerability_id: PropertyRef = PropertyRef("vulnerability_id", extra_index=True)
    fix_type: PropertyRef = PropertyRef("fix_type", extra_index=True)


@dataclass(frozen=True)
class SocketDevOrgToFixRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SocketDevOrganization)-[:RESOURCE]->(:SocketDevFix)
class SocketDevOrgToFixRel(CartographyRelSchema):
    target_node_label: str = "SocketDevOrganization"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ORG_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: SocketDevOrgToFixRelProperties = SocketDevOrgToFixRelProperties()


@dataclass(frozen=True)
class SocketDevFixToAlertRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SocketDevFix)-[:APPLIES_TO]->(:SocketDevAlert)
class SocketDevFixToAlertRel(CartographyRelSchema):
    target_node_label: str = "SocketDevAlert"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("alert_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "APPLIES_TO"
    properties: SocketDevFixToAlertRelProperties = SocketDevFixToAlertRelProperties()


@dataclass(frozen=True)
class SocketDevFixToDependencyRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SocketDevDependency)-[:SHOULD_UPDATE_TO]->(:SocketDevFix)
class SocketDevFixToDependencyRel(CartographyRelSchema):
    target_node_label: str = "SocketDevDependency"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("dependency_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "SHOULD_UPDATE_TO"
    properties: SocketDevFixToDependencyRelProperties = (
        SocketDevFixToDependencyRelProperties()
    )


@dataclass(frozen=True)
class SocketDevFixSchema(CartographyNodeSchema):
    label: str = "SocketDevFix"
    properties: SocketDevFixNodeProperties = SocketDevFixNodeProperties()
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["Fix"])
    sub_resource_relationship: SocketDevOrgToFixRel = SocketDevOrgToFixRel()
    other_relationships: OtherRelationships = OtherRelationships(
        rels=[
            SocketDevFixToAlertRel(),
            SocketDevFixToDependencyRel(),
        ],
    )
