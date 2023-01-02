from tests.integration.util import check_nodes
from tests.integration.util import check_rels


def test_check_rels(neo4j_session):
    # Arrange
    neo4j_session.run(
        """
        MERGE (homer:Human{id: "Homer"})

        MERGE (bart:Human{id: "Bart"})
        MERGE (homer)<-[:PARENT]-(bart)

        MERGE (lisa:Human{id: "Lisa"})
        MERGE (homer)<-[:PARENT]-(lisa)
        """,
    )

    # Act and assert
    expected = {
        ('Homer', 'Lisa'),
        ('Homer', 'Bart'),
    }
    assert check_rels(neo4j_session, 'Human', 'id', 'Human', 'id', 'PARENT') == expected


def test_check_nodes(neo4j_session):
    neo4j_session.run(
        """
        MERGE (w:WorldAsset{id: "the-worldasset-id-1"})
        ON CREATE SET w.lastupdated = 1
        MERGE (w2:WorldAsset{id: "the-worldasset-id-2"})
        ON CREATE SET w2.lastupdated = 1
        """,
    )

    expected = {
        ('the-worldasset-id-1', 1),
        ('the-worldasset-id-2', 1),
    }

    assert check_nodes(
        neo4j_session,
        'WorldAsset',
        ['id', 'lastupdated'],
    ) == expected

    assert check_nodes(neo4j_session, 'WorldAsset', []) is None
