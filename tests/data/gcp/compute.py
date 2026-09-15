# flake8: noqa
VPC_RESPONSE = {
    "id": "projects/project-abc/global/networks",
    "items": [
        {
            "autoCreateSubnetworks": True,
            "creationTimestamp": "2018-05-10T17:33:18.968-07:00",
            "description": "Default network for the project",
            "id": "123456",
            "kind": "compute#network",
            "name": "default",
            "routingConfig": {
                "routingMode": "REGIONAL",
            },
            "selfLink": "https://www.googleapis.com/compute/v1/projects/project-abc/global/networks/default",
            "subnetworks": [
                "https://www.googleapis.com/compute/v1/projects/project-abc/regions/europe-west2/subnetworks/default",
                "https://www.googleapis.com/compute/v1/projects/project-abc/regions/asia-east2/subnetworks/default",
                "https://www.googleapis.com/compute/v1/projects/project-abc/regions/asia-east1/subnetworks/default",
                "https://www.googleapis.com/compute/v1/projects/project-abc/regions/us-east1/subnetworks/default",
                "https://www.googleapis.com/compute/v1/projects/project-abc/regions/northamerica-northeast1/subnetworks/default",
                "https://www.googleapis.com/compute/v1/projects/project-abc/regions/europe-west1/subnetworks/default",
                "https://www.googleapis.com/compute/v1/projects/project-abc/regions/europe-west3/subnetworks/default",
                "https://www.googleapis.com/compute/v1/projects/project-abc/regions/asia-south1/subnetworks/default",
                "https://www.googleapis.com/compute/v1/projects/project-abc/regions/europe-west4/subnetworks/default",
                "https://www.googleapis.com/compute/v1/projects/project-abc/regions/asia-southeast1/subnetworks/default",
                "https://www.googleapis.com/compute/v1/projects/project-abc/regions/us-west2/subnetworks/default",
                "https://www.googleapis.com/compute/v1/projects/project-abc/regions/us-central1/subnetworks/default",
                "https://www.googleapis.com/compute/v1/projects/project-abc/regions/asia-northeast2/subnetworks/default",
                "https://www.googleapis.com/compute/v1/projects/project-abc/regions/us-east4/subnetworks/default",
                "https://www.googleapis.com/compute/v1/projects/project-abc/regions/us-west1/subnetworks/default",
                "https://www.googleapis.com/compute/v1/projects/project-abc/regions/southamerica-east1/subnetworks/default",
                "https://www.googleapis.com/compute/v1/projects/project-abc/regions/asia-northeast1/subnetworks/default",
                "https://www.googleapis.com/compute/v1/projects/project-abc/regions/europe-west6/subnetworks/default",
                "https://www.googleapis.com/compute/v1/projects/project-abc/regions/europe-north1/subnetworks/default",
                "https://www.googleapis.com/compute/v1/projects/project-abc/regions/australia-southeast1/subnetworks/default",
            ],
        },
    ],
    "kind": "compute#networkList",
    "selfLink": "https://www.googleapis.com/compute/v1/projects/project-abc/global/networks",
}

VPC_RESPONSE_2 = {
    "id": "projects/project-def/global/networks",
    "items": [
        {
            "autoCreateSubnetworks": True,
            "creationTimestamp": "2018-05-10T17:33:18.968-07:00",
            "description": "Default network for the project",
            "id": "234567",
            "kind": "compute#network",
            "name": "default2",
            "routingConfig": {
                "routingMode": "REGIONAL",
            },
            "selfLink": "https://www.googleapis.com/compute/v1/projects/project-def/global/networks/default2",
            "subnetworks": [
                "https://www.googleapis.com/compute/v1/projects/project-def/regions/europe-west2/subnetworks/default2",
                "https://www.googleapis.com/compute/v1/projects/project-def/regions/asia-east2/subnetworks/default2",
                "https://www.googleapis.com/compute/v1/projects/project-def/regions/asia-east1/subnetworks/default2",
                "https://www.googleapis.com/compute/v1/projects/project-def/regions/us-east1/subnetworks/default2",
                "https://www.googleapis.com/compute/v1/projects/project-def/regions/northamerica-northeast1/subnetworks/default2",
                "https://www.googleapis.com/compute/v1/projects/project-def/regions/europe-west1/subnetworks/default2",
                "https://www.googleapis.com/compute/v1/projects/project-def/regions/europe-west3/subnetworks/default2",
                "https://www.googleapis.com/compute/v1/projects/project-def/regions/asia-south1/subnetworks/default2",
                "https://www.googleapis.com/compute/v1/projects/project-def/regions/europe-west4/subnetworks/default2",
                "https://www.googleapis.com/compute/v1/projects/project-def/regions/asia-southeast1/subnetworks/default2",
                "https://www.googleapis.com/compute/v1/projects/project-def/regions/us-west2/subnetworks/default2",
                "https://www.googleapis.com/compute/v1/projects/project-def/regions/us-central1/subnetworks/default2",
                "https://www.googleapis.com/compute/v1/projects/project-def/regions/asia-northeast2/subnetworks/default2",
                "https://www.googleapis.com/compute/v1/projects/project-def/regions/us-east4/subnetworks/default2",
                "https://www.googleapis.com/compute/v1/projects/project-def/regions/us-west1/subnetworks/default2",
                "https://www.googleapis.com/compute/v1/projects/project-def/regions/southamerica-east1/subnetworks/default2",
                "https://www.googleapis.com/compute/v1/projects/project-def/regions/asia-northeast1/subnetworks/default2",
                "https://www.googleapis.com/compute/v1/projects/project-def/regions/europe-west6/subnetworks/default2",
                "https://www.googleapis.com/compute/v1/projects/project-def/regions/europe-north1/subnetworks/default2",
                "https://www.googleapis.com/compute/v1/projects/project-def/regions/australia-southeast1/subnetworks/default2",
            ],
        },
    ],
    "kind": "compute#networkList",
    "selfLink": "https://www.googleapis.com/compute/v1/projects/project-def/global/networks",
}

VPC_SUBNET_RESPONSE = {
    "id": "projects/project-abc/regions/europe-west2/subnetworks",
    "items": [
        {
            "creationTimestamp": "2018-05-10T17:33:24.446-07:00",
            "fingerprint": "!@#$%ASDF",
            "gatewayAddress": "10.0.0.1",
            "id": "98765",
            "ipCidrRange": "10.0.0.0/20",
            "kind": "compute#subnetwork",
            "name": "default",
            "network": "https://www.googleapis.com/compute/v1/projects/project-abc/global/networks/default",
            "privateIpGoogleAccess": False,
            "region": "https://www.googleapis.com/compute/v1/projects/project-abc/regions/europe-west2",
            "selfLink": "https://www.googleapis.com/compute/v1/projects/project-abc/regions/europe-west2/subnetworks/default",
        },
    ],
    "kind": "compute#subnetworkList",
    "selfLink": "https://www.googleapis.com/compute/v1/projects/project-abc/regions/europe-west2/subnetworks",
}

