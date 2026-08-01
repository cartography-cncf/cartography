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
from cartography.models.ontology.labels import SECRET


# --- Node Definitions ---
@dataclass(frozen=True)
class NetlifyEnvVarNodeProperties(CartographyNodeProperties):
    # Composite `<account_id>|<site_id>|<key>`, built in transform(). The key is the only stable
    # natural identifier, and the same key can exist both team-wide and on an individual site.
    id: PropertyRef = PropertyRef(
        "id",
        description="Composite `<account_id>|<site_id>|<key>`, with `_account` in place of the site id for a team-wide variable. The key is the only stable natural identifier, and the same key can exist at both scopes.",
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    key: PropertyRef = PropertyRef(
        "key", extra_index=True, description="Variable name."
    )
    # Empty for a team-wide variable, so it also distinguishes the two scopes.
    site_id: PropertyRef = PropertyRef(
        "site_id", description="Id of the site, empty for a team-wide variable."
    )
    scope: PropertyRef = PropertyRef("scope", description="`site` or `account`.")
    # Where the variable is readable: builds, functions, runtime, post_processing.
    scopes: PropertyRef = PropertyRef(
        "scopes",
        description="Where the variable is readable: `builds`, `functions`, `runtime`, `post_processing`.",
    )
    # Deploy contexts the variable is set for, flattened from `values[].context`.
    contexts: PropertyRef = PropertyRef(
        "contexts", description="Deploy contexts the variable is set for."
    )
    is_secret: PropertyRef = PropertyRef(
        "is_secret", description="Whether Netlify marks the variable secret."
    )
    # String mirror of is_secret. Conditional extra labels are compared as Cypher strings, so a
    # real boolean would never match; see ExtraNodeLabel.when() in models/core/nodes.py.
    is_secret_flag: PropertyRef = PropertyRef(
        "is_secret_flag",
        description="String mirror of `is_secret`. Conditional extra labels are compared as Cypher strings, so a real boolean would never match.",
    )
    updated_at: PropertyRef = PropertyRef(
        "updated_at", description="When the variable was last changed."
    )


# --- Relationship Definitions ---
@dataclass(frozen=True)
class NetlifyEnvVarToNetlifyAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:NetlifyAccount)-[:RESOURCE]->(:NetlifyEnvVar)
class NetlifyEnvVarToNetlifyAccountRel(CartographyRelSchema):
    target_node_label: str = "NetlifyAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("NETLIFY_ACCOUNT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: NetlifyEnvVarToNetlifyAccountRelProperties = (
        NetlifyEnvVarToNetlifyAccountRelProperties()
    )


@dataclass(frozen=True)
class NetlifyEnvVarToSiteRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:NetlifySite)-[:HAS_ENV_VAR]->(:NetlifyEnvVar), only for site-scoped variables.
class NetlifyEnvVarToSiteRel(CartographyRelSchema):
    target_node_label: str = "NetlifySite"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("site_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS_ENV_VAR"
    properties: NetlifyEnvVarToSiteRelProperties = NetlifyEnvVarToSiteRelProperties()


@dataclass(frozen=True)
class NetlifyEnvVarToUserRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:NetlifyEnvVar)-[:UPDATED_BY]->(:NetlifyUser)
class NetlifyEnvVarToUserRel(CartographyRelSchema):
    """The team member who last changed this variable."""

    target_node_label: str = "NetlifyUser"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("updated_by_user_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "UPDATED_BY"
    properties: NetlifyEnvVarToUserRelProperties = NetlifyEnvVarToUserRelProperties()


# --- Main Schema ---
@dataclass(frozen=True)
class NetlifyEnvVarSchema(CartographyNodeSchema):
    """
    A Netlify environment variable, team-wide or scoped to one site.

    Values are never ingested. Netlify masks a secret value down to its last four characters and
    returns a non-secret value in full, so transform() drops the `values[].value` field
    entirely and keeps only the contexts each value was set for.
    """

    label: str = "NetlifyEnvVar"
    properties: NetlifyEnvVarNodeProperties = NetlifyEnvVarNodeProperties()
    # Only variables Netlify itself marks secret carry the ontology Secret label; the rest are
    # ordinary configuration.
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(
        [SECRET.when(is_secret_flag="true")],
    )
    sub_resource_relationship: NetlifyEnvVarToNetlifyAccountRel = (
        NetlifyEnvVarToNetlifyAccountRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            NetlifyEnvVarToSiteRel(),
            NetlifyEnvVarToUserRel(),
        ],
    )
