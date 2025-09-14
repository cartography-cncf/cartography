import tests.data.aws.apigatewayv2 as test_data
from cartography.intel.aws import apigatewayv2


def test_transform_apigatewayv2_apis():
    transformed = apigatewayv2.transform_apigatewayv2_apis(test_data.GET_APIS)
    assert transformed[0]["id"] == "api-001"
    assert transformed[0]["protocoltype"] == "HTTP"
