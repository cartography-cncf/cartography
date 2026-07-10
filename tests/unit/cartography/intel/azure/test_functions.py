from azure.mgmt.web.models import SiteConfigResource

import cartography.intel.azure.functions as functions


def test_transform_function_apps_reads_sdk_11_site_config_shape() -> None:
    app_id = (
        "/subscriptions/sub-1/resourceGroups/rg-1/providers/Microsoft.Web/sites/fn-1"
    )
    digest = "sha256:" + "a" * 64
    image_uri = f"repo/image@{digest}"

    data = functions.transform_function_apps(
        [
            {
                "id": app_id,
                "name": "fn-1",
                "kind": "functionapp,linux",
                "location": "eastus",
                "properties": {
                    "state": "Running",
                    "defaultHostName": "fn-1.azurewebsites.net",
                    "httpsOnly": True,
                },
            },
        ],
        {app_id: SiteConfigResource(linux_fx_version=f"DOCKER|{image_uri}").as_dict()},
    )

    assert data == [
        {
            "id": app_id,
            "name": "fn-1",
            "kind": "functionapp,linux",
            "location": "eastus",
            "state": "Running",
            "default_host_name": "fn-1.azurewebsites.net",
            "https_only": True,
            "is_container": True,
            "deployment_type": "container",
            "image_uri": image_uri,
            "image_digest": digest,
            "architecture_normalized": "amd64",
            "tags": None,
            "identity_principal_ids": [],
        },
    ]
