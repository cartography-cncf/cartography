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
from cartography.models.ontology.labels import CVE


@dataclass(frozen=True)
class TenableCveNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id",
        description=(
            "`TNB|<tenant id>|<CVE ID>`, for example "
            "`TNB|cloud.tenable.com|CVE-2024-1234`."
        ),
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    cve_id: PropertyRef = PropertyRef(
        "cve_id",
        extra_index=True,
        description="CVE identifier, for example `CVE-2024-1234`.",
    )


@dataclass(frozen=True)
class TenableCveToTenantRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


# (:TenableTenant)-[:RESOURCE]->(:TenableCve)
@dataclass(frozen=True)
class TenableCveToTenantRel(CartographyRelSchema):
    """Links a Tenable tenant to a CVE named by one of its plugins."""

    target_node_label: str = "TenableTenant"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("TENABLE_TENANT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: TenableCveToTenantRelProperties = TenableCveToTenantRelProperties()


@dataclass(frozen=True)
class TenableCveToPluginRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


# (:TenablePlugin)-[:HAS_CVE]->(:TenableCve)
@dataclass(frozen=True)
class TenableCveToPluginRel(CartographyRelSchema):
    """Links a Tenable plugin to a CVE it checks for."""

    target_node_label: str = "TenablePlugin"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("plugin_ids", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS_CVE"
    properties: TenableCveToPluginRelProperties = TenableCveToPluginRelProperties()


@dataclass(frozen=True)
class TenableCveSchema(CartographyNodeSchema):
    """A CVE named by a Tenable plugin. Tenable supplies no per-CVE data, so this
    node holds identity only; findings reach it through the plugin that detected them.

    ``id`` is ``TNB|<tenant id>|<CVE ID>``. The prefix stops the `cve` module, which
    MERGEs on ``(:CVE {id})``, from adopting these nodes. The tenant gives each
    tenant its own nodes, so one tenant's cleanup cannot delete another's.
    """

    label: str = "TenableCve"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([CVE])
    properties: TenableCveNodeProperties = TenableCveNodeProperties()
    sub_resource_relationship: TenableCveToTenantRel = TenableCveToTenantRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [TenableCveToPluginRel()],
    )
