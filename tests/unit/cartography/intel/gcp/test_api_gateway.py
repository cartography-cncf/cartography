import json
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest
from googleapiclient.errors import HttpError

import cartography.intel.gcp.api_gateway as api_gateway
import tests.data.gcp.api_gateway as test_data

API_A = "projects/p/locations/global/apis/a"
API_B = "projects/p/locations/global/apis/b"
CONFIG_A1 = "projects/1/locations/global/apis/a/configs/c1"
CONFIG_A2 = "projects/1/locations/global/apis/a/configs/c2"
CONFIG_B1 = "projects/1/locations/global/apis/b/configs/c1"


def _http_error(status: int, reason: str | None = None) -> HttpError:
    resp = MagicMock()
    resp.status = status
    payload: dict = {"error": {"code": status}}
    if reason:
        payload["error"]["errors"] = [{"reason": reason}]
    return HttpError(resp=resp, content=json.dumps(payload).encode("utf-8"))


def _single_page_client() -> MagicMock:
    apigateway = MagicMock()
    apigateway.projects().locations().apis().configs().list_next.return_value = None
    return apigateway


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


@pytest.mark.parametrize(
    ("apis_incomplete", "configs_incomplete", "gateways_incomplete", "cleaned"),
    [
        (False, False, False, {"Gateway", "ApiConfig", "Api"}),
        # Configs are listed per Api, so a partial Api listing leaves configs
        # unlisted as well. Gateways are listed on their own and still clean up.
        (True, False, False, {"Gateway"}),
        (False, True, False, {"Gateway", "Api"}),
        (False, False, True, {"ApiConfig", "Api"}),
        (True, True, True, set()),
    ],
)
def test_sync_cleans_up_only_what_was_listed_completely(
    apis_incomplete, configs_incomplete, gateways_incomplete, cleaned
):
    """
    Cleanup deletes whatever the run did not touch. Suppressing it for every
    type whenever any one listing is partial would let a long regional outage
    block cleanup of resources that were listed in full.
    """
    with (
        patch.object(api_gateway, "get_apis", return_value=([], apis_incomplete)),
        patch.object(
            api_gateway, "get_api_configs", return_value=([], configs_incomplete)
        ),
        patch.object(
            api_gateway, "get_gateways", return_value=([], gateways_incomplete)
        ),
        patch.object(api_gateway, "load_apis"),
        patch.object(api_gateway, "load_api_configs"),
        patch.object(api_gateway, "load_gateways"),
        patch.object(api_gateway, "GraphJob") as mock_graph_job,
    ):
        api_gateway.sync(MagicMock(), MagicMock(), "p", 1, {})

    ran = {
        type(call.args[0]).__name__.removeprefix("GCPApiGateway").removesuffix("Schema")
        for call in mock_graph_job.from_node_schema.call_args_list
    }
    assert ran == cleaned


def test_get_api_configs_skips_an_api_deleted_mid_sync():
    """
    An Api deleted between apis.list and configs.list answers 404. Its configs
    are gone with it, so the sync moves on without raising, and the listing is
    still complete for cleanup purposes.
    """
    with patch.object(
        api_gateway,
        "gcp_api_execute_with_retry",
        side_effect=[
            _http_error(404),
            {"apiConfigs": [{"name": CONFIG_B1}]},
            {"name": CONFIG_B1},
        ],
    ):
        configs, incomplete = api_gateway.get_api_configs(
            _single_page_client(), "p", [API_A, API_B]
        )

    assert [(c["name"], c["parentApi"]) for c in configs] == [(CONFIG_B1, API_B)]
    assert incomplete is False


def test_get_api_configs_skips_a_config_deleted_mid_sync():
    with patch.object(
        api_gateway,
        "gcp_api_execute_with_retry",
        side_effect=[
            {"apiConfigs": [{"name": CONFIG_A1}, {"name": CONFIG_A2}]},
            _http_error(404),
            {"name": CONFIG_A2},
        ],
    ):
        configs, incomplete = api_gateway.get_api_configs(
            _single_page_client(), "p", [API_A]
        )

    assert [c["name"] for c in configs] == [CONFIG_A2]
    assert incomplete is False


