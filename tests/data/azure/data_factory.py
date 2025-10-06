MOCK_FACTORIES = [
    {
        'id': '/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.DataFactory/factories/my-test-adf',
        'name': 'my-test-adf',
        'location': 'eastus',
        'properties': {
            'provisioning_state': 'Succeeded',
            'create_time': '2025-01-01T12:00:00.000Z',
            'version': '2018-06-01',
        },
    },
]

MOCK_PIPELINES = [
    {
        'id': '/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.DataFactory/factories/my-test-adf/pipelines/MyPipeline',
        'name': 'MyPipeline',
        'description': 'A test pipeline.',
    },
]

MOCK_DATASETS = [
    {
        'id': '/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.DataFactory/factories/my-test-adf/datasets/MyDataset',
        'name': 'MyDataset',
        'properties': {
            'type': 'AzureBlob',
        },
    },
]

MOCK_LINKED_SERVICES = [
    {
        'id': '/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.DataFactory/factories/my-test-adf/linkedservices/MyLinkedService',
        'name': 'MyLinkedService',
        'properties': {
            'type': 'AzureBlobStorage',
        },
    },
]