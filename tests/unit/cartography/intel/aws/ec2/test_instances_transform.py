from cartography.intel.aws.ec2.instances import transform_ec2_instances
from tests.data.aws.ec2.instances import INSTANCE_WITH_IAM_PROFILE
from tests.data.aws.ec2.instances_missing_private_ip import (
    DESCRIBE_INSTANCES_MISSING_PRIVATE_IP,
)

FAKE_REGION = "us-east-1"
FAKE_ACCOUNT_ID = "123456789012"


def _make_reservation(instance_id, network_interfaces, block_device_mappings=None):
    """Helper: build a minimal DescribeInstances reservation dict."""
    return {
        "ReservationId": "r-1",
        "OwnerId": FAKE_ACCOUNT_ID,
        "Instances": [
            {
                "InstanceId": instance_id,
                "NetworkInterfaces": network_interfaces,
                "BlockDeviceMappings": block_device_mappings or [],
            }
        ],
    }


def test_transform_ec2_instances_handles_missing_private_ip():
    reservations = DESCRIBE_INSTANCES_MISSING_PRIVATE_IP["Reservations"]
    data = transform_ec2_instances(reservations, FAKE_REGION, FAKE_ACCOUNT_ID)

    assert data.network_interface_list == [
        {
            "NetworkInterfaceId": "eni-1",
            "Status": "in-use",
            "MacAddress": "00:00:00:00:00:00",
            "Description": "",
            "PrivateDnsName": None,
            "PrivateIpAddress": None,
            "InstanceId": "i-missing",
            "SubnetId": None,
            "GroupId": "sg-1",
        }
    ]


def test_transform_ec2_instances_extracts_eks_cluster_tag():
    reservations = [
        {
            "ReservationId": "r-1",
            "OwnerId": FAKE_ACCOUNT_ID,
            "Instances": [
                {
                    "InstanceId": "i-eks",
                    "NetworkInterfaces": [],
                    "BlockDeviceMappings": [],
                    "Tags": [
                        {"Key": "eks:cluster-name", "Value": "prod-cluster"},
                    ],
                },
            ],
        },
    ]

    data = transform_ec2_instances(reservations, FAKE_REGION, FAKE_ACCOUNT_ID)

    assert data.instance_list[0]["EksClusterName"] == "prod-cluster"


# --- IPv6 extraction tests ---


def test_transform_ipv6_single_address():
    """Instance with one IPv6 on primary NI (DeviceIndex=0) produces one record."""
    reservations = [
        _make_reservation(
            "i-1",
            [
                {
                    "NetworkInterfaceId": "eni-1",
                    "Status": "in-use",
                    "MacAddress": "00:00:00:00:00:01",
                    "Description": "",
                    "Groups": [],
                    "Attachment": {"DeviceIndex": 0},
                    "Ipv6Addresses": [
                        {"Ipv6Address": "2001:db8::1", "IsPrimaryIpv6": True}
                    ],
                }
            ],
        )
    ]

    data = transform_ec2_instances(reservations, FAKE_REGION, FAKE_ACCOUNT_ID)

    assert data.ipv6_address_list == [
        {
            "Ipv6Address": "2001:db8::1",
            "NetworkInterfaceId": "eni-1",
            "IsPrimaryIpv6": True,
        }
    ]
    # Instance-level field should be populated from the primary NI.
    assert data.instance_list[0]["IPv6Address"] == "2001:db8::1"


def test_transform_ipv6_no_ipv6():
    """Instance with no IPv6 addresses produces empty list and None on instance."""
    reservations = [
        _make_reservation(
            "i-2",
            [
                {
                    "NetworkInterfaceId": "eni-2",
                    "Status": "in-use",
                    "MacAddress": "00:00:00:00:00:02",
                    "Description": "",
                    "Groups": [],
                    "Attachment": {"DeviceIndex": 0},
                    "Ipv6Addresses": [],
                }
            ],
        )
    ]

    data = transform_ec2_instances(reservations, FAKE_REGION, FAKE_ACCOUNT_ID)

    assert data.ipv6_address_list == []
    assert data.instance_list[0]["IPv6Address"] is None


def test_transform_ipv6_no_network_interfaces():
    """Instance with no network interfaces at all — ipv6_address_list is empty."""
    reservations = [_make_reservation("i-3", [])]

    data = transform_ec2_instances(reservations, FAKE_REGION, FAKE_ACCOUNT_ID)

    assert data.ipv6_address_list == []
    assert data.instance_list[0]["IPv6Address"] is None


