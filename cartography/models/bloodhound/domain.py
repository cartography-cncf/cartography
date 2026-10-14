from dataclasses import dataclass

from cartography.models.bloodhound.common import AD_OBJECT
from cartography.models.bloodhound.common import ADObjectNodeProperties
from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels
from cartography.models.ontology.labels import TENANT


@dataclass(frozen=True)
class ADDomainNodeProperties(ADObjectNodeProperties):
    functionallevel: PropertyRef = PropertyRef(
        "functionallevel",
        description="Domain functional level, such as `2016`.",
    )
    forest_root_id: PropertyRef = PropertyRef(
        "forest_root_id",
        description="SID of the forest root domain.",
    )


@dataclass(frozen=True)
class ADDomainSchema(CartographyNodeSchema):
    """An Active Directory domain, keyed by domain SID.

    The domain is the tenant for every AD object imported from it. A domain that
    appears only as the target of a trust is kept as a placeholder with
    `collected` set to false.
    """

    label: str = "ADDomain"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([TENANT, AD_OBJECT])
    properties: ADDomainNodeProperties = ADDomainNodeProperties()
