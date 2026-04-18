from __future__ import annotations

# Okta intel module - Applications
import asyncio
import json
import logging
from typing import Any

import neo4j
from okta.client import Client as OktaClient
from okta.models.application import Application as OktaApplication

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.okta.common import collect_paginated
from cartography.models.okta.application import OktaApplicationSchema
from cartography.models.okta.reply_uri import OktaReplyUriSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


####
# Get Applications
####
@timeit
def sync_okta_applications(
    okta_client: OktaClient,
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    """
    Sync Okta applications
    :param okta_client: An Okta client object
    :param neo4j_session: Session with Neo4j server
    :param common_job_parameters: Settings used by all Okta modules
    :return: Nothing
    """

    logger.info("Syncing Okta applications")
    applications = asyncio.run(_get_okta_applications(okta_client))
    transformed_applications = _transform_okta_applications(okta_client, applications)
    _load_okta_applications(
        neo4j_session, transformed_applications, common_job_parameters
    )
    _cleanup_okta_applications(neo4j_session, common_job_parameters)
    reply_uris = _transform_okta_reply_uris(applications)
    _load_okta_reply_uris(neo4j_session, reply_uris, common_job_parameters)
    _cleanup_okta_reply_uris(neo4j_session, common_job_parameters)


@timeit
async def _get_okta_applications(okta_client: OktaClient) -> list[OktaApplication]:
    """
    Get Okta applications list from Okta
    :param okta_client: An Okta client object
    :return: List of Okta applications
    """
    return await collect_paginated(okta_client.list_applications, limit=200)


@timeit
def _transform_okta_applications(
    okta_client: OktaClient,
    okta_applications: list[OktaApplication],
) -> list[dict[str, Any]]:
    """
    :param okta_client: An Okta client object
    Convert a list of Okta applications into a format for Neo4j
    :param okta_applications: List of Okta applications
    :return: List of application dicts
    """
    transformed_applications: list[OktaApplication] = []
    logger.info("Transforming %s Okta applications", len(okta_applications))
    for okta_application in okta_applications:
        application_props: dict[str, Any] = {}
        application_props["id"] = okta_application.id
        # Sparse app types (bookmarks, SWA, ...) can have any of the nested
        # sub-objects set to None, so every level must be guarded to avoid
        # aborting the whole sync on one atypical app.
        accessibility = okta_application.accessibility
        application_props["accessibility_error_redirect_url"] = (
            accessibility.error_redirect_url if accessibility else None
        )
        application_props["accessibility_login_redirect_url"] = (
            accessibility.login_redirect_url if accessibility else None
        )
        application_props["accessibility_self_service"] = (
            accessibility.self_service if accessibility else None
        )

        application_props["created"] = okta_application.created
        credentials = okta_application.credentials
        signing = credentials.signing if credentials else None
        application_props["credentials_signing_kid"] = signing.kid if signing else None
        application_props["credentials_signing_last_rotated"] = (
            signing.last_rotated if signing else None
        )
        application_props["credentials_signing_next_rotation"] = (
            signing.next_rotation if signing else None
        )
        application_props["credentials_signing_rotation_mode"] = (
            signing.rotation_mode if signing else None
        )
        application_props["credentials_signing_use"] = signing.use if signing else None
        user_name_template = credentials.user_name_template if credentials else None
        application_props["credentials_user_name_template_push_status"] = (
            user_name_template.push_status if user_name_template else None
        )
        application_props["credentials_user_name_template_suffix"] = (
            user_name_template.suffix if user_name_template else None
        )
        application_props["credentials_user_name_template_template"] = (
            user_name_template.template if user_name_template else None
        )
        application_props["credentials_user_name_template_type"] = (
            user_name_template.type if user_name_template else None
        )
        application_props["features"] = okta_application.features
        application_props["label"] = okta_application.label
        application_props["last_updated"] = okta_application.last_updated
        # Licensing information varies by application type and license model.
        # seat_count is only available for applications with seat-based licensing.
        # Other licensing models may have different attributes (e.g., unlimited, per-user).
        # We extract seat_count when available; other licensing attributes can be added
        # as needed based on specific application requirements.
        licensing = okta_application.licensing
        application_props["licensing_seat_count"] = (
            getattr(licensing, "seat_count", None) if licensing else None
        )
        application_props["name"] = okta_application.name
        settings = okta_application.settings
        settings_app = settings.app if settings else None
        application_props["settings_app_acs_url"] = (
            settings_app.acs_url if settings_app else None
        )
        application_props["settings_app_button_field"] = (
            settings_app.button_field if settings_app else None
        )
        application_props["settings_app_login_url_regex"] = (
            settings_app.login_url_regex if settings_app else None
        )
        application_props["settings_app_org_name"] = (
            settings_app.org_name if settings_app else None
        )
        application_props["settings_app_password_field"] = (
            settings_app.password_field if settings_app else None
        )
        application_props["settings_app_url"] = (
            settings_app.url if settings_app else None
        )
        application_props["settings_app_username_field"] = (
            settings_app.username_field if settings_app else None
        )
        application_props["settings_app_implicit_assignment"] = (
            settings.implicit_assignment if settings else None
        )
        application_props["settings_app_inline_hook_id"] = (
            settings.inline_hook_id if settings else None
        )
        notifications = settings.notifications if settings else None
        vpn = notifications.vpn if notifications else None
        network = vpn.network if vpn else None
        application_props["settings_notifications_vpn_help_url"] = (
            vpn.help_url if vpn else None
        )
        application_props["settings_notifications_vpn_message"] = (
            vpn.message if vpn else None
        )
        application_props["settings_notifications_vpn_network_connection"] = (
            network.connection if network else None
        )
        application_props["settings_notifications_vpn_network_exclude"] = (
            json.dumps(network.exclude) if network else None
        )
        application_props["settings_notifications_vpn_network_include"] = (
            json.dumps(network.include) if network else None
        )
        notes = settings.notes if settings else None
        application_props["settings_notes_admin"] = getattr(notes, "admin", None)
        application_props["settings_notes_enduser"] = getattr(notes, "enduser", None)
        # Parse SAML sign-on configuration if present
        sign_on = getattr(settings, "sign_on", None) if settings else None
        if sign_on:
            # Common SAML sign-on properties
            if hasattr(sign_on, "default_relay_state"):
                application_props["settings_sign_on_default_relay_state"] = (
                    sign_on.default_relay_state
                )
            if hasattr(sign_on, "sso_acs_url"):
                application_props["settings_sign_on_sso_acs_url"] = sign_on.sso_acs_url
            if hasattr(sign_on, "sso_acs_url_override"):
                application_props["settings_sign_on_sso_acs_url_override"] = (
                    sign_on.sso_acs_url_override
                )
            if hasattr(sign_on, "recipient"):
                application_props["settings_sign_on_recipient"] = sign_on.recipient
            if hasattr(sign_on, "recipient_override"):
                application_props["settings_sign_on_recipient_override"] = (
                    sign_on.recipient_override
                )
            if hasattr(sign_on, "destination"):
                application_props["settings_sign_on_destination"] = sign_on.destination
            if hasattr(sign_on, "destination_override"):
                application_props["settings_sign_on_destination_override"] = (
                    sign_on.destination_override
                )
            if hasattr(sign_on, "audience"):
                application_props["settings_sign_on_audience"] = sign_on.audience
            if hasattr(sign_on, "audience_override"):
                application_props["settings_sign_on_audience_override"] = (
                    sign_on.audience_override
                )
            if hasattr(sign_on, "idp_issuer"):
                application_props["settings_sign_on_idp_issuer"] = sign_on.idp_issuer
            if hasattr(sign_on, "subject_name_id_template"):
                application_props["settings_sign_on_subject_name_id_template"] = (
                    sign_on.subject_name_id_template
                )
            if hasattr(sign_on, "subject_name_id_format"):
                application_props["settings_sign_on_subject_name_id_format"] = (
                    sign_on.subject_name_id_format
                )
            if hasattr(sign_on, "response_signed"):
                application_props["settings_sign_on_response_signed"] = (
                    sign_on.response_signed
                )
            if hasattr(sign_on, "assertion_signed"):
                application_props["settings_sign_on_assertion_signed"] = (
                    sign_on.assertion_signed
                )
            if hasattr(sign_on, "signature_algorithm"):
                application_props["settings_sign_on_signature_algorithm"] = (
                    sign_on.signature_algorithm
                )
            if hasattr(sign_on, "digest_algorithm"):
                application_props["settings_sign_on_digest_algorithm"] = (
                    sign_on.digest_algorithm
                )
            if hasattr(sign_on, "honor_force_authn"):
                application_props["settings_sign_on_honor_force_authn"] = (
                    sign_on.honor_force_authn
                )
            if hasattr(sign_on, "authn_context_class_ref"):
                application_props["settings_sign_on_authn_context_class_ref"] = (
                    sign_on.authn_context_class_ref
                )
        # oauth_client, sometimes this doesn't exist, sometimes its None
        oauth_client = getattr(settings, "oauth_client", None) if settings else None
        if oauth_client:
            application_type = getattr(oauth_client, "application_type", None)
            application_props["settings_oauth_client_application_type"] = (
                application_type.value if application_type else None
            )
            application_props["settings_oauth_client_client_uri"] = (
                oauth_client.client_uri
            )
            consent_method = getattr(oauth_client, "consent_method", None)
            application_props["settings_oauth_client_consent_method"] = (
                consent_method.value if consent_method else None
            )
            application_props["settings_oauth_client_grant_Type"] = [
                grant_type.value for grant_type in (oauth_client.grant_types or [])
            ]
            idp_initiated_login = getattr(oauth_client, "idp_initiated_login", None)
            application_props[
                "settings_oauth_client_idp_initiated_login_default_scope"
            ] = (
                json.dumps(idp_initiated_login.default_scope)
                if idp_initiated_login
                else None
            )
            application_props["settings_oauth_client_idp_initiated_login_mode"] = (
                idp_initiated_login.mode if idp_initiated_login else None
            )
            application_props["settings_oauth_client_initiate_login_uri"] = (
                oauth_client.initiate_login_uri
            )
            application_props["settings_oauth_client_logo_uri"] = oauth_client.logo_uri
            application_props["settings_oauth_client_policy_uri"] = (
                oauth_client.policy_uri
            )
            application_props["settings_oauth_client_post_logout_redirect_uris"] = (
                json.dumps(oauth_client.post_logout_redirect_uris)
            )
            application_props["settings_oauth_client_redirect_uris"] = json.dumps(
                oauth_client.redirect_uris
            )
            application_props["settings_oauth_client_response_types"] = [
                response_type.value
                for response_type in (oauth_client.response_types or [])
            ]
            application_props["settings_oauth_client_tos_uri"] = oauth_client.tos_uri
            application_props["settings_oauth_client_wildcard_redirect"] = (
                oauth_client.wildcard_redirect
            )
        # This value can also be None, in which case it has no value
        if okta_application.sign_on_mode:
            application_props["sign_on_mode"] = okta_application.sign_on_mode.value
        else:
            application_props["sign_on_mode"] = okta_application.sign_on_mode
        application_props["status"] = (
            okta_application.status.value if okta_application.status else None
        )
        application_props["activated"] = okta_application.activated
        visibility = okta_application.visibility
        # visibility.app_links is a dict of poorly defined shape, treat as JSON blob.
        application_props["visibility_app_links"] = (
            json.dumps(visibility.app_links) if visibility else None
        )
        application_props["visibility_auto_launch"] = (
            visibility.auto_launch if visibility else None
        )
        application_props["visibility_auto_submit_toolbar"] = (
            visibility.auto_submit_toolbar if visibility else None
        )
        # visibility.hide is an ApplicationVisibilityHide model that behaves
        # like a dict; stored as JSON.
        hide = visibility.hide if visibility else None
        application_props["visibility_hide"] = (
            json.dumps(hide.as_dict()) if hide else None
        )
        transformed_applications.append(application_props)
        # Add user assignments
        app_users = asyncio.run(
            _get_application_assigned_users(okta_client, okta_application.id)
        )
        for app_user in app_users:
            match_app = {**application_props, "user_id": app_user}
            transformed_applications.append(match_app)
        # Add group assignments
        app_groups = asyncio.run(
            _get_application_assigned_groups(okta_client, okta_application.id)
        )
        for app_group in app_groups:
            match_app = {**application_props, "group_id": app_group}
            transformed_applications.append(match_app)

    return transformed_applications


@timeit
def _load_okta_applications(
    neo4j_session: neo4j.Session,
    application_list: list[dict],
    common_job_parameters: dict[str, Any],
) -> None:
    """
    Load Okta application information into the graph
    :param neo4j_session: session with neo4j server
    :param application_list: list of application
    :param common_job_parameters: Settings used by all Okta modules
    :return: Nothing
    """

    logger.info("Loading %s Okta applications", len(application_list))

    load(
        neo4j_session,
        OktaApplicationSchema(),
        application_list,
        OKTA_ORG_ID=common_job_parameters["OKTA_ORG_ID"],
        lastupdated=common_job_parameters["UPDATE_TAG"],
    )


@timeit
def _cleanup_okta_applications(
    neo4j_session: neo4j.Session, common_job_parameters: dict[str, Any]
) -> None:
    """
    Cleanup application nodes and relationships
    :param neo4j_session: session with neo4j server
    :param common_job_parameters: Settings used by all Okta modules
    :return: Nothing
    """
    GraphJob.from_node_schema(OktaApplicationSchema(), common_job_parameters).run(
        neo4j_session
    )


####
# Get Applications assigned to users
####


@timeit
async def _get_application_assigned_users(
    okta_client: OktaClient, app_id: str
) -> list[str]:
    """
    Get Okta application users list from Okta
    :param okta_client: An Okta client object
    :param app_id: The application ID to fetch users for
    :return: List of Okta application user IDs
    """
    application_users = await collect_paginated(
        okta_client.list_application_users, limit=500, app_id=app_id
    )
    return [user.id for user in application_users]


####
# Get Applications assigned to groups
####
@timeit
async def _get_application_assigned_groups(
    okta_client: OktaClient, app_id: str
) -> list[str]:
    """
    Get Okta application groups list from Okta
    :param okta_client: An Okta client object
    :param app_id: The application ID to fetch groups for
    :return: List of Okta application group IDs
    """
    application_groups = await collect_paginated(
        okta_client.list_application_group_assignments, limit=200, app_id=app_id
    )
    return [group.id for group in application_groups]


####
# ReplyUri
####


@timeit
def _transform_okta_reply_uris(
    okta_applications: list[OktaApplication],
) -> list[dict[str, Any]]:
    """
    Extract OAuth redirect URIs per application into ReplyUri records.
    """
    reply_uris: list[dict[str, Any]] = []
    for okta_application in okta_applications:
        settings = okta_application.settings
        oauth_client = getattr(settings, "oauth_client", None) if settings else None
        if not oauth_client:
            continue
        for redirect_uri in oauth_client.redirect_uris or []:
            reply_uris.append(
                {
                    "id": redirect_uri,
                    "uri": redirect_uri,
                    "application_id": okta_application.id,
                }
            )
    return reply_uris


@timeit
def _load_okta_reply_uris(
    neo4j_session: neo4j.Session,
    reply_uri_list: list[dict[str, Any]],
    common_job_parameters: dict[str, Any],
) -> None:
    logger.info("Loading %s Okta ReplyUris", len(reply_uri_list))
    load(
        neo4j_session,
        OktaReplyUriSchema(),
        reply_uri_list,
        OKTA_ORG_ID=common_job_parameters["OKTA_ORG_ID"],
        lastupdated=common_job_parameters["UPDATE_TAG"],
    )


@timeit
def _cleanup_okta_reply_uris(
    neo4j_session: neo4j.Session, common_job_parameters: dict[str, Any]
) -> None:
    GraphJob.from_node_schema(OktaReplyUriSchema(), common_job_parameters).run(
        neo4j_session
    )