GCP_LIST_INSTANCES_RESPONSE = {
    "id": "projects/project-abc/zones/europe-west2-b/instances",
    "items": [
        {
            "canIpForward": False,
            "cpuPlatform": "Intel Haswell",
            "creationTimestamp": "2018-02-16T10:42:04.362-08:00",
            "deletionProtection": True,
            "description": "",
            "disks": [
                {
                    "autoDelete": True,
                    "boot": True,
                    "deviceName": "instance-1",
                    "guestOsFeatures": [
                        {
                            "type": "VIRTIO_SCSI_MULTIQUEUE",
                        },
                    ],
                    "index": 0,
                    "interface": "SCSI",
                    "kind": "compute#attachedDisk",
                    "licenses": [
                        "https://www.googleapis.com/compute/v1/projects/project-that-has-license/global/licenses/ubuntu-1404-trusty",
                    ],
                    "mode": "READ_WRITE",
                    "source": "https://www.googleapis.com/compute/v1/projects/project-abc/zones/europe-west2-b/disks/instance-1",
                    "type": "PERSISTENT",
                },
            ],
            "id": "1234",
            "kind": "compute#instance",
            "labelFingerprint": "fingerprint1234=",
            "machineType": "https://www.googleapis.com/compute/v1/projects/project-abc/zones/europe-west2-b/machineTypes/n1-standard-1",
            "metadata": {
                "fingerprint": "fingerprint2345",
                "kind": "compute#metadata",
            },
            "name": "instance-1",
            "networkInterfaces": [
                {
                    "accessConfigs": [
                        {
                            "kind": "compute#accessConfig",
                            "name": "External NAT",
                            "natIP": "1.2.3.4",
                            "networkTier": "PREMIUM",
                            "type": "ONE_TO_ONE_NAT",
                        },
                    ],
                    "fingerprint": "fingerprint-3456",
                    "kind": "compute#networkInterface",
                    "name": "nic0",
                    "network": "https://www.googleapis.com/compute/v1/projects/project-abc/global/networks/default",
                    "networkIP": "10.0.0.2",
                    "subnetwork": "https://www.googleapis.com/compute/v1/projects/project-abc/regions/europe-west2/subnetworks/default",
                },
            ],
            "scheduling": {
                "automaticRestart": True,
                "onHostMaintenance": "MIGRATE",
                "preemptible": False,
            },
            "selfLink": "https://www.googleapis.com/compute/v1/projects/project-abc/zones/europe-west2-b/instances/instance-1",
            "serviceAccounts": [
                {
                    "email": "my-svc-account@developer.gserviceaccount.com",
                    "scopes": [
                        "https://www.googleapis.com/auth/devstorage.read_only",
                        "https://www.googleapis.com/auth/logging.write",
                        "https://www.googleapis.com/auth/monitoring.write",
                        "https://www.googleapis.com/auth/servicecontrol",
                        "https://www.googleapis.com/auth/service.management.readonly",
                        "https://www.googleapis.com/auth/trace.append",
                    ],
                },
            ],
            "startRestricted": False,
            "status": "RUNNING",
            "tags": {
                "fingerprint": "fingerprint3456",
                "items": ["test"],
            },
            "zone": "https://www.googleapis.com/compute/v1/projects/project-abc/zones/europe-west2-b",
        },
        {
            "canIpForward": True,
            "cpuPlatform": "Intel Haswell",
            "creationTimestamp": "2018-04-19T05:24:54.903-07:00",
            "deletionProtection": False,
            "description": "",
            "disks": [
                {
                    "autoDelete": True,
                    "boot": True,
                    "deviceName": "instance-1-test",
                    "guestOsFeatures": [
                        {
                            "type": "VIRTIO_SCSI_MULTIQUEUE",
                        },
                    ],
                    "index": 0,
                    "interface": "SCSI",
                    "kind": "compute#attachedDisk",
                    "licenses": [
                        "https://www.googleapis.com/compute/v1/projects/project-that-has-license/global/licenses/ubuntu-1404-trusty",
                    ],
                    "mode": "READ_WRITE",
                    "source": "https://www.googleapis.com/compute/v1/projects/project-abc/zones/europe-west2-b/disks/instance-1-test",
                    "type": "PERSISTENT",
                },
            ],
            "id": "2345",
            "kind": "compute#instance",
            "labelFingerprint": "fingerprint1234=",
            "machineType": "https://www.googleapis.com/compute/v1/projects/project-abc/zones/europe-west2-b/machineTypes/n1-standard-1",
            "metadata": {
                "fingerprint": "fingerprint2345",
                "kind": "compute#metadata",
            },
            "name": "instance-1-test",
            "networkInterfaces": [
                {
                    "accessConfigs": [
                        {
                            "kind": "compute#accessConfig",
                            "name": "External NAT",
                            "natIP": "1.3.4.5",
                            "networkTier": "PREMIUM",
                            "type": "ONE_TO_ONE_NAT",
                        },
                    ],
                    "fingerprint": "fingerprint4567",
                    "kind": "compute#networkInterface",
                    "name": "nic0",
                    "network": "https://www.googleapis.com/compute/v1/projects/project-abc/global/networks/default",
                    "networkIP": "10.0.0.3",
                    "subnetwork": "https://www.googleapis.com/compute/v1/projects/project-abc/regions/europe-west2/subnetworks/default",
                },
            ],
            "scheduling": {
                "automaticRestart": True,
                "onHostMaintenance": "MIGRATE",
                "preemptible": False,
            },
            "selfLink": "https://www.googleapis.com/compute/v1/projects/project-abc/zones/europe-west2-b/instances/instance-1-test",
            "serviceAccounts": [
                {
                    "email": "my-svc-account@developer.gserviceaccount.com",
                    "scopes": [
                        "https://www.googleapis.com/auth/devstorage.read_only",
                        "https://www.googleapis.com/auth/logging.write",
                        "https://www.googleapis.com/auth/monitoring.write",
                        "https://www.googleapis.com/auth/servicecontrol",
                        "https://www.googleapis.com/auth/service.management.readonly",
                        "https://www.googleapis.com/auth/trace.append",
                    ],
                },
            ],
            "startRestricted": False,
            "status": "RUNNING",
            "tags": {
                "fingerprint": "fingerprint1234=",
            },
            "zone": "https://www.googleapis.com/compute/v1/projects/project-abc/zones/europe-west2-b",
        },
    ],
    "kind": "compute#instanceList",
    "selfLink": "https://www.googleapis.com/compute/v1/projects/project-abc/zones/europe-west2-b/instances",
}

