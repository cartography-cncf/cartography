from typing import Dict
from typing import List

import neo4j

from cartography.intel.okta import cleanup_okta_groups
from cartography.intel.okta.groups import load_okta_group_members
from cartography.intel.okta.groups import transform_okta_group_member_list
from tests.data.okta.groups import GROUP_MEMBERS_SAMPLE_DATA


TEST_ORG_ID = 'ORG_ID'


def test_load_okta_group_members(neo4j_session):
    # Arrange: Create org with group 123
    TEST_GROUP_ID = 'MY_GROUP_123'
    TEST_UPDATE_TAG = 000000
    neo4j_session.run(
        '''
        MERGE (o:OktaOrganization{id: {ORG_ID}})-[:RESOURCE]->(g:OktaGroup{id: {GROUP_ID}, lastupdated: {UPDATE_TAG}})
        ''',
        ORG_ID=TEST_ORG_ID,
        GROUP_ID=TEST_GROUP_ID,
        UPDATE_TAG=TEST_UPDATE_TAG,
    )
    transformed_members: List[Dict] = transform_okta_group_member_list(GROUP_MEMBERS_SAMPLE_DATA)

    # Act: Attach members to group 123
    load_okta_group_members(neo4j_session, TEST_GROUP_ID, transformed_members, TEST_UPDATE_TAG)

    # Assert: members are attached to group 123
    result: neo4j.BoltStatementResult = neo4j_session.run(
        'MATCH (o:OktaGroup{id: {GROUP_ID}})<-[:MEMBER_OF_OKTA_GROUP]-(u:OktaUser) RETURN u.last_name',
        GROUP_ID=TEST_GROUP_ID,
    )
    actual_nodes = {n['u.last_name'] for n in result}
    expected_nodes = {
        'Clarkson',
        'Hammond',
        'May',
    }
    assert actual_nodes == expected_nodes


def test_cleanup_okta_groups(neo4j_session):
    # Arrange: Create group 456 with update tag=111111
    TEST_GROUP_ID = 'MY_GROUP_456'
    UPDATE_TAG_T1 = 111111
    UPDATE_TAG_T2 = 222222
    neo4j_session.run(
        'MERGE (:OktaOrganization{id: {ORG_ID}})-[:RESOURCE]->(:OktaGroup{id: {GROUP_ID}, lastupdated: {UPDATE_TAG}})',
        ORG_ID=TEST_ORG_ID,
        GROUP_ID=TEST_GROUP_ID,
        UPDATE_TAG=UPDATE_TAG_T1,
    )

    # Assert 1: MY_GROUP_456 exists
    expected_nodes = {(TEST_GROUP_ID)}
    nodes = neo4j_session.run(
        "MATCH (g:OktaGroup{id: {GROUP_ID}}) RETURN g.id",
        GROUP_ID=TEST_GROUP_ID,
    )
    actual_nodes = {(n['g.id']) for n in nodes}
    assert actual_nodes == expected_nodes

    # Act: delete all groups where update tag != 222222
    COMMON_JOB_PARAMETERS = {
        'UPDATE_TAG': UPDATE_TAG_T2,
        'OKTA_ORG_ID': TEST_ORG_ID,
    }
    cleanup_okta_groups(neo4j_session, COMMON_JOB_PARAMETERS)

    # Assert 2: cleanup job has run; no groups exist anymore.
    expected_nodes = set()
    nodes = neo4j_session.run("MATCH (g:OktaGroup) RETURN g.id")
    actual_nodes = {(n['g.id']) for n in nodes}
    assert actual_nodes == expected_nodes
