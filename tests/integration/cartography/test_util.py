from unittest.mock import patch

from cartography.stats import get_stats_client
from cartography.stats import ScopedStatsClient
from cartography.util import merge_module_sync_metadata


TEST_ACCOUNT_ID = '000000000000'
TEST_UPDATE_TAG = 123456789


@patch.object(ScopedStatsClient, 'incr')
def test_merge_module_sync_metadata(mock_stat_incr, neo4j_session):
    # Arrange
    group_type = 'AWSAccount'
    group_id = TEST_ACCOUNT_ID
    synced_type = 'S3Bucket'
    stat_handler = get_stats_client(__name__)
    expected_nodes = {
        (
            f'AWSAccount_{TEST_ACCOUNT_ID}_S3Bucket',
            'AWSAccount',
            TEST_ACCOUNT_ID,
            'S3Bucket',
            TEST_UPDATE_TAG,
        ),
    }
    # Act
    merge_module_sync_metadata(
        neo4j_session=neo4j_session,
        group_type=group_type,
        group_id=group_id,
        synced_type=synced_type,
        update_tag=TEST_UPDATE_TAG,
        stat_handler=stat_handler,
    )
    # Assert
    nodes = neo4j_session.run(
        f"""
        MATCH (m:ModuleSyncMetadata{{id:'AWSAccount_{TEST_ACCOUNT_ID}_S3Bucket'}})
        RETURN
            m.id,
            m.syncedtype,
            m.grouptype,
            m.groupid,
            m.lastupdated
    """,
    )
    # Assert
    actual_nodes = {
        (
            n['m.id'],
            n['m.grouptype'],
            n['m.groupid'],
            n['m.syncedtype'],
            n['m.lastupdated'],
        )
        for n in nodes
    }
    assert actual_nodes == expected_nodes
    mock_stat_incr.assert_called_once_with(
        f'{group_type}_{group_id}_{synced_type}_lastupdated',
        TEST_UPDATE_TAG,
    )