def test_transform_ipv6_multiple_nics_multiple_addresses():
    """Multiple NICs each with multiple IPv6 addresses all appear in ipv6_address_list."""
    reservations = [
        _make_reservation(
            "i-4",
            [
                {
                    "NetworkInterfaceId": "eni-10",
                    "Status": "in-use",
                    "MacAddress": "00:00:00:00:00:10",
                    "Description": "",
                    "Groups": [],
                    "Attachment": {"DeviceIndex": 0},
                    "Ipv6Addresses": [
                        {"Ipv6Address": "2001:db8::a", "IsPrimaryIpv6": True},
                        {"Ipv6Address": "2001:db8::b", "IsPrimaryIpv6": False},
                    ],
                },
                {
                    "NetworkInterfaceId": "eni-11",
                    "Status": "in-use",
                    "MacAddress": "00:00:00:00:00:11",
                    "Description": "",
                    "Groups": [],
                    "Attachment": {"DeviceIndex": 1},
                    "Ipv6Addresses": [
                        {"Ipv6Address": "2001:db8::c", "IsPrimaryIpv6": False},
                    ],
                },
            ],
        )
    ]

    data = transform_ec2_instances(reservations, FAKE_REGION, FAKE_ACCOUNT_ID)

    assert len(data.ipv6_address_list) == 3
    assert {
        "Ipv6Address": "2001:db8::a",
        "NetworkInterfaceId": "eni-10",
        "IsPrimaryIpv6": True,
    } in data.ipv6_address_list
    assert {
        "Ipv6Address": "2001:db8::b",
        "NetworkInterfaceId": "eni-10",
        "IsPrimaryIpv6": False,
    } in data.ipv6_address_list
    assert {
        "Ipv6Address": "2001:db8::c",
        "NetworkInterfaceId": "eni-11",
        "IsPrimaryIpv6": False,
    } in data.ipv6_address_list
    # Instance field comes from primary NI (DeviceIndex=0) with IsPrimaryIpv6=True preferred.
    assert data.instance_list[0]["IPv6Address"] == "2001:db8::a"


def test_transform_ipv6_primary_flag_on_non_first_entry():
    """When IsPrimaryIpv6=True is on the second entry, it is preferred for the instance field."""
    reservations = [
        _make_reservation(
            "i-5",
            [
                {
                    "NetworkInterfaceId": "eni-20",
                    "Status": "in-use",
                    "MacAddress": "00:00:00:00:00:20",
                    "Description": "",
                    "Groups": [],
                    "Attachment": {"DeviceIndex": 0},
                    "Ipv6Addresses": [
                        {"Ipv6Address": "2001:db8::1", "IsPrimaryIpv6": False},
                        {"Ipv6Address": "2001:db8::2", "IsPrimaryIpv6": True},
                    ],
                }
            ],
        )
    ]

    data = transform_ec2_instances(reservations, FAKE_REGION, FAKE_ACCOUNT_ID)

    # Should pick the entry with IsPrimaryIpv6=True, not the first entry.
    assert data.instance_list[0]["IPv6Address"] == "2001:db8::2"


def test_transform_ipv6_non_primary_nic_does_not_set_instance_field():
    """IPv6 on a secondary NI (DeviceIndex=1) does not populate instance IPv6Address."""
    reservations = [
        _make_reservation(
            "i-6",
            [
                {
                    "NetworkInterfaceId": "eni-30",
                    "Status": "in-use",
                    "MacAddress": "00:00:00:00:00:30",
                    "Description": "",
                    "Groups": [],
                    "Attachment": {"DeviceIndex": 1},
                    "Ipv6Addresses": [
                        {"Ipv6Address": "2001:db8::ff", "IsPrimaryIpv6": False}
                    ],
                }
            ],
        )
    ]

    data = transform_ec2_instances(reservations, FAKE_REGION, FAKE_ACCOUNT_ID)

    # No DeviceIndex=0 NI, so instance field stays None.
    assert data.instance_list[0]["IPv6Address"] is None
    # The address is still recorded in ipv6_address_list.
    assert len(data.ipv6_address_list) == 1
    assert data.ipv6_address_list[0]["Ipv6Address"] == "2001:db8::ff"


def test_transform_ipv6_missing_is_primary_defaults_false():
    """Entries without the IsPrimaryIpv6 key default to False rather than None."""
    reservations = [
        _make_reservation(
            "i-7",
            [
                {
                    "NetworkInterfaceId": "eni-40",
                    "Status": "in-use",
                    "MacAddress": "00:00:00:00:00:40",
                    "Description": "",
                    "Groups": [],
                    "Attachment": {"DeviceIndex": 0},
                    # IsPrimaryIpv6 key is absent (older API response)
                    "Ipv6Addresses": [{"Ipv6Address": "2001:db8::100"}],
                }
            ],
        )
    ]

    data = transform_ec2_instances(reservations, FAKE_REGION, FAKE_ACCOUNT_ID)

    assert data.ipv6_address_list[0]["IsPrimaryIpv6"] is False


def test_transform_ec2_instances_extracts_metadata_options():
    data = transform_ec2_instances(
        INSTANCE_WITH_IAM_PROFILE, FAKE_REGION, FAKE_ACCOUNT_ID
    )

    assert data.instance_list[0]["MetadataHttpTokens"] == "required"
    assert data.instance_list[0]["MetadataHttpPutResponseHopLimit"] == 2
    assert data.instance_list[0]["MetadataHttpEndpoint"] == "enabled"
    assert data.instance_list[0]["MetadataHttpProtocolIpv6"] == "disabled"
    assert data.instance_list[0]["MetadataInstanceTags"] == "disabled"
    assert data.instance_list[0]["ImdsAccessMode"] == "v2_only"
    assert data.instance_list[0]["ImdsV1Enabled"] is False
    assert data.instance_list[0]["ImdsV2Required"] is True
