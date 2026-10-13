import cartography.intel.subimage.neo4jusers
import tests.data.subimage.neo4jusers


def test_transform():
    # Act
    result = cartography.intel.subimage.neo4jusers.transform(
        tests.data.subimage.neo4jusers.SUBIMAGE_NEO4J_USERS_RAW,
    )

    # Assert
    assert result == tests.data.subimage.neo4jusers.SUBIMAGE_NEO4J_USERS_TRANSFORMED
