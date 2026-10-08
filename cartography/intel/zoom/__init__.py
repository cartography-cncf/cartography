import logging

import neo4j

from cartography.config import Config
from cartography.intel.zoom import access
from cartography.intel.zoom import apps
from cartography.intel.zoom import client_versions
from cartography.intel.zoom import meetings
from cartography.intel.zoom import recordings
from cartography.intel.zoom import settings
from cartography.intel.zoom.client import RequestBudget
from cartography.intel.zoom.client import ZoomClient
from cartography.intel.zoom.users import cleanup as cleanup_users
from cartography.intel.zoom.users import sync
from cartography.intel.zoom.util import optional_call
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def start_zoom_ingestion(neo4j_session: neo4j.Session, config: Config) -> None:
    if not all(
        (config.zoom_account_id, config.zoom_client_id, config.zoom_client_secret)
    ):
        logger.info("Zoom import is not configured - skipping this module.")
        return

    if config.zoom_request_limit < 1:
        raise ValueError("Zoom request limit must be positive")
    client = ZoomClient(
        config.zoom_account_id,
        config.zoom_client_id,
        config.zoom_client_secret,
        RequestBudget(config.zoom_request_limit),
    )
    sections = {
        section.strip()
        for section in config.zoom_sections.split(",")
        if section.strip()
    }
    unknown = sections - {
        "groups",
        "roles",
        "settings",
        "apps",
        "meetings",
        "recordings",
        "client_versions",
    }
    if unknown:
        raise ValueError(f"Unknown Zoom sections: {sorted(unknown)}")
    if not 1 <= config.zoom_lookback_days <= 30:
        raise ValueError("Zoom lookback days must be between 1 and 30")
    account_id, tag = config.zoom_account_id, config.update_tag
    with client.session:
        users = sync(neo4j_session, client, account_id, tag)
        groups = None
        if "groups" in sections or "settings" in sections:
            groups = optional_call(
                "groups",
                lambda: access.sync_groups(
                    neo4j_session, client, account_id, tag, users
                ),
            )
        if "roles" in sections:
            optional_call(
                "roles",
                lambda: access.sync_roles(
                    neo4j_session, client, account_id, tag, users
                ),
            )
        settings_complete = False
        if "settings" in sections:
            settings_complete = settings.sync(
                neo4j_session, client, account_id, tag, users, groups
            )
        if "apps" in sections:
            optional_call(
                "apps", lambda: apps.sync(neo4j_session, client, account_id, tag)
            )
        if "meetings" in sections:
            meetings.sync(neo4j_session, client, account_id, tag, users)
        if "recordings" in sections:
            recordings.sync(
                neo4j_session, client, account_id, tag, users, config.zoom_lookback_days
            )
        if "client_versions" in sections:
            optional_call(
                "client_versions",
                lambda: client_versions.sync(neo4j_session, client, account_id, tag),
            )
        cleanup_users(neo4j_session, account_id, tag)
        if settings_complete:
            settings.cleanup(neo4j_session, account_id, tag)