TRANSFORMED_GCP_VPCS = [
    {
        "partial_uri": "projects/project-abc/global/networks/default",
        "name": "default",
        "self_link": "https://www.googleapis.com/compute/v1/projects/project-abc/global/networks/default",
        "project_id": "project-abc",
        "auto_create_subnetworks": True,
        "description": "Default network for the project",
        "routing_config_routing_mode": "REGIONAL",
    },
]

TRANSFORMED_GCP_SUBNETS = [
    {
        "id": "projects/project-abc/regions/europe-west2/subnetworks/default",
        "partial_uri": "projects/project-abc/regions/europe-west2/subnetworks/default",
        "name": "default",
        "vpc_self_link": "https://www.googleapis.com/compute/v1/projects/project-abc/global/networks/default",
        "vpc_partial_uri": "projects/project-abc/global/networks/default",
        "project_id": "project-abc",
        "region": "europe-west2",
        "gateway_address": "10.0.0.1",
        "ip_cidr_range": "10.0.0.0/20",
        "self_link": "https://www.googleapis.com/compute/v1/projects/project-abc/regions/europe-west2/subnetworks/default",
        "private_ip_google_access": False,
    },
]

TRANSFORMED_GCP_INSTANCES = [
    {
        "canIpForward": False,
        "cpuPlatform": "Intel Haswell",
        "creationTimestamp": "2018-02-16T10:42:04.362-08:00",
        "deletionProtection": True,
        "description": "",
        "disks": [
            {
                "autoDelete": True,
                "boot": True,
                "deviceName": "instance-1",
                "guestOsFeatures": [
                    {
                        "type": "VIRTIO_SCSI_MULTIQUEUE",
                    },
                ],
                "index": 0,
                "interface": "SCSI",
                "kind": "compute#attachedDisk",
                "licenses": [
                    "https://www.googleapis.com/compute/v1/projects/project-that-has-license/global/licenses/ubuntu-1404-trusty",
                ],
                "mode": "READ_WRITE",
                "source": "https://www.googleapis.com/compute/v1/projects/project-abc/zones/europe-west2-b/disks/instance-1",
                "type": "PERSISTENT",
            },
        ],
        "id": "1234",
        "kind": "compute#instance",
        "labelFingerprint": "fingerprint1234=",
        "machineType": "https://www.googleapis.com/compute/v1/projects/project-abc/zones/europe-west2-b/machineTypes/n1-standard-1",
        "metadata": {
            "fingerprint": "fingerprint2345",
            "kind": "compute#metadata",
        },
        "name": "instance-1",
        "networkInterfaces": [
            {
                "accessConfigs": [
                    {
                        "kind": "compute#accessConfig",
                        "name": "External NAT",
                        "natIP": "1.2.3.4",
                        "networkTier": "PREMIUM",
                        "type": "ONE_TO_ONE_NAT",
                    },
                ],
                "fingerprint": "fingerprint-3456",
                "kind": "compute#networkInterface",
                "name": "nic0",
                "network": "https://www.googleapis.com/compute/v1/projects/project-abc/global/networks/default",
                "vpc_partial_uri": "projects/project-abc/global/networks/default",
                "networkIP": "10.0.0.2",
                "subnetwork": "https://www.googleapis.com/compute/v1/projects/project-abc/regions/europe-west2/subnetworks/default",
                "subnet_partial_uri": "projects/project-abc/regions/europe-west2/subnetworks/default",
            },
        ],
        "scheduling": {
            "automaticRestart": True,
            "onHostMaintenance": "MIGRATE",
            "preemptible": False,
        },
        "selfLink": "https://www.googleapis.com/compute/v1/projects/project-abc/zones/europe-west2-b/instances/instance-1",
        "serviceAccounts": [
            {
                "email": "my-svc-account@developer.gserviceaccount.com",
                "scopes": [
                    "https://www.googleapis.com/auth/devstorage.read_only",
                    "https://www.googleapis.com/auth/logging.write",
                    "https://www.googleapis.com/auth/monitoring.write",
                    "https://www.googleapis.com/auth/servicecontrol",
                    "https://www.googleapis.com/auth/service.management.readonly",
                    "https://www.googleapis.com/auth/trace.append",
                ],
            },
        ],
        "startRestricted": False,
        "status": "RUNNING",
        "tags": {
            "fingerprint": "fingerprint3456",
            "items": ["test"],
        },
        "zone": "https://www.googleapis.com/compute/v1/projects/project-abc/zones/europe-west2-b",
        "partial_uri": "projects/project-abc/zones/europe-west2-b/instances/instance-1",
        "project_id": "project-abc",
        "zone_name": "europe-west2-b",
    },
    {
        "canIpForward": True,
        "cpuPlatform": "Intel Haswell",
        "creationTimestamp": "2018-04-19T05:24:54.903-07:00",
        "deletionProtection": False,
        "description": "",
        "disks": [
            {
                "autoDelete": True,
                "boot": True,
                "deviceName": "instance-1-test",
                "guestOsFeatures": [
                    {
                        "type": "VIRTIO_SCSI_MULTIQUEUE",
                    },
                ],
                "index": 0,
                "interface": "SCSI",
                "kind": "compute#attachedDisk",
                "licenses": [
                    "https://www.googleapis.com/compute/v1/projects/project-that-has-license/global/licenses/ubuntu-1404-trusty",
                ],
                "mode": "READ_WRITE",
                "source": "https://www.googleapis.com/compute/v1/projects/project-abc/zones/europe-west2-b/disks/instance-1-test",
                "type": "PERSISTENT",
            },
        ],
        "id": "2345",
        "kind": "compute#instance",
        "labelFingerprint": "fingerprint1234=",
        "machineType": "https://www.googleapis.com/compute/v1/projects/project-abc/zones/europe-west2-b/machineTypes/n1-standard-1",
        "metadata": {
            "fingerprint": "fingerprint2345",
            "kind": "compute#metadata",
        },
        "name": "instance-1-test",
        "networkInterfaces": [
            {
                "accessConfigs": [
                    {
                        "kind": "compute#accessConfig",
                        "name": "External NAT",
                        "natIP": "1.3.4.5",
                        "networkTier": "PREMIUM",
                        "type": "ONE_TO_ONE_NAT",
                    },
                ],
                "fingerprint": "fingerprint4567",
                "kind": "compute#networkInterface",
                "name": "nic0",
                "network": "https://www.googleapis.com/compute/v1/projects/project-abc/global/networks/default",
                "vpc_partial_uri": "projects/project-abc/global/networks/default",
                "networkIP": "10.0.0.3",
                "subnetwork": "https://www.googleapis.com/compute/v1/projects/project-abc/regions/europe-west2/subnetworks/default",
                "subnet_partial_uri": "projects/project-abc/regions/europe-west2/subnetworks/default",
            },
        ],
        "scheduling": {
            "automaticRestart": True,
            "onHostMaintenance": "MIGRATE",
            "preemptible": False,
        },
        "selfLink": "https://www.googleapis.com/compute/v1/projects/project-abc/zones/europe-west2-b/instances/instance-1-test",
        "serviceAccounts": [
            {
                "email": "my-svc-account@developer.gserviceaccount.com",
                "scopes": [
                    "https://www.googleapis.com/auth/devstorage.read_only",
                    "https://www.googleapis.com/auth/logging.write",
                    "https://www.googleapis.com/auth/monitoring.write",
                    "https://www.googleapis.com/auth/servicecontrol",
                    "https://www.googleapis.com/auth/service.management.readonly",
                    "https://www.googleapis.com/auth/trace.append",
                ],
            },
        ],
        "startRestricted": False,
        "status": "RUNNING",
        "tags": {
            "fingerprint": "fingerprint1234=",
        },
        "zone": "https://www.googleapis.com/compute/v1/projects/project-abc/zones/europe-west2-b",
        "partial_uri": "projects/project-abc/zones/europe-west2-b/instances/instance-1-test",
        "project_id": "project-abc",
        "zone_name": "europe-west2-b",
    },
]

