from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_source_node_matcher
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import MatchLinkSubResource
from cartography.models.core.relationships import SourceNodeMatcher
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class OktaApplicationToFederationRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last sync that observed this relationship.",
    )
    _sub_resource_label: PropertyRef = PropertyRef(
        "_sub_resource_label",
        set_in_kwargs=True,
        description="Label of the Okta organization that owns this relationship.",
    )
    _sub_resource_id: PropertyRef = PropertyRef(
        "_sub_resource_id",
        set_in_kwargs=True,
        description="Identifier of the Okta organization that owns this relationship.",
    )
    sign_on_mode: PropertyRef = PropertyRef(
        "sign_on_mode",
        description="Okta sign-on mode of the app, such as SAML_2_0 or BROWSER_PLUGIN.",
    )
    matched_on: PropertyRef = PropertyRef(
        "matched_on",
        description="Okta app setting that names the tenant, such as settings.app.domain.",
    )


@dataclass(frozen=True)
class OktaApplicationToSlackTeamMatchLink(CartographyRelSchema):
    """
    Links an Okta Slack app to the Slack workspaces it signs users into.
    Cartography considers `OktaApplication` nodes with `name` `slack`. When
    `settings_app_domain` ends in `.enterprise`, Cartography removes the suffix
    and links the app to every `SlackTeam` whose `enterprise_domain` matches,
    because the app signs users into an Enterprise Grid organization.
    Otherwise, Cartography links the app to the `SlackTeam` whose `domain`
    matches, only when exactly one workspace matches. Matching is
    case-insensitive, and `matched_on` is `settings.app.domain`.
    """

    source_node_label: str = "OktaApplication"
    source_node_matcher: SourceNodeMatcher = make_source_node_matcher(
        {"id": PropertyRef("okta_app_id")},
    )
    source_node_sub_resource: MatchLinkSubResource = MatchLinkSubResource(
        target_node_label="OktaOrganization",
        target_node_matcher=make_target_node_matcher(
            {"id": PropertyRef("_sub_resource_id", set_in_kwargs=True)},
        ),
        direction=LinkDirection.INWARD,
        rel_label="RESOURCE",
    )
    target_node_label: str = "SlackTeam"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("target_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "FEDERATES_TO"
    properties: OktaApplicationToFederationRelProperties = (
        OktaApplicationToFederationRelProperties()
    )


@dataclass(frozen=True)
class OktaApplicationToGitHubOrganizationMatchLink(CartographyRelSchema):
    """
    Links an Okta GitHub Cloud app to the GitHub organization it signs users into.
    Cartography considers `OktaApplication` nodes with `name` `githubcloud` and
    links `settings_app_github_org` to `GitHubOrganization.username`, only when
    exactly one organization matches. Matching is case-insensitive, and
    `matched_on` is `settings.app.githubOrg`.
    """

    source_node_label: str = "OktaApplication"
    source_node_matcher: SourceNodeMatcher = make_source_node_matcher(
        {"id": PropertyRef("okta_app_id")},
    )
    source_node_sub_resource: MatchLinkSubResource = MatchLinkSubResource(
        target_node_label="OktaOrganization",
        target_node_matcher=make_target_node_matcher(
            {"id": PropertyRef("_sub_resource_id", set_in_kwargs=True)},
        ),
        direction=LinkDirection.INWARD,
        rel_label="RESOURCE",
    )
    target_node_label: str = "GitHubOrganization"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("target_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "FEDERATES_TO"
    properties: OktaApplicationToFederationRelProperties = (
        OktaApplicationToFederationRelProperties()
    )


@dataclass(frozen=True)
class OktaApplicationToGoogleWorkspaceTenantMatchLink(CartographyRelSchema):
    """
    Links an Okta Google Workspace app to the tenant it signs users into.
    Cartography considers `OktaApplication` nodes with `name` `google` and links
    `settings_app_domain` to `GoogleWorkspaceTenant.domain`, only when exactly
    one tenant matches. Matching is case-insensitive, and `matched_on` is
    `settings.app.domain`.
    """

    source_node_label: str = "OktaApplication"
    source_node_matcher: SourceNodeMatcher = make_source_node_matcher(
        {"id": PropertyRef("okta_app_id")},
    )
    source_node_sub_resource: MatchLinkSubResource = MatchLinkSubResource(
        target_node_label="OktaOrganization",
        target_node_matcher=make_target_node_matcher(
            {"id": PropertyRef("_sub_resource_id", set_in_kwargs=True)},
        ),
        direction=LinkDirection.INWARD,
        rel_label="RESOURCE",
    )
    target_node_label: str = "GoogleWorkspaceTenant"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("target_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "FEDERATES_TO"
    properties: OktaApplicationToFederationRelProperties = (
        OktaApplicationToFederationRelProperties()
    )


@dataclass(frozen=True)
class OktaApplicationToSalesforceOrganizationMatchLink(CartographyRelSchema):
    """
    Links an Okta Salesforce app to the Salesforce organization it signs users into.
    Cartography considers `OktaApplication` nodes with `name` `salesforce`. It
    compares the host of `settings_app_login_url` with the host of
    `SalesforceOrganization.instance_url` (`matched_on` is
    `settings.app.loginUrl`). If no organization has that host, it compares
    `<settings_app_custom_domain>.my.salesforce.com` (or
    `<settings_app_custom_domain>.sandbox.my.salesforce.com` and
    `<settings_app_custom_domain>--<name>.sandbox.my.salesforce.com` when
    `settings_app_instance_type` is `SANDBOX`) instead (`matched_on` is
    `settings.app.customDomain`). Cartography skips a candidate when
    `settings_app_instance_type` is `PRODUCTION` and `is_sandbox` is `true`, or
    `SANDBOX` and `is_sandbox` is `false`. It links the app only when exactly
    one organization remains. Matching is case-insensitive.
    """

    source_node_label: str = "OktaApplication"
    source_node_matcher: SourceNodeMatcher = make_source_node_matcher(
        {"id": PropertyRef("okta_app_id")},
    )
    source_node_sub_resource: MatchLinkSubResource = MatchLinkSubResource(
        target_node_label="OktaOrganization",
        target_node_matcher=make_target_node_matcher(
            {"id": PropertyRef("_sub_resource_id", set_in_kwargs=True)},
        ),
        direction=LinkDirection.INWARD,
        rel_label="RESOURCE",
    )
    target_node_label: str = "SalesforceOrganization"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("target_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "FEDERATES_TO"
    properties: OktaApplicationToFederationRelProperties = (
        OktaApplicationToFederationRelProperties()
    )
