# Mock data for a top-level Data Factory
MOCK_FACTORIES = [
    {
        "id": "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.DataFactory/factories/my-test-adf",
        "name": "my-test-adf",
        "location": "eastus",
        "properties": {
            "provisioningState": "Succeeded",
            "createTime": "2025-01-01T12:00:00.000Z",
            "version": "2018-06-01",
        },
    },
]

# Mock data for a Linked Service that connects to a Data Lake (AzureBlobFS)
MOCK_LINKED_SERVICES = [
    {
        "id": "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.DataFactory/factories/my-test-adf/linkedservices/MyTestDataLakeLink",
        "name": "MyTestDataLakeLink",
        "properties": {
            "type": "AzureBlobFS",
            "type_properties": {
                "connectionString": "DefaultEndpointsProtocol=https;AccountName=mytestdatalake;EndpointSuffix=core.windows.net;",
            },
        },
    },
]

# Mock data for a Dataset that uses the Linked Service above
MOCK_DATASETS = [
    {
        "id": "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.DataFactory/factories/my-test-adf/datasets/MyTestSourceDataset",
        "name": "MyTestSourceDataset",
        "properties": {
            "type": "DelimitedText",
            "linked_service_name": {
                "type": "LinkedServiceReference",
                "reference_name": "MyTestDataLakeLink",
            },
        },
    },
]

# Mock data for a Pipeline that uses the Dataset above
MOCK_PIPELINES = [
    {
        "id": "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.DataFactory/factories/my-test-adf/pipelines/MyTestPipeline",
        "name": "MyTestPipeline",
        "properties": {
            "description": "A test pipeline.",
        },
        # This is the key correction: `activities` is at the top level
        "activities": [
            {
                "name": "MyCopyActivity",
                "type": "Copy",
                "inputs": [
                    {
                        "type": "DatasetReference",
                        "reference_name": "MyTestSourceDataset",
                    },
                ],
                "outputs": [],
            },
        ],
    },
]
