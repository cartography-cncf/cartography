from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels
from cartography.models.ontology.labels import TENANT


@dataclass(frozen=True)
class OktaOrganizationNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id", description="Unique identifier for the Okta resource."
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last sync that observed this resource.",
    )
    name: PropertyRef = PropertyRef("name", description="Okta name.")
    admin_console_session_idle_timeout_minutes: PropertyRef = PropertyRef(
        "admin_console_session_idle_timeout_minutes",
        description=(
            "Maximum idle time, in minutes, of an Okta Admin Console session. Null when "
            "the API token cannot read first-party app settings (`okta.apps.read`)."
        ),
    )
    admin_console_session_max_lifetime_minutes: PropertyRef = PropertyRef(
        "admin_console_session_max_lifetime_minutes",
        description=(
            "Maximum lifetime, in minutes, of an Okta Admin Console session. Null when "
            "the API token cannot read first-party app settings (`okta.apps.read`)."
        ),
    )
    log_streams_synced: PropertyRef = PropertyRef(
        "log_streams_synced",
        description=(
            "Whether the last sync could read the org's log streams. False when the "
            "API token lacks `okta.logStreams.read`, so a missing `OktaLogStream` "
            "does not mean the org has none."
        ),
    )


@dataclass(frozen=True)
class OktaOrganizationSchema(CartographyNodeSchema):
    label: str = "OktaOrganization"
    properties: OktaOrganizationNodeProperties = OktaOrganizationNodeProperties()
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([TENANT])