LIST_FIREWALLS_RESPONSE = {
    "id": "projects/project-abc/global/firewalls",
    "items": [
        {
            "allowed": [
                {
                    "IPProtocol": "icmp",
                },
            ],
            "creationTimestamp": "2018-05-10T17:33:45.769-07:00",
            "description": "Allow ICMP from anywhere",
            "direction": "INGRESS",
            "disabled": False,
            "id": "121212",
            "kind": "compute#firewall",
            "logConfig": {
                "enable": False,
            },
            "name": "default-allow-icmp",
            "network": "https://www.googleapis.com/compute/v1/projects/project-abc/global/networks/default",
            "priority": 65534,
            "selfLink": "https://www.googleapis.com/compute/v1/projects/project-abc/global/firewalls/default-allow-icmp",
            "sourceRanges": ["0.0.0.0/0"],
        },
        {
            "allowed": [
                {
                    "IPProtocol": "tcp",
                    "ports": ["0-65535"],
                },
                {
                    "IPProtocol": "udp",
                    "ports": ["0-65535"],
                },
                {
                    "IPProtocol": "icmp",
                },
            ],
            "creationTimestamp": "2018-05-10T17:33:45.754-07:00",
            "description": "Allow internal traffic on the default network",
            "direction": "INGRESS",
            "disabled": False,
            "id": "131313",
            "kind": "compute#firewall",
            "logConfig": {
                "enable": False,
            },
            "name": "default-allow-internal",
            "network": "https://www.googleapis.com/compute/v1/projects/project-abc/global/networks/default",
            "priority": 65534,
            "selfLink": "https://www.googleapis.com/compute/v1/projects/project-abc/global/firewalls/default-allow-internal",
            "sourceRanges": ["10.128.0.0/9"],
        },
        {
            "allowed": [
                {
                    "IPProtocol": "tcp",
                    "ports": ["3389"],
                },
            ],
            "creationTimestamp": "2018-05-10T17:33:45.764-07:00",
            "description": "Allow RDP from anywhere",
            "direction": "INGRESS",
            "disabled": False,
            "id": "141414",
            "kind": "compute#firewall",
            "logConfig": {
                "enable": False,
            },
            "name": "default-allow-rdp",
            "network": "https://www.googleapis.com/compute/v1/projects/project-abc/global/networks/default",
            "priority": 65534,
            "selfLink": "https://www.googleapis.com/compute/v1/projects/project-abc/global/firewalls/default-allow-rdp",
            "sourceRanges": ["0.0.0.0/0"],
        },
        {
            "allowed": [
                {
                    "IPProtocol": "tcp",
                    "ports": ["22"],
                },
            ],
            "creationTimestamp": "2018-05-10T17:33:45.759-07:00",
            "description": "Allow SSH from anywhere",
            "direction": "INGRESS",
            "disabled": False,
            "id": "151515",
            "kind": "compute#firewall",
            "logConfig": {
                "enable": False,
            },
            "name": "default-allow-ssh",
            "network": "https://www.googleapis.com/compute/v1/projects/project-abc/global/networks/default",
            "priority": 65534,
            "selfLink": "https://www.googleapis.com/compute/v1/projects/project-abc/global/firewalls/default-allow-ssh",
            "sourceRanges": ["0.0.0.0/0"],
        },
        {
            "allowed": [
                {
                    "IPProtocol": "tcp",
                    "ports": ["9000-9001"],
                },
            ],
            "creationTimestamp": "2019-02-08T10:03:14.422-08:00",
            "description": "",
            "direction": "INGRESS",
            "disabled": False,
            "id": "161616",
            "kind": "compute#firewall",
            "logConfig": {
                "enable": True,
            },
            "name": "custom-port-incoming",
            "network": "https://www.googleapis.com/compute/v1/projects/project-abc/global/networks/default",
            "priority": 1000,
            "selfLink": "https://www.googleapis.com/compute/v1/projects/project-abc/global/firewalls/custom-port-incoming",
            "sourceRanges": ["0.0.0.0/0"],
            "targetTags": ["test"],
        },
    ],
    "kind": "compute#firewallList",
    "selfLink": "https://www.googleapis.com/compute/v1/projects/project-abc/global/firewalls",
}

