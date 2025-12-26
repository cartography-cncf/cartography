import json
from datetime import datetime

from cartography.intel.aws.ec2.vpc_endpoint import transform_vpc_endpoint_data

FAKE_REGION = "us-east-1"


def test_transform_vpc_endpoint_interface_endpoint():
    """Test transforming an Interface VPC endpoint"""
    raw_endpoints = [
        {
            "VpcEndpointId": "vpce-1234567890abcdef0",
            "VpcId": "vpc-12345678",
            "ServiceName": "com.amazonaws.us-east-1.s3",
            "ServiceRegion": "us-east-1",
            "VpcEndpointType": "Interface",
            "State": "available",
            "PolicyDocument": '{"Version":"2012-10-17","Statement":[{"Effect":"Allow","Principal":"*","Action":"*","Resource":"*"}]}',
            "RouteTableIds": [],
            "SubnetIds": ["subnet-12345", "subnet-67890"],
            "NetworkInterfaceIds": ["eni-11111", "eni-22222"],
            "DnsEntries": [
                {"DnsName": "vpce-1234567890abcdef0.s3.us-east-1.vpce.amazonaws.com", "HostedZoneId": "Z123"}
            ],
            "PrivateDnsEnabled": True,
            "RequesterManaged": False,
            "IpAddressType": "ipv4",
            "OwnerId": "123456789012",
            "CreationTimestamp": datetime(2023, 1, 15, 10, 30, 0),
            "Groups": [
                {"GroupId": "sg-12345", "GroupName": "default"}
            ],
        }
    ]

    result = transform_vpc_endpoint_data(raw_endpoints, FAKE_REGION)

    assert len(result) == 1
    endpoint = result[0]

    assert endpoint["VpcEndpointId"] == "vpce-1234567890abcdef0"
    assert endpoint["VpcId"] == "vpc-12345678"
    assert endpoint["ServiceName"] == "com.amazonaws.us-east-1.s3"
    assert endpoint["VpcEndpointType"] == "Interface"
    assert endpoint["State"] == "available"
    assert endpoint["SubnetIds"] == ["subnet-12345", "subnet-67890"]
    assert endpoint["NetworkInterfaceIds"] == ["eni-11111", "eni-22222"]
    assert endpoint["PrivateDnsEnabled"] is True
    assert endpoint["RequesterManaged"] is False
    assert endpoint["IpAddressType"] == "ipv4"
    assert endpoint["OwnerId"] == "123456789012"
    assert endpoint["CreationTimestamp"] == "2023-01-15T10:30:00"
    assert len(endpoint["Groups"]) == 1


def test_transform_vpc_endpoint_gateway_endpoint():
    """Test transforming a Gateway VPC endpoint"""
    raw_endpoints = [
        {
            "VpcEndpointId": "vpce-gateway123",
            "VpcId": "vpc-12345678",
            "ServiceName": "com.amazonaws.us-east-1.dynamodb",
            "ServiceRegion": "us-east-1",
            "VpcEndpointType": "Gateway",
            "State": "available",
            "PolicyDocument": None,
            "RouteTableIds": ["rtb-12345", "rtb-67890"],
            "SubnetIds": [],
            "NetworkInterfaceIds": [],
            "DnsEntries": [],
            "PrivateDnsEnabled": False,
            "RequesterManaged": False,
            "IpAddressType": None,
            "OwnerId": "123456789012",
            "CreationTimestamp": datetime(2023, 2, 20, 14, 45, 0),
            "Groups": [],
        }
    ]

    result = transform_vpc_endpoint_data(raw_endpoints, FAKE_REGION)

    assert len(result) == 1
    endpoint = result[0]

    assert endpoint["VpcEndpointId"] == "vpce-gateway123"
    assert endpoint["VpcEndpointType"] == "Gateway"
    assert endpoint["RouteTableIds"] == ["rtb-12345", "rtb-67890"]
    assert endpoint["SubnetIds"] == []
    assert endpoint["NetworkInterfaceIds"] == []
    assert endpoint["PrivateDnsEnabled"] is False
    assert endpoint["PolicyDocument"] is None


