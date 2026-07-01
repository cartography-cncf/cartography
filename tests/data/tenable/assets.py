TENABLE_TENANT_ID = "cloud.tenable.com"

ASSET_ID_1 = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
ASSET_ID_2 = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"

NETWORK_ID = "00000000-0000-0000-0000-000000000000"

TAG_ID_1 = "cccccccc-cccc-cccc-cccc-cccccccccccc"

AWS_EC2_INSTANCE_ID_1 = "i-1234567890abcdef0"
AZURE_VM_ID_2 = "dddddddd-dddd-dddd-dddd-dddddddddddd"

ASSETS_DATA = [
    {
        # AWS EC2 host with agent
        "id": ASSET_ID_1,
        "has_agent": True,
        "has_plugin_results": True,
        "is_licensed": True,
        "is_public": False,
        "types": ["host", "cloud"],
        "system_types": ["aws-ec2-instance"],
        "operating_systems": ["Oracle Linux 8.4"],
        "serial_number": None,
        "tenable_agent_days_since_active": 2,
        "timestamps": {
            "created_at": "2024-09-24T15:01:25.000Z",
            "updated_at": "2024-12-16T09:45:50.000Z",
            "first_seen": "2024-09-24T15:01:25.000Z",
            "last_seen": "2024-12-16T09:45:50.000Z",
        },
        "scan": {
            "first_scan_time": "2024-09-24T15:01:25.000Z",
            "last_scan_time": "2024-12-16T09:45:50.000Z",
            "last_authenticated_scan_date": "2024-11-09T22:22:44.735Z",
            "last_licensed_scan_date": "2024-12-16T09:45:50.000Z",
            "last_scan_id": "scan-id-1",
        },
        "cloud": {
            "aws": {
                "ec2_instance_id": "i-1234567890abcdef0",
                "ec2_instance_ami_id": "ami-0abcdef1234567890",
                "owner_id": "123456789012",
                "availability_zone": "us-east-1a",
                "region": "us-east-1",
                "vpc_id": "vpc-12345678",
                "subnet_id": "subnet-12345678",
                "ec2_instance_type": "t3.medium",
                "ec2_instance_state_name": "running",
                "ec2_instance_group_name": "launch-wizard-1",
                "ec2_name": "test-server-1",
            }
        },
        "network": {
            "network_id": "00000000-0000-0000-0000-000000000000",
            "network_name": "Default",
            "ipv4s": ["192.168.1.10", "172.26.114.163"],
            "ipv6s": [],
            "fqdns": ["server1.example.com"],
            "hostnames": ["server1"],
            "mac_addresses": ["00:11:22:33:44:55"],
        },
        "ratings": {
            "acr": {"score": 5},
            "aes": {"score": 600},
        },
        "sources": [
            {
                "name": "NESSUS_AGENT",
                "first_seen": "2024-09-24T15:01:25.000Z",
                "last_seen": "2024-12-16T09:45:50.000Z",
            }
        ],
        "tags": [
            {
                "uuid": TAG_ID_1,
                "key": "Environment",
                "value": "Production",
                "added_by": "admin@example.com",
                "added_at": "2024-10-01T00:00:00.000Z",
            }
        ],
    },
    {
        # Webapp asset (no agent, no cloud)
        "id": ASSET_ID_2,
        "has_agent": False,
        "has_plugin_results": True,
        "is_licensed": True,
        "is_public": True,
        "types": ["webapp"],
        "system_types": [],
        "operating_systems": ["Windows Server 2019"],
        "serial_number": "ABCDEFG",
        "tenable_agent_days_since_active": None,
        "timestamps": {
            "created_at": "2024-05-09T10:31:04.817Z",
            "updated_at": "2024-07-02T18:41:24.423Z",
            "first_seen": "2022-10-20T09:32:46.000Z",
            "last_seen": "2022-10-20T11:08:51.000Z",
        },
        "scan": {
            "first_scan_time": "2017-12-31T20:40:23.447Z",
            "last_scan_time": "2024-07-02T12:51:10.918Z",
            "last_authenticated_scan_date": None,
            "last_licensed_scan_date": "2024-07-02T12:51:10.918Z",
            "last_scan_id": "scan-id-2",
        },
        "cloud": {
            "azure": {
                "vm_id": AZURE_VM_ID_2,
                "resource_id": "/subscriptions/sub-123/resourceGroups/rg-prod/providers/Microsoft.Compute/virtualMachines/test-vm",
            }
        },
        "network": {
            "network_id": "00000000-0000-0000-0000-000000000000",
            "network_name": "Default",
            "ipv4s": ["10.0.0.20"],
            "ipv6s": ["2001:db8::1"],
            "fqdns": ["server2.example.com"],
            "hostnames": ["server2"],
            "mac_addresses": ["aa:bb:cc:dd:ee:ff"],
        },
        "ratings": {
            "acr": {"score": 7},
            "aes": {"score": 800},
        },
        "sources": [
            {
                "name": "NESSUS_SCAN",
                "first_seen": "2022-10-20T09:32:46.000Z",
                "last_seen": "2022-10-20T11:08:51.000Z",
            }
        ],
        "tags": [],
    },
]
