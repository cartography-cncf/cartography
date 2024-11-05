import cartography.intel.aws.wafv2
import tests.data.aws.wafv2

TEST_ACCOUNT_ID = '000000000000'
TEST_UPDATE_TAG = 123456789


def test_load_waf_acl(neo4j_session, *args):
    """
    Ensure that expected buckets get loaded with their key fields.
    """
    data = tests.data.aws.wafv2.LIST_WEB_ACL
    cartography.intel.aws.wafv2.load_waf_acl(neo4j_session, data, TEST_ACCOUNT_ID, TEST_UPDATE_TAG)

    nodes = neo4j_session.run(
        """
        MATCH (n:WAFv2WebACL) return n.id, n.name
        """,
    )
    assert nodes[0]['n.id'] == data[0]['Id']


