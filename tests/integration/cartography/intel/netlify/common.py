import neo4j

import cartography.intel.netlify.users
import tests.data.netlify.users

TEST_ACCOUNT_ID = "5f5a5d7053c60b4be4c8784d"
TEST_ACCOUNT_SLUG = "example-team"
TEST_SITE_ID = "11111111-2222-3333-4444-555555555555"
TEST_GIT_SITE_ID = "99999999-8888-7777-6666-555555555555"
TEST_USER_ID = "5f5a5d7053c60b4be4c8784b"
TEST_UPDATE_TAG = 123456789
TEST_BASE_URL = "https://api.netlify.com/api/v1"


def create_test_netlify_account(
    neo4j_session: neo4j.Session,
    account_id: str = TEST_ACCOUNT_ID,
    update_tag: int = TEST_UPDATE_TAG,
) -> None:
    """
    Create the tenant node every other Netlify node hangs off.

    Written as raw Cypher rather than by calling load_netlify_accounts() so that a resource test
    does not depend on the account sync's own fixtures.
    """
    neo4j_session.run(
        """
        MERGE (a:NetlifyAccount{id: $account_id})
        ON CREATE SET a.firstseen = timestamp()
        SET a.lastupdated = $update_tag, a.slug = $account_slug, a :Tenant
        """,
        account_id=account_id,
        account_slug=TEST_ACCOUNT_SLUG,
        update_tag=update_tag,
    )


def create_test_netlify_users(
    neo4j_session: neo4j.Session,
    account_id: str = TEST_ACCOUNT_ID,
    update_tag: int = TEST_UPDATE_TAG,
) -> None:
    """
    Seed the team's members, for tests of resources that point at a user.

    Goes through load_netlify_users() rather than raw Cypher because the user's team edges are
    MatchLinks, so reproducing them by hand here would drift from the real shape.
    """
    users, _invites = cartography.intel.netlify.users.transform_netlify_users(
        tests.data.netlify.users.NETLIFY_MEMBERS,
        account_id,
    )
    cartography.intel.netlify.users.load_netlify_users(
        neo4j_session,
        users,
        account_id,
        update_tag,
    )


def find_secret_in_graph(
    neo4j_session: neo4j.Session,
    secret: str,
) -> list[tuple[str, str]]:
    """
    Return every (node label, property name) whose value contains `secret`.

    Done in Python rather than Cypher because a property can be a list, and Cypher's toString()
    rejects arrays, so a pure-Cypher scan would blow up on the first list-valued property instead
    of checking it.

    Several Netlify endpoints hand back live credentials (database connection strings, build hook
    URLs, notification hook payloads). This is the assertion that they never land in the graph,
    including via a future model that adds a PropertyRef for one of them.
    """
    hits = []
    for record in neo4j_session.run(
        "MATCH (n) RETURN labels(n) AS labels, properties(n) AS p"
    ):
        for key, value in record["p"].items():
            values = value if isinstance(value, list) else [value]
            if any(secret in str(v) for v in values):
                # The first label is the provider-specific one; ontology labels follow.
                hits.append((record["labels"][0], key))
    return sorted(set(hits))


def common_job_parameters(
    account_id: str = TEST_ACCOUNT_ID,
    update_tag: int = TEST_UPDATE_TAG,
) -> dict:
    return {
        "UPDATE_TAG": update_tag,
        "NETLIFY_ACCOUNT_ID": account_id,
    }