def test_transform_vpc_endpoint_with_dict_policy():
    """Test transforming VPC endpoint with dict policy document"""
    policy_dict = {
        "Version": "2012-10-17",
        "Statement": [{"Effect": "Allow", "Principal": "*", "Action": "s3:GetObject", "Resource": "arn:aws:s3:::mybucket/*"}]
    }

    raw_endpoints = [
        {
            "VpcEndpointId": "vpce-policy-test",
            "VpcId": "vpc-12345678",
            "ServiceName": "com.amazonaws.us-east-1.s3",
            "ServiceRegion": "us-east-1",
            "VpcEndpointType": "Gateway",
            "State": "available",
            "PolicyDocument": policy_dict,
            "RouteTableIds": ["rtb-12345"],
            "SubnetIds": [],
            "NetworkInterfaceIds": [],
            "DnsEntries": [],
            "PrivateDnsEnabled": False,
            "RequesterManaged": False,
            "IpAddressType": None,
            "OwnerId": "123456789012",
            "CreationTimestamp": datetime(2023, 3, 10, 9, 15, 0),
            "Groups": [],
        }
    ]

    result = transform_vpc_endpoint_data(raw_endpoints, FAKE_REGION)

    assert len(result) == 1
    endpoint = result[0]

    # Policy should be converted to JSON string
    assert isinstance(endpoint["PolicyDocument"], str)
    parsed_policy = json.loads(endpoint["PolicyDocument"])
    assert parsed_policy["Version"] == "2012-10-17"
    assert len(parsed_policy["Statement"]) == 1


def test_transform_vpc_endpoint_empty_list():
    """Test transforming an empty list of VPC endpoints"""
    result = transform_vpc_endpoint_data([], FAKE_REGION)
    assert result == []


def test_transform_vpc_endpoint_multiple_endpoints():
    """Test transforming multiple VPC endpoints"""
    raw_endpoints = [
        {
            "VpcEndpointId": "vpce-1",
            "VpcId": "vpc-1",
            "ServiceName": "com.amazonaws.us-east-1.s3",
            "ServiceRegion": "us-east-1",
            "VpcEndpointType": "Gateway",
            "State": "available",
            "PolicyDocument": None,
            "RouteTableIds": ["rtb-1"],
            "SubnetIds": [],
            "NetworkInterfaceIds": [],
            "DnsEntries": [],
            "PrivateDnsEnabled": False,
            "RequesterManaged": False,
            "IpAddressType": None,
            "OwnerId": "123456789012",
            "CreationTimestamp": datetime(2023, 1, 1, 0, 0, 0),
            "Groups": [],
        },
        {
            "VpcEndpointId": "vpce-2",
            "VpcId": "vpc-2",
            "ServiceName": "com.amazonaws.us-east-1.ec2",
            "ServiceRegion": "us-east-1",
            "VpcEndpointType": "Interface",
            "State": "pending",
            "PolicyDocument": None,
            "RouteTableIds": [],
            "SubnetIds": ["subnet-1"],
            "NetworkInterfaceIds": ["eni-1"],
            "DnsEntries": [{"DnsName": "test.com", "HostedZoneId": "Z1"}],
            "PrivateDnsEnabled": True,
            "RequesterManaged": False,
            "IpAddressType": "ipv4",
            "OwnerId": "123456789012",
            "CreationTimestamp": datetime(2023, 2, 1, 0, 0, 0),
            "Groups": [{"GroupId": "sg-1", "GroupName": "default"}],
        },
    ]

    result = transform_vpc_endpoint_data(raw_endpoints, FAKE_REGION)

    assert len(result) == 2
    assert result[0]["VpcEndpointId"] == "vpce-1"
    assert result[1]["VpcEndpointId"] == "vpce-2"
    assert result[0]["VpcEndpointType"] == "Gateway"
    assert result[1]["VpcEndpointType"] == "Interface"


def test_transform_vpc_endpoint_gateway_load_balancer():
    """Test transforming a GatewayLoadBalancer VPC endpoint"""
    raw_endpoints = [
        {
            "VpcEndpointId": "vpce-gwlb",
            "VpcId": "vpc-gwlb",
            "ServiceName": "com.amazonaws.vpce.us-east-1.vpce-svc-123456",
            "ServiceRegion": "us-east-1",
            "VpcEndpointType": "GatewayLoadBalancer",
            "State": "available",
            "PolicyDocument": None,
            "RouteTableIds": [],
            "SubnetIds": ["subnet-gwlb"],
            "NetworkInterfaceIds": ["eni-gwlb"],
            "DnsEntries": [],
            "PrivateDnsEnabled": False,
            "RequesterManaged": False,
            "IpAddressType": "ipv4",
            "OwnerId": "123456789012",
            "CreationTimestamp": datetime(2023, 3, 15, 12, 0, 0),
            "Groups": [{"GroupId": "sg-gwlb", "GroupName": "gwlb-sg"}],
        }
    ]

    result = transform_vpc_endpoint_data(raw_endpoints, FAKE_REGION)

    assert len(result) == 1
    endpoint = result[0]

    assert endpoint["VpcEndpointId"] == "vpce-gwlb"
    assert endpoint["VpcEndpointType"] == "GatewayLoadBalancer"
    assert endpoint["State"] == "available"
    assert endpoint["SubnetIds"] == ["subnet-gwlb"]
    assert endpoint["NetworkInterfaceIds"] == ["eni-gwlb"]
    assert len(endpoint["Groups"]) == 1
    assert endpoint["Groups"][0]["GroupId"] == "sg-gwlb"
