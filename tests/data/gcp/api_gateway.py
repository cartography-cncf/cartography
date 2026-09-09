# Shapes match apigateway.googleapis.com v1 discovery revision 20260902.
# https://apigateway.googleapis.com/$discovery/rest?version=v1

LIST_APIS_RESPONSE = [
    {
        "name": "projects/test-project-123/locations/global/apis/orders-api",
        "createTime": "2024-01-01T00:00:00Z",
        "updateTime": "2024-01-02T00:00:00Z",
        "displayName": "Orders API",
        "managedService": "orders-api-1a2b3c.apigateway.test-project-123.cloud.goog",
        "state": "ACTIVE",
        "labels": {"env": "prod"},
    },
    {
        # displayName and labels are optional upstream.
        "name": "projects/test-project-123/locations/global/apis/internal-api",
        "createTime": "2024-03-01T00:00:00Z",
        "updateTime": "2024-03-01T00:00:00Z",
        "managedService": "internal-api-4d5e6f.apigateway.test-project-123.cloud.goog",
        "state": "CREATING",
    },
]

# Returned by configs.get(view=FULL). configs.list has no view parameter and
# omits openapiDocuments entirely, which is why the module fetches per config.
LIST_API_CONFIGS_RESPONSE = [
    {
        "name": "projects/test-project-123/locations/global/apis/orders-api/configs/v1",
        "createTime": "2024-01-01T00:00:00Z",
        "updateTime": "2024-01-01T00:00:00Z",
        "displayName": "v1",
        "gatewayServiceAccount": "projects/-/serviceAccounts/gw@test-project-123.iam.gserviceaccount.com",
        "serviceConfigId": "orders-api-1a2b3c-2024-01-01r0",
        "state": "ACTIVE",
        "openapiDocuments": [
            {
                "document": {
                    "path": "openapi.yaml",
                    # base64 of a minimal OAS2 document. Contents are ingested
                    # verbatim; parsing security definitions is a follow-up.
                    "contents": "c3dhZ2dlcjogJzIuMCcK",
                }
            }
        ],
    },
    {
        # No openapiDocuments: a gRPC-backed config.
        "name": "projects/test-project-123/locations/global/apis/internal-api/configs/v1",
        "createTime": "2024-03-01T00:00:00Z",
        "updateTime": "2024-03-01T00:00:00Z",
        "serviceConfigId": "internal-api-4d5e6f-2024-03-01r0",
        "state": "ACTIVE",
        "grpcServices": [{"fileDescriptorSet": {"path": "api_descriptor.pb"}}],
    },
]

LIST_GATEWAYS_RESPONSE = [
    {
        "name": "projects/test-project-123/locations/us-central1/gateways/orders-gw",
        "createTime": "2024-01-03T00:00:00Z",
        "updateTime": "2024-01-04T00:00:00Z",
        "displayName": "Orders Gateway",
        "apiConfig": "projects/test-project-123/locations/global/apis/orders-api/configs/v1",
        "state": "ACTIVE",
        "defaultHostname": "orders-gw-1a2b3c.uc.gateway.dev",
        "labels": {"env": "prod"},
    },
    {
        # No defaultHostname yet: gateway still creating.
        "name": "projects/test-project-123/locations/europe-west1/gateways/internal-gw",
        "createTime": "2024-03-02T00:00:00Z",
        "updateTime": "2024-03-02T00:00:00Z",
        "apiConfig": "projects/test-project-123/locations/global/apis/internal-api/configs/v1",
        "state": "CREATING",
    },
]
