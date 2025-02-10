import tests.data.aws.apigateway as test_data
from cartography.intel.aws.apigateway import parse_policy


def test_parse_policy():
    res = parse_policy("1", test_data.DOUBLY_ESCAPED_POLICY)

    assert (res) is not None
    assert (res["api_id"]) is not None
    assert (res["internet_accessible"]) is not None
    assert (res["accessible_actions"]) is not None


def test_none_policy():
    res = parse_policy(None, None)

    assert (res) is None
