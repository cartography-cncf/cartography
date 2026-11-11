from typing import Any

import neo4j

from cartography.client.core.tx import run_write_query


# DEPRECATED: remove with the SlackUser compatibility label on SlackBot in v1.0.0.
def migrate_members_that_changed_kind(
    neo4j_session: neo4j.Session,
    users: list[dict[str, Any]],
    bots: list[dict[str, Any]],
) -> None:
    """
    Reuse the existing node when Slack reports a member as the other kind.

    load() merges on the primary label, and a SlackBot also carries the SlackUser
    compatibility label. A former user gets a second node as a bot, and a former
    bot matches the user merge and keeps its bot labels. Graphs written before
    SlackBot existed hold every bot as a SlackUser. Resetting the properties drops
    the ones that only the former kind sets. Without the compatibility label, each
    kind merges only its own nodes and cleanup deletes the node of the former kind.
    """
    run_write_query(
        neo4j_session,
        """
        MATCH (member:SlackUser)
        WHERE member.id IN $bot_ids AND NOT member:SlackBot
        SET member = {id: member.id, firstseen: member.firstseen}
        SET member:SlackBot
        REMOVE member:UserAccount
        """,
        bot_ids=[bot["id"] for bot in bots],
    )
    run_write_query(
        neo4j_session,
        """
        MATCH (member:SlackBot)
        WHERE member.id IN $user_ids
        SET member = {id: member.id, firstseen: member.firstseen}
        REMOVE member:SlackBot:ThirdPartyApp
        """,
        user_ids=[user["id"] for user in users],
    )
