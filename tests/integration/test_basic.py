from cartography.intel import create_indexes


def test_create_indexes(neo4j_session):
    # ensure the idempotency of creating indexes
    create_indexes.run(neo4j_session, None)
    create_indexes.run(neo4j_session, None)
