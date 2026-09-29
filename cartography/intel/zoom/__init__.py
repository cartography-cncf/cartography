import logging

import neo4j

from cartography.config import Config
from cartography.graph.job import GraphJob
from cartography.intel.zoom import access
from cartography.intel.zoom import activity
from cartography.intel.zoom import apps
from cartography.intel.zoom import meetings
from cartography.intel.zoom import recordings
from cartography.intel.zoom import settings
from cartography.intel.zoom.client import ZoomClient
from cartography.intel.zoom.users import sync
from cartography.intel.zoom.util import optional_call
from cartography.models.zoom.settings import ZoomSecuritySettingsSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def start_zoom_ingestion(neo4j_session: neo4j.Session, config: Config) -> None:
    if not all(
        (config.zoom_account_id, config.zoom_client_id, config.zoom_client_secret)
    ):
        logger.info("Zoom import is not configured - skipping this module.")
        return

    client = ZoomClient(
        config.zoom_account_id, config.zoom_client_id, config.zoom_client_secret
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
        "reports",
        "dashboard",
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
        if "settings" in sections:
            settings.sync(neo4j_session, client, account_id, tag, users, groups)
            # Membership is complete before reaching this point. Only vanished
            # owners are removed; denied settings for current owners are retained.
            for kind, owners in (
                ("user", [u["zoom_id"] for u in users if u.get("zoom_id")]),
                ("group", None if groups is None else [g["id"] for g in groups]),
            ):
                if owners is not None:
                    GraphJob.from_node_schema(
                        ZoomSecuritySettingsSchema(),
                        {"ACCOUNT_ID": account_id, "UPDATE_TAG": tag},
                        iterationsize=1000,
                        node_filters={"scope_type": kind},
                        excluded_node_filters={"scope_id": owners},
                        delete_current=True,
                    ).run(neo4j_session)
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
        if "reports" in sections:
            activity.sync_reports(
                neo4j_session, client, account_id, tag, users, config.zoom_lookback_days
            )
        if "dashboard" in sections:
            optional_call(
                "dashboard",
                lambda: activity.sync_dashboard(
                    neo4j_session,
                    client,
                    account_id,
                    tag,
                    users,
                    config.zoom_lookback_days,
                ),
            )
