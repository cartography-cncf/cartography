MOCK_CLUSTERS = [
    {
        "id": "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.ContainerService/managedClusters/my-test-aks-cluster",
        "name": "my-test-aks-cluster",
        "location": "eastus",
        "properties": {
            "provisioning_state": "Succeeded",
            "kubernetes_version": "1.28.5",
            "fqdn": "my-test-aks-cluster-dns-abcdef.hcp.eastus.azmk8s.io",
        },
    },
]

MOCK_AGENT_POOLS = [
    {
        # CORRECTED: Added the real 'id' field, as provided by the API.
        "id": "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.ContainerService/managedClusters/my-test-aks-cluster/agentPools/agentpool",
        "name": "agentpool",
        "properties": {
            "provisioning_state": "Succeeded",
            "vm_size": "Standard_D2s_v3",
            "os_type": "Linux",
            "count": 3,
        },
    },
]
