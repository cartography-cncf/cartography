from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import TargetNodeMatcher
from cartography.models.ontology.labels import TENANT


@dataclass(frozen=True)
class ZendeskTenantNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", description="Normalized Zendesk subdomain.")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    domain: PropertyRef = PropertyRef("domain", description="Zendesk account hostname.")


@dataclass(frozen=True)
class ZendeskTenantSchema(CartographyNodeSchema):
    """A Zendesk account, identified by its configured subdomain.

    Ontology Mapping: The extra label `Tenant` enables cross-platform tenant queries.

    This node is constructed from the configured account subdomain, following
    [Zendesk's API URL conventions](https://developer.zendesk.com/api-reference/introduction/doc-conventions/).
    It is not an Organizations API object or a separately fetched account record.
    """

    label: str = "ZendeskTenant"
    properties: ZendeskTenantNodeProperties = ZendeskTenantNodeProperties()
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([TENANT])
    scoped_cleanup: bool = False


@dataclass(frozen=True)
class ZendeskRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ZendeskResourceToTenantRel(CartographyRelSchema):
    """Contains a Zendesk resource within its account and scopes its cleanup."""

    target_node_label: str = "ZendeskTenant"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("TENANT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: ZendeskRelProperties = ZendeskRelProperties()