TRANSFORMED_FW_LIST = [
    {
        "allowed": [
            {
                "IPProtocol": "icmp",
            },
        ],
        "creationTimestamp": "2018-05-10T17:33:45.769-07:00",
        "description": "Allow ICMP from anywhere",
        "direction": "INGRESS",
        "disabled": False,
        "id": "projects/project-abc/global/firewalls/default-allow-icmp",
        "kind": "compute#firewall",
        "logConfig": {
            "enable": False,
        },
        "name": "default-allow-icmp",
        "network": "https://www.googleapis.com/compute/v1/projects/project-abc/global/networks/default",
        "priority": 65534,
        "selfLink": "https://www.googleapis.com/compute/v1/projects/project-abc/global/firewalls/default-allow-icmp",
        "sourceRanges": ["0.0.0.0/0"],
        "transformed_allow_list": [
            {
                "fromport": None,
                "protocol": "icmp",
                "ruleid": "projects/project-abc/global/firewalls/default-allow-icmp/allow/icmp",
                "toport": None,
            },
        ],
        "transformed_deny_list": [],
        "vpc_partial_uri": "projects/project-abc/global/networks/default",
        "has_target_service_accounts": False,
    },
    {
        "allowed": [
            {
                "IPProtocol": "tcp",
                "ports": ["0-65535"],
            },
            {
                "IPProtocol": "udp",
                "ports": ["0-65535"],
            },
            {
                "IPProtocol": "icmp",
            },
        ],
        "creationTimestamp": "2018-05-10T17:33:45.754-07:00",
        "description": "Allow internal traffic on the default network",
        "direction": "INGRESS",
        "disabled": False,
        "id": "projects/project-abc/global/firewalls/default-allow-internal",
        "kind": "compute#firewall",
        "logConfig": {
            "enable": False,
        },
        "name": "default-allow-internal",
        "network": "https://www.googleapis.com/compute/v1/projects/project-abc/global/networks/default",
        "priority": 65534,
        "selfLink": "https://www.googleapis.com/compute/v1/projects/project-abc/global/firewalls/default-allow-internal",
        "sourceRanges": ["10.128.0.0/9"],
        "transformed_allow_list": [
            {
                "fromport": 0,
                "protocol": "tcp",
                "ruleid": "projects/project-abc/global/firewalls/default-allow-internal/allow/0to65535tcp",
                "toport": 65535,
            },
            {
                "fromport": 0,
                "protocol": "udp",
                "ruleid": "projects/project-abc/global/firewalls/default-allow-internal/allow/0to65535udp",
                "toport": 65535,
            },
            {
                "fromport": None,
                "protocol": "icmp",
                "ruleid": "projects/project-abc/global/firewalls/default-allow-internal/allow/icmp",
                "toport": None,
            },
        ],
        "transformed_deny_list": [],
        "vpc_partial_uri": "projects/project-abc/global/networks/default",
        "has_target_service_accounts": False,
    },
    {
        "allowed": [
            {
                "IPProtocol": "tcp",
                "ports": ["3389"],
            },
        ],
        "creationTimestamp": "2018-05-10T17:33:45.764-07:00",
        "description": "Allow RDP from anywhere",
        "direction": "INGRESS",
        "disabled": False,
        "id": "projects/project-abc/global/firewalls/default-allow-rdp",
        "kind": "compute#firewall",
        "logConfig": {
            "enable": False,
        },
        "name": "default-allow-rdp",
        "network": "https://www.googleapis.com/compute/v1/projects/project-abc/global/networks/default",
        "priority": 65534,
        "selfLink": "https://www.googleapis.com/compute/v1/projects/project-abc/global/firewalls/default-allow-rdp",
        "sourceRanges": ["0.0.0.0/0"],
        "transformed_allow_list": [
            {
                "fromport": 3389,
                "protocol": "tcp",
                "ruleid": "projects/project-abc/global/firewalls/default-allow-rdp/allow/3389tcp",
                "toport": 3389,
            },
        ],
        "transformed_deny_list": [],
        "vpc_partial_uri": "projects/project-abc/global/networks/default",
        "has_target_service_accounts": False,
    },
    {
        "allowed": [
            {
                "IPProtocol": "tcp",
                "ports": ["22"],
            },
        ],
        "creationTimestamp": "2018-05-10T17:33:45.759-07:00",
        "description": "Allow SSH from anywhere",
        "direction": "INGRESS",
        "disabled": False,
        "id": "projects/project-abc/global/firewalls/default-allow-ssh",
        "kind": "compute#firewall",
        "logConfig": {
            "enable": False,
        },
        "name": "default-allow-ssh",
        "network": "https://www.googleapis.com/compute/v1/projects/project-abc/global/networks/default",
        "priority": 65534,
        "selfLink": "https://www.googleapis.com/compute/v1/projects/project-abc/global/firewalls/default-allow-ssh",
        "sourceRanges": ["0.0.0.0/0"],
        "transformed_allow_list": [
            {
                "fromport": 22,
                "protocol": "tcp",
                "ruleid": "projects/project-abc/global/firewalls/default-allow-ssh/allow/22tcp",
                "toport": 22,
            },
        ],
        "transformed_deny_list": [],
        "vpc_partial_uri": "projects/project-abc/global/networks/default",
        "has_target_service_accounts": False,
    },
    {
        "allowed": [
            {
                "IPProtocol": "tcp",
                "ports": ["9000-9001"],
            },
        ],
        "creationTimestamp": "2019-02-08T10:03:14.422-08:00",
        "description": "",
        "direction": "INGRESS",
        "disabled": False,
        "id": "projects/project-abc/global/firewalls/custom-port-incoming",
        "kind": "compute#firewall",
        "logConfig": {
            "enable": True,
        },
        "name": "custom-port-incoming",
        "network": "https://www.googleapis.com/compute/v1/projects/project-abc/global/networks/default",
        "priority": 1000,
        "selfLink": "https://www.googleapis.com/compute/v1/projects/project-abc/global/firewalls/custom-port-incoming",
        "sourceRanges": ["0.0.0.0/0"],
        "targetTags": ["test"],
        "transformed_allow_list": [
            {
                "fromport": 9000,
                "protocol": "tcp",
                "ruleid": "projects/project-abc/global/firewalls/custom-port-incoming/allow/9000to9001tcp",
                "toport": 9001,
            },
        ],
        "transformed_deny_list": [],
        "vpc_partial_uri": "projects/project-abc/global/networks/default",
        "has_target_service_accounts": False,
    },
]

