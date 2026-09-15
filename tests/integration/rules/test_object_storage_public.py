from cartography.client.core.tx import read_list_of_dicts_tx
from cartography.rules.data.rules.object_storage_public import (
    _cloudflare_r2_bucket_public,
)
from cartography.rules.data.rules.object_storage_public import (
    _supabase_storage_bucket_public,
)


def _reset_graph(neo4j_session) -> None:
    neo4j_session.run("MATCH (n) DETACH DELETE n")


def test_cloudflare_r2_public_and_r2_dev(neo4j_session) -> None:
    """A custom public domain and the r2.dev development URL both make a bucket readable."""
    _reset_graph(neo4j_session)
    neo4j_session.run(
        """
        CREATE (acc:CloudflareAccount {id: 'acct-1'})
        CREATE (pub:CloudflareR2Bucket {id: 'b-public', name: 'public',
            location: 'weur', public: true, r2_dev_enabled: false})
        CREATE (dev:CloudflareR2Bucket {id: 'b-r2dev', name: 'r2dev',
            location: 'enam', public: false, r2_dev_enabled: true})
        CREATE (priv:CloudflareR2Bucket {id: 'b-private', name: 'private',
            location: 'weur', public: false, r2_dev_enabled: false})
        CREATE (unknown:CloudflareR2Bucket {id: 'b-null', name: 'null'})
        MERGE (acc)-[:RESOURCE]->(pub)
        MERGE (acc)-[:RESOURCE]->(dev)
        MERGE (acc)-[:RESOURCE]->(priv)
        MERGE (acc)-[:RESOURCE]->(unknown)
        """
    )

    findings = neo4j_session.execute_read(
        read_list_of_dicts_tx, _cloudflare_r2_bucket_public.cypher_query
    )

    assert {f["id"] for f in findings} == {"b-public", "b-r2dev"}
    # public_access is the OR of the two signals, and coalesce keeps it a boolean even when
    # only one of them is set.
    assert all(f["public_access"] is True for f in findings)
    assert {f["region"] for f in findings} == {"weur", "enam"}


def test_supabase_storage_public_bucket(neo4j_session) -> None:
    _reset_graph(neo4j_session)
    neo4j_session.run(
        """
        CREATE (prj:SupabaseProject {id: 'ref-1'})
        CREATE (pub:SupabaseStorageBucket {id: 'ref-1/avatars', name: 'avatars',
            public: true})
        CREATE (priv:SupabaseStorageBucket {id: 'ref-1/private', name: 'private',
            public: false})
        MERGE (prj)-[:RESOURCE]->(pub)
        MERGE (prj)-[:RESOURCE]->(priv)
        """
    )

    findings = neo4j_session.execute_read(
        read_list_of_dicts_tx, _supabase_storage_bucket_public.cypher_query
    )

    assert [(f["id"], f["name"], f["public_access"]) for f in findings] == [
        ("ref-1/avatars", "avatars", True)
    ]