@pytest.mark.parametrize(
    "error",
    [_http_error(503), _http_error(403, "forbidden")],
    ids=["transient", "permission-denied"],
)
def test_a_failed_full_fetch_keeps_the_config_with_the_document_unknown(error):
    """
    The config is known to exist from configs.list, so a failed FULL fetch must
    neither abort the project's sync (every GCP service after API Gateway would
    be skipped) nor report the config as having no OpenAPI document.
    """
    with patch.object(
        api_gateway,
        "gcp_api_execute_with_retry",
        side_effect=[{"apiConfigs": [{"name": CONFIG_A1}]}, error],
    ):
        configs, incomplete = api_gateway.get_api_configs(
            _single_page_client(), "p", [API_A]
        )

    assert [c["name"] for c in configs] == [CONFIG_A1]
    assert incomplete is False
    transformed = api_gateway.transform_api_configs(configs)[0]
    assert transformed["hasOpenapiDocument"] is None
    assert transformed["openapiDocumentPath"] is None


def test_get_api_configs_records_each_configs_own_parent():
    with patch.object(
        api_gateway,
        "gcp_api_execute_with_retry",
        side_effect=[
            {"apiConfigs": [{"name": CONFIG_A1}]},
            {"name": CONFIG_A1},
            {"apiConfigs": [{"name": CONFIG_B1}]},
            {"name": CONFIG_B1},
        ],
    ):
        configs, _ = api_gateway.get_api_configs(
            _single_page_client(), "p", [API_A, API_B]
        )

    assert {c["name"]: c["parentApi"] for c in configs} == {
        CONFIG_A1: API_A,
        CONFIG_B1: API_B,
    }


def test_get_apis_and_get_gateways_follow_every_page():
    apigateway = MagicMock()
    apigateway.projects().locations().apis().list_next.side_effect = [
        MagicMock(),
        None,
    ]
    apigateway.projects().locations().gateways().list_next.side_effect = [
        MagicMock(),
        None,
    ]
    with patch.object(
        api_gateway,
        "gcp_api_execute_with_retry",
        side_effect=[
            {"apis": [{"name": API_A}]},
            {"apis": [{"name": API_B}]},
            {"gateways": [{"name": "g1"}]},
            {"gateways": [{"name": "g2"}]},
        ],
    ):
        apis, _ = api_gateway.get_apis(apigateway, "p")
        gateways, _ = api_gateway.get_gateways(apigateway, "p")

    assert [a["name"] for a in apis] == [API_A, API_B]
    assert [g["name"] for g in gateways] == ["g1", "g2"]


def test_get_api_configs_follows_every_page():
    apigateway = MagicMock()
    configs_resource = apigateway.projects().locations().apis().configs()
    configs_resource.list_next.side_effect = [MagicMock(), None]
    first_page = {"apiConfigs": [{"name": CONFIG_A1}]}
    with patch.object(
        api_gateway,
        "gcp_api_execute_with_retry",
        side_effect=[
            first_page,
            {"apiConfigs": [{"name": CONFIG_A2}]},
            {"name": CONFIG_A1},
            {"name": CONFIG_A2},
        ],
    ):
        configs, incomplete = api_gateway.get_api_configs(apigateway, "p", [API_A])

    assert [c["name"] for c in configs] == [CONFIG_A1, CONFIG_A2]
    assert incomplete is False
    configs_resource.list_next.assert_any_call(
        previous_request=configs_resource.list.return_value,
        previous_response=first_page,
    )


def test_get_api_configs_flags_unreachable_locations_as_incomplete():
    """
    The unreachable page comes first so a later clean page cannot clear the
    flag. A missed flag lets cleanup delete configs that still exist.
    """
    apigateway = MagicMock()
    apigateway.projects().locations().apis().configs().list_next.side_effect = [
        MagicMock(),
        None,
    ]
    with patch.object(
        api_gateway,
        "gcp_api_execute_with_retry",
        side_effect=[
            {"apiConfigs": [{"name": CONFIG_A1}], "unreachableLocations": ["x"]},
            {"apiConfigs": [{"name": CONFIG_A2}]},
            {"name": CONFIG_A1},
            {"name": CONFIG_A2},
        ],
    ):
        configs, incomplete = api_gateway.get_api_configs(apigateway, "p", [API_A])

    assert [c["name"] for c in configs] == [CONFIG_A1, CONFIG_A2]
    assert incomplete is True


@pytest.mark.parametrize(
    ("raw", "email"),
    [
        (
            "projects/-/serviceAccounts/gw@p.iam.gserviceaccount.com",
            "gw@p.iam.gserviceaccount.com",
        ),
        ("gw@p.iam.gserviceaccount.com", "gw@p.iam.gserviceaccount.com"),
        (None, None),
    ],
)
def test_transform_api_configs_extracts_the_backend_service_account_email(raw, email):
    config = {"name": CONFIG_A1, "parentApi": API_A, "gatewayServiceAccount": raw}

    result = api_gateway.transform_api_configs([config])[0]

    assert result["gatewayServiceAccountEmail"] == email
