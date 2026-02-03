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
from cartography.models.okta.application import OktaApplicationSchema
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


@timeit
async def _get_okta_applications(okta_client: OktaClient) -> list[OktaApplication]:
    """
    Get Okta applications list from Okta
    :param okta_client: An Okta client object
    :return: List of Okta applications
    """
    output_applications = []
    query_parameters = {"limit": 200}
    applications, resp, _ = await okta_client.list_applications(query_parameters)
    output_applications += applications
    while resp.has_next():
        applications, _ = await resp.next()
        output_applications += applications
        logger.debug("Fetched %s applications", len(applications))
    return output_applications


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
        application_props = {}
        application_props["id"] = okta_application.id
        application_props["accessibility_error_redirect_url"] = (
            okta_application.accessibility.error_redirect_url
        )
        application_props["accessibility_login_redirect_url"] = (
            okta_application.accessibility.login_redirect_url
        )
        application_props["accessibility_self_service"] = (
            okta_application.accessibility.self_service
        )

        application_props["created"] = okta_application.created
        application_props["credentials_signing_kid"] = (
            okta_application.credentials.signing.kid
        )
        application_props["credentials_signing_last_rotated"] = (
            okta_application.credentials.signing.last_rotated
        )
        application_props["credentials_signing_next_rotation"] = (
            okta_application.credentials.signing.next_rotation
        )
        application_props["credentials_signing_rotation_mode"] = (
            okta_application.credentials.signing.rotation_mode
        )
        application_props["credentials_signing_use"] = (
            okta_application.credentials.signing.use
        )
        application_props["credentials_user_name_template_push_status"] = (
            okta_application.credentials.user_name_template.push_status
        )
        application_props["credentials_user_name_template_suffix"] = (
            okta_application.credentials.user_name_template.suffix
        )
        application_props["credentials_user_name_template_template"] = (
            okta_application.credentials.user_name_template.template
        )
        application_props["credentials_user_name_template_type"] = (
            okta_application.credentials.user_name_template.type
        )
        application_props["features"] = okta_application.features
        application_props["label"] = okta_application.label
        application_props["last_updated"] = okta_application.last_updated
        # Licensing information varies by application type and license model.
        # seat_count is only available for applications with seat-based licensing.
        # Other licensing models may have different attributes (e.g., unlimited, per-user).
        # We extract seat_count when available; other licensing attributes can be added
        # as needed based on specific application requirements.
        if hasattr(okta_application.licensing, "seat_count"):
            application_props["licensing_seat_count"] = (
                okta_application.licensing.seat_count
            )
        else:
            application_props["licensing_seat_count"] = None
        application_props["name"] = okta_application.name
        application_props["settings_app_acs_url"] = (
            okta_application.settings.app.acs_url
        )
        application_props["settings_app_button_field"] = (
            okta_application.settings.app.button_field
        )
        application_props["settings_app_login_url_regex"] = (
            okta_application.settings.app.login_url_regex
        )
        application_props["settings_app_org_name"] = (
            okta_application.settings.app.org_name
        )
        application_props["settings_app_password_field"] = (
            okta_application.settings.app.password_field
        )
        application_props["settings_app_url"] = okta_application.settings.app.url
        application_props["settings_app_username_field"] = (
            okta_application.settings.app.username_field
        )
        application_props["settings_app_implicit_assignment"] = (
            okta_application.settings.implicit_assignment
        )
        application_props["settings_app_inline_hook_id"] = (
            okta_application.settings.inline_hook_id
        )
        application_props["settings_notifications_vpn_help_url"] = (
            okta_application.settings.notifications.vpn.help_url
        )
        application_props["settings_notifications_vpn_message"] = (
            okta_application.settings.notifications.vpn.message
        )
        application_props["settings_notifications_vpn_network_connection"] = (
            okta_application.settings.notifications.vpn.network.connection
        )
        application_props["settings_notifications_vpn_network_exclude"] = json.dumps(
            okta_application.settings.notifications.vpn.network.exclude
        )
        application_props["settings_notifications_vpn_network_include"] = json.dumps(
            okta_application.settings.notifications.vpn.network.include
        )
        if hasattr(okta_application.settings.notes, "admin"):
            application_props["settings_notes_admin"] = (
                okta_application.settings.notes.admin
            )
        if hasattr(okta_application.settings.notes, "enduser"):
            application_props["settings_notes_enduser"] = (
                okta_application.settings.notes.enduser
            )
        # Parse SAML sign-on configuration if present
        if (
            hasattr(okta_application.settings, "sign_on")
            and okta_application.settings.sign_on
        ):
            sign_on = okta_application.settings.sign_on
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
        if (
            hasattr(okta_application.settings, "oauth_client")
            and okta_application.settings.oauth_client
        ):
            application_props["settings_oauth_client_application_type"] = (
                okta_application.settings.oauth_client.application_type.value
            )

            application_props["settings_oauth_client_client_uri"] = (
                okta_application.settings.oauth_client.client_uri
            )
            application_props["settings_oauth_client_consent_method"] = (
                okta_application.settings.oauth_client.consent_method.value
            )
            application_props["settings_oauth_client_grant_Type"] = [
                grant_type.value
                for grant_type in okta_application.settings.oauth_client.grant_types
            ]
            application_props[
                "settings_oauth_client_idp_initiated_login_default_scope"
            ] = json.dumps(
                okta_application.settings.oauth_client.idp_initiated_login.default_scope
            )
            application_props["settings_oauth_client_idp_initiated_login_mode"] = (
                okta_application.settings.oauth_client.idp_initiated_login.mode
            )
            application_props["settings_oauth_client_initiate_login_uri"] = (
                okta_application.settings.oauth_client.initiate_login_uri
            )
            application_props["settings_oauth_client_logo_uri"] = (
                okta_application.settings.oauth_client.logo_uri
            )
            application_props["settings_oauth_client_policy_uri"] = (
                okta_application.settings.oauth_client.policy_uri
            )
            application_props["settings_oauth_client_post_logout_redirect_uris"] = (
                json.dumps(
                    okta_application.settings.oauth_client.post_logout_redirect_uris
                )
            )
            application_props["settings_oauth_client_redirect_uris"] = json.dumps(
                okta_application.settings.oauth_client.redirect_uris
            )
            application_props["settings_oauth_client_response_types"] = [
                response_type.value
                for response_type in okta_application.settings.oauth_client.response_types
            ]
            application_props["settings_oauth_client_tos_uri"] = (
                okta_application.settings.oauth_client.tos_uri
            )
            application_props["settings_oauth_client_wildcard_redirect"] = (
                okta_application.settings.oauth_client.wildcard_redirect
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
        # This returns a dict of somewhat poorly defined value
        # best to treat it as a json blob
        application_props["visibility_app_links"] = json.dumps(
            okta_application.visibility.app_links
        )
        application_props["visibility_auto_launch"] = (
            okta_application.visibility.auto_launch
        )
        application_props["visibility_auto_submit_toolbar"] = (
            okta_application.visibility.auto_submit_toolbar
        )
        # This is an `ApplicationVisibilityHide` model but its
        # really a dict but we'll present it as JSON
        application_props["visibility_hide"] = json.dumps(
            okta_application.visibility.hide.as_dict()
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
    output_application_users = []
    query_parameters = {"limit": 500}
    application_users, resp, err = await okta_client.list_application_users(
        app_id, query_parameters
    )
    if err:
        logger.warning(
            "Failed to fetch users for application %s: %s",
            app_id,
            err,
        )
        return []
    output_application_users += application_users
    while resp.has_next():
        application_users, err = await resp.next()
        if err:
            logger.warning(
                "Failed to fetch next page of users for application %s: %s",
                app_id,
                err,
            )
            break
        output_application_users += application_users
        logger.debug("Fetched %s application users", len(application_users))
    output_application_users_ids = [user.id for user in output_application_users]
    return output_application_users_ids


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
    output_application_groups = []
    query_parameters = {"limit": 200}
    application_groups, resp, err = (
        await okta_client.list_application_group_assignments(app_id, query_parameters)
    )
    if err:
        logger.warning(
            "Failed to fetch groups for application %s: %s",
            app_id,
            err,
        )
        return []
    output_application_groups += application_groups
    while resp.has_next():
        application_groups, err = await resp.next()
        if err:
            logger.warning(
                "Failed to fetch next page of groups for application %s: %s",
                app_id,
                err,
            )
            break
        output_application_groups += application_groups
        logger.debug("Fetched %s application groups", len(application_groups))
    output_application_group_ids = [group.id for group in output_application_groups]
    return output_application_group_ids
