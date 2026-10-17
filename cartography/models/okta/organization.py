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
    admin_roles_synced: PropertyRef = PropertyRef(
        "admin_roles_synced",
        description=(
            "Whether the last sync could read user and group admin role assignments. "
            "False when the API token's admin role cannot read them, so a missing "
            "`OktaUserRole` or `OktaGroupRole` does not mean a user has no admin role."
        ),
    )
    application_roles_synced: PropertyRef = PropertyRef(
        "application_roles_synced",
        description=(
            "Whether the last sync could read the admin roles assigned to OAuth "
            "service apps. False when the credential lacks `okta.roles.read` or an "
            "admin role that allows it, so a missing `OktaApplicationRole` does not "
            "mean an app has no admin role."
        ),
    )
    app_grants_synced: PropertyRef = PropertyRef(
        "app_grants_synced",
        description=(
            "Whether the last sync could read the OAuth scopes granted to apps "
            "into `OktaApplication.granted_scopes`. False when the credential "
            "lacks `okta.appGrants.read` or an admin role that allows it, so a "
            "null `granted_scopes` does not mean an app has no grants."
        ),
    )


@dataclass(frozen=True)
class OktaOrganizationSchema(CartographyNodeSchema):
    label: str = "OktaOrganization"
    properties: OktaOrganizationNodeProperties = OktaOrganizationNodeProperties()
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([TENANT])
