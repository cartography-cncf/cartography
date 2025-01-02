import pytest

from tests.integration.util import check_nodes
from tests.integration.util import check_rels


@pytest.mark.flaky(reruns=5)
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
    assert check_rels(neo4j_session, 'Human', 'id', 'Human', 'id', 'PARENT', False) == expected


def test_check_nodes(neo4j_session):
    # Arrange
    neo4j_session.run(
        """
        MERGE (w:WorldAsset{id: "the-worldasset-id-1"})
        ON CREATE SET w.lastupdated = 1
        MERGE (w2:WorldAsset{id: "the-worldasset-id-2"})
        ON CREATE SET w2.lastupdated = 1
        """,
    )

    # Act and assert
    expected = {
        ('the-worldasset-id-1', 1),
        ('the-worldasset-id-2', 1),
    }
    assert check_nodes(
        neo4j_session,
        'WorldAsset',
        ['id', 'lastupdated'],
    ) == expected


def test_check_nodes_empty_list_raises_exc(neo4j_session):
    with pytest.raises(ValueError):
        check_nodes(neo4j_session, 'WorldAsset', [])
