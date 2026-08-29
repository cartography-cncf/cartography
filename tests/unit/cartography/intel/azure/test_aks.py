import cartography.intel.azure.aks as aks


def test_transform_aks_clusters_handles_hybrid_model_dicts() -> None:
    data = aks.transform_aks_clusters(
        [
            {
                "id": "/subscriptions/sub-1/resourceGroups/rg-1/providers/Microsoft.ContainerService/managedClusters/cluster-1",
                "name": "cluster-1",
                "location": "eastus",
                "properties": {
                    "provisioningState": "Succeeded",
                    "kubernetesVersion": "1.28.5",
                    "fqdn": "cluster-1.example",
                    "apiServerAccessProfile": {"enablePrivateCluster": False},
                    "publicNetworkAccess": "Disabled",
                },
            },
        ],
    )

    assert data == [
        {
            "id": "/subscriptions/sub-1/resourceGroups/rg-1/providers/Microsoft.ContainerService/managedClusters/cluster-1",
            "name": "cluster-1",
            "location": "eastus",
            "provisioning_state": "Succeeded",
            "kubernetes_version": "1.28.5",
            "fqdn": "cluster-1.example",
            "api_server_public_access": False,
        },
    ]


def test_transform_agent_pools_handles_hybrid_model_dicts() -> None:
    data = aks.transform_agent_pools(
        [
            {
                "id": "/subscriptions/sub-1/resourceGroups/rg-1/providers/Microsoft.ContainerService/managedClusters/cluster-1/agentPools/pool-1",
                "name": "pool-1",
                "properties": {
                    "provisioningState": "Succeeded",
                    "vmSize": "Standard_D2s_v3",
                    "osType": "Linux",
                    "count": 3,
                },
            },
        ],
    )

    assert data == [
        {
            "id": "/subscriptions/sub-1/resourceGroups/rg-1/providers/Microsoft.ContainerService/managedClusters/cluster-1/agentPools/pool-1",
            "name": "pool-1",
            "provisioning_state": "Succeeded",
            "vm_size": "Standard_D2s_v3",
            "os_type": "Linux",
            "count": 3,
        },
    ]
