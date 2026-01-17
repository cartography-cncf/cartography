from cartography.intel.aws.ec2.instances import transform_ec2_instances
from tests.data.aws.ec2.instances_missing_private_ip import (
    DESCRIBE_INSTANCES_MISSING_PRIVATE_IP,
)

FAKE_REGION = "us-east-1"
FAKE_ACCOUNT_ID = "123456789012"


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
