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
    id: PropertyRef = PropertyRef(
        "id",
        description="Unique Socket.dev fix identifier.",
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last time the node was updated.",
    )
    purl: PropertyRef = PropertyRef(
        "purl",
        description="Package URL of the affected package.",
    )
    fixed_version: PropertyRef = PropertyRef(
        "fixed_version",
        description="Package version that fixes the vulnerability.",
    )
    update_type: PropertyRef = PropertyRef(
        "update_type",
        description="Type of version update required.",
    )
    vulnerability_id: PropertyRef = PropertyRef(
        "vulnerability_id",
        extra_index=True,
        description="CVE or GHSA identifier addressed by the fix.",
    )
    fix_type: PropertyRef = PropertyRef(
        "fix_type",
        extra_index=True,
        description="Availability classification for the fix.",
    )


@dataclass(frozen=True)
class SocketDevOrgToFixRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SocketDevOrganization)-[:RESOURCE]->(:SocketDevFix)
class SocketDevOrgToFixRel(CartographyRelSchema):
    """Links a Socket.dev organization to one of its available fixes."""

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
    """Links an available fix to the alert it addresses."""

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
    """Links a dependency to the fix version it should use."""

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
    """An available remediation for a Socket.dev vulnerability alert."""

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
