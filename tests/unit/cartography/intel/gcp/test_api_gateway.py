from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.intel.gcp.api_gateway as api_gateway
import tests.data.gcp.api_gateway as test_data


def test_transform_apis_shapes_records():
    result = api_gateway.transform_apis(test_data.LIST_APIS_RESPONSE)

    assert len(result) == 2
    orders = result[0]
    assert orders["id"] == orders["name"]
    assert orders["displayName"] == "Orders API"
    assert (
        orders["managedService"]
        == "orders-api-1a2b3c.apigateway.test-project-123.cloud.goog"
    )
    assert orders["state"] == "ACTIVE"


def test_transform_apis_tolerates_missing_optional_fields():
    # displayName is optional upstream and must not raise.
    result = api_gateway.transform_apis(test_data.LIST_APIS_RESPONSE)

    internal = result[1]
    assert internal["displayName"] is None
    assert internal["state"] == "CREATING"


def test_transform_api_configs_links_to_the_api_it_was_listed_under():
    """
    Config names carry the project number and Api names the project id, so
    trimming a config name never matches its Api node. The link must come from
    the Api the config was listed under.
    """
    result = api_gateway.transform_api_configs(test_data.LIST_API_CONFIGS_RESPONSE)

    assert (
        result[0]["apiId"]
        == "projects/test-project-123/locations/global/apis/orders-api"
    )
    assert (
        result[1]["apiId"]
        == "projects/test-project-123/locations/global/apis/internal-api"
    )
    assert not result[0]["id"].startswith(result[0]["apiId"])


def test_transform_api_configs_records_openapi_document_presence():
    result = api_gateway.transform_api_configs(test_data.LIST_API_CONFIGS_RESPONSE)

    assert result[0]["hasOpenapiDocument"] is True
    assert result[0]["openapiDocumentPath"] == "openapi.yaml"

    # gRPC-backed configs carry no OpenAPI document at all.
    assert result[1]["hasOpenapiDocument"] is False
    assert result[1]["openapiDocumentPath"] is None


def test_transform_gateways_parses_region_from_resource_name():
    result = api_gateway.transform_gateways(test_data.LIST_GATEWAYS_RESPONSE)

    assert result[0]["region"] == "us-central1"
    assert result[1]["region"] == "europe-west1"


def test_transform_gateways_handles_absent_hostname():
    # defaultHostname is only populated once the gateway reaches ACTIVE.
    result = api_gateway.transform_gateways(test_data.LIST_GATEWAYS_RESPONSE)

    assert result[0]["defaultHostname"] == "orders-gw-1a2b3c.uc.gateway.dev"
    assert result[1]["defaultHostname"] is None


def test_get_api_configs_requests_full_view():
    """
    configs.list never returns openapiDocuments and configs.get defaults to
    view=BASIC, so the module must ask for FULL explicitly. Regressing this
    silently produces configs with no document rather than an error.
    """
    apigateway = MagicMock()
    configs_resource = apigateway.projects().locations().apis().configs()
    configs_resource.list_next.return_value = None

    with patch.object(
        api_gateway,
        "gcp_api_execute_with_retry",
        side_effect=[
            {"apiConfigs": [{"name": "projects/p/locations/global/apis/a/configs/c"}]},
            {"name": "projects/p/locations/global/apis/a/configs/c", "state": "ACTIVE"},
        ],
    ):
        configs, _ = api_gateway.get_api_configs(
            apigateway, "p", ["projects/p/locations/global/apis/a"]
        )

    configs_resource.get.assert_called_once_with(
        name="projects/p/locations/global/apis/a/configs/c", view="FULL"
    )
    assert configs[0]["parentApi"] == "projects/p/locations/global/apis/a"


def test_get_apis_flags_unreachable_locations_as_incomplete():
    """
    A partial listing must be reported so sync can suppress cleanup. Without
    this, a transient regional failure deletes gateways that still exist.
    """
    apigateway = MagicMock()
    apigateway.projects().locations().apis().list_next.return_value = None

    with patch.object(
        api_gateway,
        "gcp_api_execute_with_retry",
        return_value={"apis": [], "unreachableLocations": ["us-east1"]},
    ):
        apis, incomplete = api_gateway.get_apis(apigateway, "p")

    assert apis == []
    assert incomplete is True


def test_get_apis_complete_listing_is_not_flagged():
    apigateway = MagicMock()
    apigateway.projects().locations().apis().list_next.return_value = None

    with patch.object(
        api_gateway,
        "gcp_api_execute_with_retry",
        return_value={"apis": [{"name": "projects/p/locations/global/apis/a"}]},
    ):
        apis, incomplete = api_gateway.get_apis(apigateway, "p")

    assert len(apis) == 1
    assert incomplete is False


def test_sync_suppresses_cleanup_when_a_listing_is_incomplete():
    with (
        patch.object(api_gateway, "get_apis", return_value=([], True)),
        patch.object(api_gateway, "get_api_configs", return_value=([], False)),
        patch.object(api_gateway, "get_gateways", return_value=([], False)),
        patch.object(api_gateway, "load_apis"),
        patch.object(api_gateway, "load_api_configs"),
        patch.object(api_gateway, "load_gateways"),
        patch.object(api_gateway, "cleanup_api_gateway") as mock_cleanup,
    ):
        api_gateway.sync(MagicMock(), MagicMock(), "p", 1, {})

    mock_cleanup.assert_not_called()


def test_sync_runs_cleanup_when_every_listing_is_complete():
    with (
        patch.object(api_gateway, "get_apis", return_value=([], False)),
        patch.object(api_gateway, "get_api_configs", return_value=([], False)),
        patch.object(api_gateway, "get_gateways", return_value=([], False)),
        patch.object(api_gateway, "load_apis"),
        patch.object(api_gateway, "load_api_configs"),
        patch.object(api_gateway, "load_gateways"),
        patch.object(api_gateway, "cleanup_api_gateway") as mock_cleanup,
    ):
        api_gateway.sync(MagicMock(), MagicMock(), "p", 1, {})

    mock_cleanup.assert_called_once()
