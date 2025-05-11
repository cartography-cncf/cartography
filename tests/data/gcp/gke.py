# flake8: noqa
GKE_RESPONSE = {
    "clusters": [
        {
            "selfLink": "https://container.googleapis.com/v1/projects/test-cluster/locations/europe-west2/clusters/test-cluster",
            "createTime": "2019-01-01T00:00:00+00:00",
            "name": "test-cluster",
            "description": "Test cluster",
            "loggingService": "logging.googleapis.com",
            "monitoringService": "none",
            "network": "test-cluster",
            "subnetwork": "test-cluster",
            "clusterIpv4Cidr": "0.0.0.0/14",
            "zone": "europe-west2",
            "location": "europe-west2",
            "endpoint": "0.0.0.0",
            "initialClusterVersion": "1.12.10-gke.15",
            "currentMasterVersion": "1.14.10-gke.27",
            "status": "RUNNING",
            "servicesIpv4Cidr": "0.0.0.0/15",
            "databaseEncryption": {
                "state": "DECRYPTED",
            },
            "locations": [
                "europe-west2-c",
                "europe-west2-b",
                "europe-west2-a",
            ],
            "networkPolicy": {
                "provider": "CALICO",
                "enabled": True,
            },
            "maintenancePolicy": {
                "window": {
                    "dailyMaintenanceWindow": {
                        "startTime": "01:00",
                        "duration": "PT4H0M0S",
                    },
                },
                "resourceVersion": "111111",
            },
            "defaultMaxPodsConstraint": {
                "maxPodsPerNode": "10",
            },
            "masterAuthorizedNetworksConfig": {
                "enabled": True,
            },
            "networkConfig": {
                "network": "projects/test-cluster/global/networks/test-cluster",
                "subnetwork": "projects/test-cluster/regions/europe-west2/subnetworks/test-cluster",
            },
            "addonsConfig": {
                "httpLoadBalancing": {
                    "disabled": True,
                },
                "horizontalPodAutoscaling": {
                    "disabled": True,
                },
                "kubernetesDashboard": {
                    "disabled": True,
                },
                "networkPolicyConfig": {},
            },
            "legacyAbac": {},
            "shieldedNodes": {},
            "ipAllocationPolicy": {
                "useIpAliases": True,
                "clusterIpv4Cidr": "0.0.0.0/14",
                "servicesIpv4Cidr": "0.0.0.0/15",
                "clusterSecondaryRangeName": "pods",
                "servicesSecondaryRangeName": "services",
                "clusterIpv4CidrBlock": "0.0.0.0/14",
                "servicesIpv4CidrBlock": "0.0.0.0/15",
            },
            "privateClusterConfig": {
                "enablePrivateNodes": True,
                "enablePrivateEndpoint": True,
                "masterIpv4CidrBlock": "0.0.0.0/28",
                "privateEndpoint": "0.0.0.0",
                "publicEndpoint": "0.0.0.0",
                "peeringName": "gke-111111-1111-1111-peer",
            },
            "masterAuth": {
                "clusterCaCertificate": "11111",
            },
            "nodePools": [
                {
                    "name": "default-111-111-111-111-gke-17",
                    "config": {
                        "machineType": "n1-standard-8",
                        "diskSizeGb": 50,
                        "oauthScopes": [
                            "https://www.googleapis.com/auth/compute",
                        ],
                        "metadata": {
                            "disable-legacy-endpoints": "true",
                        },
                        "imageType": "COS",
                        "tags": ["default-node"],
                        "serviceAccount": "test-cluster-node@test-cluster.iam.gserviceaccount.com",
                        "diskType": "pd-standard",
                        "shieldedInstanceConfig": {
                            "enableIntegrityMonitoring": True,
                        },
                    },
                    "initialNodeCount": 2,
                    "management": {
                        "autoRepair": True,
                    },
                    "maxPodsConstraint": {
                        "maxPodsPerNode": "10",
                    },
                    "podIpv4CidrSize": 24,
                    "locations": [
                        "europe-west2-c",
                        "europe-west2-b",
                        "europe-west2-a",
                    ],
                    "selfLink": "https://container.googleapis.com/v1/projects/test-cluster/locations/europe-west2/clusters/test-cluster/nodePools/default-111-111-111-111-gke-17",
                    "version": "1.14.10-gke.17",
                    "instanceGroupUrls": [
                        "https://www.googleapis.com/compute/v1/projects/test-cluster/zones/europe-west2-a/instanceGroupManagers/gke-gcp-111-111-111-111-1-1-111-111",
                    ],
                    "status": "RUNNING",
                },
            ],
        },
    ],
}
