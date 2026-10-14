from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import ExtraNodeLabel
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import TargetNodeMatcher

AD_OBJECT = ExtraNodeLabel(
    label="ADObject",
    description=(
        "An Active Directory object imported from BloodHound collector output. "
        "Every AD node carries this label so edges can match a principal of any "
        "type by its identifier."
    ),
)


@dataclass(frozen=True)
class ADObjectNodeProperties(CartographyNodeProperties):
    """Properties shared by every AD object imported from BloodHound output.

    AD attribute names follow the lowercase names BloodHound emits.
    """

    id: PropertyRef = PropertyRef(
        "id",
        description="Object identifier: the SID for security principals, the GUID for OUs, GPOs and containers.",
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    objectid: PropertyRef = PropertyRef(
        "id",
        extra_index=True,
        description="Same as `id`. Named like BloodHound CE's `objectid` so BloodHound queries carry over.",
    )
    name: PropertyRef = PropertyRef(
        "name",
        extra_index=True,
        description="BloodHound display name, such as `USER@EXAMPLE.LOCAL`.",
    )
    domain: PropertyRef = PropertyRef(
        "domain",
        description="FQDN of the domain that holds the object.",
    )
    domainsid: PropertyRef = PropertyRef(
        "domainsid",
        description="SID of the domain that holds the object.",
    )
    distinguishedname: PropertyRef = PropertyRef(
        "distinguishedname",
        extra_index=True,
        description="LDAP distinguished name.",
    )
    description: PropertyRef = PropertyRef(
        "description",
        description="LDAP description attribute.",
    )
    whencreated: PropertyRef = PropertyRef(
        "whencreated",
        description="Creation time (UTC).",
    )
    isaclprotected: PropertyRef = PropertyRef(
        "isaclprotected",
        description="Whether the object's DACL blocks inheritance from its parent.",
    )
    source_uri: PropertyRef = PropertyRef(
        "source_uri",
        description="URI of the collector output file this object was read from.",
    )
    collected_at: PropertyRef = PropertyRef(
        "collected_at",
        description=(
            "Collection time from the collector output, as an ISO 8601 timestamp. "
            "SharpHound writes the collector host's local time without an offset."
        ),
    )
    collector_version: PropertyRef = PropertyRef(
        "collector_version",
        description="Version of the collector that produced the output.",
    )


@dataclass(frozen=True)
class ADDomainToObjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:ADDomain)-[:RESOURCE]->(:ADObject)
class ADDomainToObjectRel(CartographyRelSchema):
    """Scopes an AD object to the domain that holds it."""

    target_node_label: str = "ADDomain"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("DOMAIN_SID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: ADDomainToObjectRelProperties = ADDomainToObjectRelProperties()
