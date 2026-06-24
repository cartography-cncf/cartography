MOCK_CLUSTERS = [
    {
        "id": "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.ContainerService/managedClusters/my-test-aks-cluster",
        "name": "my-test-aks-cluster",
        "location": "eastus",
        "properties": {
            "provisioningState": "Succeeded",
            "kubernetesVersion": "1.28.5",
            "fqdn": "my-test-aks-cluster-dns-abcdef.hcp.eastus.azmk8s.io",
            "apiServerAccessProfile": {"enablePrivateCluster": False},
        },
        "tags": {"env": "prod", "service": "aks"},
    },
    {
        "id": "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.ContainerService/managedClusters/my-private-aks-cluster",
        "name": "my-private-aks-cluster",
        "location": "eastus",
        "properties": {
            "provisioningState": "Succeeded",
            "kubernetesVersion": "1.28.5",
            "fqdn": "my-private-aks-cluster-dns-abcdef.hcp.eastus.azmk8s.io",
            "apiServerAccessProfile": {"enablePrivateCluster": True},
        },
        "tags": {"env": "prod", "service": "aks"},
    },
    # API Server VNet Integration: not a classic private cluster, but public
    # network access is disabled. The transform must still mark it as not
    # publicly reachable via the second gate.
    {
        "id": "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.ContainerService/managedClusters/my-vnet-aks-cluster",
        "name": "my-vnet-aks-cluster",
        "location": "eastus",
        "properties": {
            "provisioningState": "Succeeded",
            "kubernetesVersion": "1.28.5",
            "fqdn": "my-vnet-aks-cluster-dns-abcdef.hcp.eastus.azmk8s.io",
            "apiServerAccessProfile": {"enablePrivateCluster": False},
            "publicNetworkAccess": "Disabled",
        },
        "tags": {"env": "prod", "service": "aks"},
    },
]

MOCK_AGENT_POOLS = [
    {
        # CORRECTED: Added the real 'id' field, as provided by the API.
        "id": "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.ContainerService/managedClusters/my-test-aks-cluster/agentPools/agentpool",
        "name": "agentpool",
        "properties": {
            "provisioningState": "Succeeded",
            "vmSize": "Standard_D2s_v3",
            "osType": "Linux",
            "count": 3,
        },
    },
]