LIST_FORWARDING_RULES_RESPONSE = {
    "id": "projects/project-abc/regions/europe-west2/forwardingRules",
    "items": [
        {
            "id": "11111111",
            "creationTimestamp": "2019-11-22T06:05:37.254-08:00",
            "name": "internal-service-1111",
            "description": "my-k8s-internal-service",
            "region": "https://www.googleapis.com/compute/v1/projects/project-abc/regions/europe-west2",
            "IPAddress": "10.0.0.10",
            "IPProtocol": "TCP",
            "ports": [
                "80",
            ],
            "selfLink": "https://www.googleapis.com/compute/v1/projects/project-abc/regions/europe-west2/forwardingRules/internal-service-1111",
            "loadBalancingScheme": "INTERNAL",
            "subnetwork": "https://www.googleapis.com/compute/v1/projects/project-abc/regions/europe-west2/subnetworks/default",
            "network": "https://www.googleapis.com/compute/v1/projects/project-abc/global/networks/default",
            "backendService": "https://www.googleapis.com/compute/v1/projects/project-abc/regions/europe-west2/backendServices/backend-service-1111",
            "networkTier": "PREMIUM",
            "target": "https://www.googleapis.com/compute/v1/projects/project-abc/regions/europe-west2/targetPools/node-pool-12345",
            "fingerprint": "12345678",
            "kind": "compute#forwardingRule",
        },
        {
            "id": "12121212",
            "creationTimestamp": "2019-03-30T14:02:47.050-07:00",
            "name": "public-ingress-controller-1234567",
            "description": "ingress-controller",
            "region": "https://www.googleapis.com/compute/v1/projects/project-abc/regions/europe-west2",
            "IPAddress": "1.2.3.11",
            "IPProtocol": "TCP",
            "portRange": "80-443",
            "target": "https://www.googleapis.com/compute/v1/projects/project-abc/regions/europe-west2/targetPools/node-pool-12345",
            "selfLink": "https://www.googleapis.com/compute/v1/projects/project-abc/regions/europe-west2/forwardingRules/public-ingress-controller-1234567",
            "loadBalancingScheme": "EXTERNAL",
            "networkTier": "PREMIUM",
            "target": "https://www.googleapis.com/compute/v1/projects/project-abc/regions/europe-west2/targetVpnGateways/vpn-12345",
            "fingerprint": "123456789",
            "kind": "compute#forwardingRule",
        },
        {
            "id": "13131313",
            "creationTimestamp": "2020-08-12T03:18:41.743-07:00",
            "name": "shard-server-22222",
            "description": "shard-server",
            "region": "https://www.googleapis.com/compute/v1/projects/project-abc/regions/europe-west2",
            "IPAddress": "10.0.0.20",
            "IPProtocol": "TCP",
            "ports": [
                "10203",
            ],
            "selfLink": "https://www.googleapis.com/compute/v1/projects/project-abc/regions/europe-west2/forwardingRules/shard-server-22222",
            "loadBalancingScheme": "INTERNAL",
            "subnetwork": "https://www.googleapis.com/compute/v1/projects/project-abc/regions/europe-west2/subnetworks/default",
            "network": "https://www.googleapis.com/compute/v1/projects/project-abc/global/networks/default",
            "backendService": "https://www.googleapis.com/compute/v1/projects/project-abc/regions/europe-west1/backendServices/backend-service-111234",
            "networkTier": "PREMIUM",
            "target": "https://www.googleapis.com/compute/v1/projects/project-abc/regions/europe-west2/targetPools/node-pool-234567",
            "fingerprint": "1234567",
            "kind": "compute#forwardingRule",
        },
        {
            # Internal regional LB: backend service only, no `target` — exercises
            # the lb_type fallback path.
            "id": "14141414",
            "creationTimestamp": "2021-06-01T09:00:00.000-07:00",
            "name": "internal-tcp-no-target-3333",
            "region": "https://www.googleapis.com/compute/v1/projects/project-abc/regions/europe-west2",
            "IPAddress": "10.0.0.30",
            "IPProtocol": "TCP",
            "ports": ["8080"],
            "selfLink": "https://www.googleapis.com/compute/v1/projects/project-abc/regions/europe-west2/forwardingRules/internal-tcp-no-target-3333",
            "loadBalancingScheme": "INTERNAL",
            "subnetwork": "https://www.googleapis.com/compute/v1/projects/project-abc/regions/europe-west2/subnetworks/default",
            "network": "https://www.googleapis.com/compute/v1/projects/project-abc/global/networks/default",
            "backendService": "https://www.googleapis.com/compute/v1/projects/project-abc/regions/europe-west2/backendServices/backend-service-3333",
            "networkTier": "PREMIUM",
            "fingerprint": "33333333",
            "kind": "compute#forwardingRule",
        },
    ],
    "selfLink": "https://www.googleapis.com/compute/v1/projects/project-abc/regions/europe-west4/forwardingRules",
    "kind": "compute#forwardingRuleList",
}

LIST_GLOBAL_FORWARDING_RULES_RESPONSE = {
    "id": "projects/project-abc/global/forwardingRules",
    "items": [
        {
            "id": "99999999",
            "creationTimestamp": "2019-11-22T06:05:37.254-08:00",
            "name": "global-rule-1",
            "description": "global forwarding rule",
            "IPAddress": "35.235.1.2",
            "IPProtocol": "TCP",
            "selfLink": "https://www.googleapis.com/compute/v1/projects/project-abc/global/forwardingRules/global-rule-1",
            "loadBalancingScheme": "EXTERNAL",
            "network": "https://www.googleapis.com/compute/v1/projects/project-abc/global/networks/default",
            "target": "https://www.googleapis.com/compute/v1/projects/project-abc/global/targetHttpsProxies/proxy-1",
            "kind": "compute#forwardingRule",
        },
    ],
    "selfLink": "https://www.googleapis.com/compute/v1/projects/project-abc/global/forwardingRules",
    "kind": "compute#forwardingRuleList",
}

# VPC response for project-abc containing two peerings on network vpc-a:
# - peering-a-to-b: peer network lives in project-def (synced in some tests)
# - peering-a-to-ext: peer network lives in project-xyz (never synced -> stub)
VPC_PEERING_RESPONSE = {
    "id": "projects/project-abc/global/networks",
    "items": [
        {
            "autoCreateSubnetworks": False,
            "creationTimestamp": "2024-01-10T10:00:00.000-08:00",
            "description": "Peered network in project-abc",
            "id": "345678",
            "kind": "compute#network",
            "name": "vpc-a",
            "routingConfig": {
                "routingMode": "GLOBAL",
            },
            "selfLink": "https://www.googleapis.com/compute/v1/projects/project-abc/global/networks/vpc-a",
            "peerings": [
                {
                    "name": "peering-a-to-b",
                    "network": "https://www.googleapis.com/compute/v1/projects/project-abc/global/networks/vpc-a",
                    "peerNetwork": "https://www.googleapis.com/compute/v1/projects/project-def/global/networks/vpc-b",
                    "state": "ACTIVE",
                    "stateDetails": "[2024-01-10T10:05:00]: Connected.",
                    "peerMtu": 1460,
                    "stackType": "IPV4_ONLY",
                    "updateStrategy": "CONSERVATIVE",
                    "autoCreateRoutes": True,
                    "exchangeSubnetRoutes": True,
                    "importCustomRoutes": False,
                    "exportCustomRoutes": True,
                    "importSubnetRoutesWithPublicIp": False,
                    "exportSubnetRoutesWithPublicIp": False,
                },
                {
                    "name": "peering-a-to-ext",
                    "network": "https://www.googleapis.com/compute/v1/projects/project-abc/global/networks/vpc-a",
                    "peerNetwork": "https://www.googleapis.com/compute/v1/projects/project-xyz/global/networks/vpc-ext",
                    "state": "INACTIVE",
                    "stateDetails": "[2024-01-11T09:00:00]: Waiting for peer network to connect.",
                    "peerMtu": 1460,
                    "stackType": "IPV4_ONLY",
                    "updateStrategy": "CONSERVATIVE",
                    "autoCreateRoutes": True,
                    "exchangeSubnetRoutes": True,
                    "importCustomRoutes": True,
                    "exportCustomRoutes": False,
                    "importSubnetRoutesWithPublicIp": False,
                    "exportSubnetRoutesWithPublicIp": False,
                },
            ],
        },
    ],
    "kind": "compute#networkList",
    "selfLink": "https://www.googleapis.com/compute/v1/projects/project-abc/global/networks",
}

# The other side of peering-a-to-b, as reported by project-def's networks.list.
VPC_PEERING_PEER_RESPONSE = {
    "id": "projects/project-def/global/networks",
    "items": [
        {
            "autoCreateSubnetworks": False,
            "creationTimestamp": "2024-01-10T10:01:00.000-08:00",
            "description": "Peered network in project-def",
            "id": "456789",
            "kind": "compute#network",
            "name": "vpc-b",
            "routingConfig": {
                "routingMode": "GLOBAL",
            },
            "selfLink": "https://www.googleapis.com/compute/v1/projects/project-def/global/networks/vpc-b",
            "peerings": [
                {
                    "name": "peering-b-to-a",
                    "network": "https://www.googleapis.com/compute/v1/projects/project-def/global/networks/vpc-b",
                    "peerNetwork": "https://www.googleapis.com/compute/v1/projects/project-abc/global/networks/vpc-a",
                    "state": "ACTIVE",
                    "stateDetails": "[2024-01-10T10:05:00]: Connected.",
                    "peerMtu": 1460,
                    "stackType": "IPV4_ONLY",
                    "updateStrategy": "CONSERVATIVE",
                    "autoCreateRoutes": True,
                    "exchangeSubnetRoutes": True,
                    "importCustomRoutes": True,
                    "exportCustomRoutes": False,
                    "importSubnetRoutesWithPublicIp": False,
                    "exportSubnetRoutesWithPublicIp": False,
                },
            ],
        },
    ],
    "kind": "compute#networkList",
    "selfLink": "https://www.googleapis.com/compute/v1/projects/project-def/global/networks",
}

# Same project/network as VPC_PEERING_RESPONSE but with all peerings removed
# (used for stale-peering cleanup tests).
VPC_PEERING_RESPONSE_NO_PEERINGS = {
    "id": "projects/project-abc/global/networks",
    "items": [
        {
            "autoCreateSubnetworks": False,
            "creationTimestamp": "2024-01-10T10:00:00.000-08:00",
            "description": "Peered network in project-abc",
            "id": "345678",
            "kind": "compute#network",
            "name": "vpc-a",
            "routingConfig": {
                "routingMode": "GLOBAL",
            },
            "selfLink": "https://www.googleapis.com/compute/v1/projects/project-abc/global/networks/vpc-a",
        },
    ],
    "kind": "compute#networkList",
    "selfLink": "https://www.googleapis.com/compute/v1/projects/project-abc/global/networks",
}

VPN_GATEWAYS_RESPONSE = {
    "id": "projects/project-abc/regions/us-central1/vpnGateways",
    "items": [
        {
            "creationTimestamp": "2024-02-01T08:00:00.000-08:00",
            "description": "HA VPN gateway in project-abc",
            "id": "111222333",
            "kind": "compute#vpnGateway",
            "name": "gw-a",
            "network": "https://www.googleapis.com/compute/v1/projects/project-abc/global/networks/vpc-a",
            "region": "https://www.googleapis.com/compute/v1/projects/project-abc/regions/us-central1",
            "selfLink": "https://www.googleapis.com/compute/v1/projects/project-abc/regions/us-central1/vpnGateways/gw-a",
            "stackType": "IPV4_ONLY",
            "gatewayIpVersion": "IPV4",
            "vpnInterfaces": [
                {
                    "id": 0,
                    "ipAddress": "203.0.113.10",
                    "interconnectAttachment": None,
                },
                {
                    "id": 1,
                    "ipAddress": "203.0.113.11",
                    "interconnectAttachment": None,
                },
            ],
        },
    ],
    "kind": "compute#vpnGatewayList",
    "selfLink": "https://www.googleapis.com/compute/v1/projects/project-abc/regions/us-central1/vpnGateways",
}

# project-abc's tunnels: one HA tunnel to project-def's gw-b, one HA tunnel to
# project-xyz's gw-ext (never synced -> stub), and one classic tunnel with no
# vpnGateway. Includes sharedSecret to prove it is never ingested.
VPN_TUNNELS_RESPONSE = {
    "id": "projects/project-abc/regions/us-central1/vpnTunnels",
    "items": [
        {
            "creationTimestamp": "2024-02-01T08:05:00.000-08:00",
            "description": "HA VPN tunnel to project-def",
            "detailedStatus": "Tunnel is up and running.",
            "id": "222333444",
            "ikeVersion": 2,
            "kind": "compute#vpnTunnel",
            "localTrafficSelector": ["0.0.0.0/0"],
            "remoteTrafficSelector": ["0.0.0.0/0"],
            "name": "tunnel-a-to-b",
            "peerGcpGateway": "https://www.googleapis.com/compute/v1/projects/project-def/regions/us-central1/vpnGateways/gw-b",
            "region": "https://www.googleapis.com/compute/v1/projects/project-abc/regions/us-central1",
            "selfLink": "https://www.googleapis.com/compute/v1/projects/project-abc/regions/us-central1/vpnTunnels/tunnel-a-to-b",
            "sharedSecret": "mock-psk-do-not-ingest",
            "sharedSecretHash": "HASHED:abc123",
            "status": "ESTABLISHED",
            "vpnGateway": "https://www.googleapis.com/compute/v1/projects/project-abc/regions/us-central1/vpnGateways/gw-a",
            "vpnGatewayInterface": 0,
        },
        {
            "creationTimestamp": "2024-02-01T08:06:00.000-08:00",
            "description": "HA VPN tunnel to project-xyz",
            "detailedStatus": "Tunnel is up and running.",
            "id": "333444555",
            "ikeVersion": 2,
            "kind": "compute#vpnTunnel",
            "localTrafficSelector": ["10.0.0.0/8"],
            "remoteTrafficSelector": ["172.16.0.0/12"],
            "name": "tunnel-a-to-ext",
            "peerGcpGateway": "https://www.googleapis.com/compute/v1/projects/project-xyz/regions/us-central1/vpnGateways/gw-ext",
            "region": "https://www.googleapis.com/compute/v1/projects/project-abc/regions/us-central1",
            "selfLink": "https://www.googleapis.com/compute/v1/projects/project-abc/regions/us-central1/vpnTunnels/tunnel-a-to-ext",
            "sharedSecret": "mock-psk-do-not-ingest-2",
            "sharedSecretHash": "HASHED:def456",
            "status": "ESTABLISHED",
            "vpnGateway": "https://www.googleapis.com/compute/v1/projects/project-abc/regions/us-central1/vpnGateways/gw-a",
            "vpnGatewayInterface": 1,
        },
        {
            "creationTimestamp": "2024-02-01T08:07:00.000-08:00",
            "description": "Classic VPN tunnel to on-prem",
            "detailedStatus": "Tunnel is up and running.",
            "id": "444555666",
            "ikeVersion": 2,
            "kind": "compute#vpnTunnel",
            "localTrafficSelector": ["0.0.0.0/0"],
            "remoteTrafficSelector": ["0.0.0.0/0"],
            "name": "tunnel-classic",
            "peerIp": "198.51.100.1",
            "region": "https://www.googleapis.com/compute/v1/projects/project-abc/regions/us-central1",
            "router": "https://www.googleapis.com/compute/v1/projects/project-abc/regions/us-central1/routers/router-a",
            "selfLink": "https://www.googleapis.com/compute/v1/projects/project-abc/regions/us-central1/vpnTunnels/tunnel-classic",
            "sharedSecret": "mock-psk-do-not-ingest-3",
            "sharedSecretHash": "HASHED:ghi789",
            "status": "ESTABLISHED",
            "targetVpnGateway": "https://www.googleapis.com/compute/v1/projects/project-abc/regions/us-central1/targetVpnGateways/classic-gw",
        },
    ],
    "kind": "compute#vpnTunnelList",
    "selfLink": "https://www.googleapis.com/compute/v1/projects/project-abc/regions/us-central1/vpnTunnels",
}

# project-def's side of the HA VPN: gateway gw-b and tunnel back to gw-a.
VPN_GATEWAYS_PEER_RESPONSE = {
    "id": "projects/project-def/regions/us-central1/vpnGateways",
    "items": [
        {
            "creationTimestamp": "2024-02-01T08:01:00.000-08:00",
            "description": "HA VPN gateway in project-def",
            "id": "555666777",
            "kind": "compute#vpnGateway",
            "name": "gw-b",
            "network": "https://www.googleapis.com/compute/v1/projects/project-def/global/networks/vpc-b",
            "region": "https://www.googleapis.com/compute/v1/projects/project-def/regions/us-central1",
            "selfLink": "https://www.googleapis.com/compute/v1/projects/project-def/regions/us-central1/vpnGateways/gw-b",
            "stackType": "IPV4_ONLY",
            "gatewayIpVersion": "IPV4",
            "vpnInterfaces": [
                {
                    "id": 0,
                    "ipAddress": "203.0.113.20",
                    "interconnectAttachment": None,
                },
            ],
        },
    ],
    "kind": "compute#vpnGatewayList",
    "selfLink": "https://www.googleapis.com/compute/v1/projects/project-def/regions/us-central1/vpnGateways",
}

VPN_TUNNELS_PEER_RESPONSE = {
    "id": "projects/project-def/regions/us-central1/vpnTunnels",
    "items": [
        {
            "creationTimestamp": "2024-02-01T08:08:00.000-08:00",
            "description": "HA VPN tunnel to project-abc",
            "detailedStatus": "Tunnel is up and running.",
            "id": "666777888",
            "ikeVersion": 2,
            "kind": "compute#vpnTunnel",
            "localTrafficSelector": ["0.0.0.0/0"],
            "remoteTrafficSelector": ["0.0.0.0/0"],
            "name": "tunnel-b-to-a",
            "peerGcpGateway": "https://www.googleapis.com/compute/v1/projects/project-abc/regions/us-central1/vpnGateways/gw-a",
            "region": "https://www.googleapis.com/compute/v1/projects/project-def/regions/us-central1",
            "selfLink": "https://www.googleapis.com/compute/v1/projects/project-def/regions/us-central1/vpnTunnels/tunnel-b-to-a",
            "sharedSecret": "mock-psk-do-not-ingest-4",
            "sharedSecretHash": "HASHED:jkl012",
            "status": "ESTABLISHED",
            "vpnGateway": "https://www.googleapis.com/compute/v1/projects/project-def/regions/us-central1/vpnGateways/gw-b",
            "vpnGatewayInterface": 0,
        },
    ],
    "kind": "compute#vpnTunnelList",
    "selfLink": "https://www.googleapis.com/compute/v1/projects/project-def/regions/us-central1/vpnTunnels",
}

# Empty regional responses (used for cleanup tests).
VPN_GATEWAYS_RESPONSE_EMPTY = {
    "id": "projects/project-abc/regions/us-central1/vpnGateways",
    "kind": "compute#vpnGatewayList",
    "selfLink": "https://www.googleapis.com/compute/v1/projects/project-abc/regions/us-central1/vpnGateways",
}

VPN_TUNNELS_RESPONSE_EMPTY = {
    "id": "projects/project-abc/regions/us-central1/vpnTunnels",
    "kind": "compute#vpnTunnelList",
    "selfLink": "https://www.googleapis.com/compute/v1/projects/project-abc/regions/us-central1/vpnTunnels",
}
