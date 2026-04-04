from cartography.intel.aws.ec2.nat_gateways import transform_nat_gateways


def test_transform_nat_gateways_public():
    """
    Verify that a public NAT gateway is transformed correctly, flattening
    the primary NatGatewayAddresses entry and constructing the ARN.
    """
    raw = [
        {
            "NatGatewayId": "nat-0abc",
            "SubnetId": "subnet-123",
            "VpcId": "vpc-456",
            "State": "available",
            "CreateTime": "2021-01-01T00:00:00+00:00",
            "ConnectivityType": "public",
            "NatGatewayAddresses": [
                {
                    "AllocationId": "eipalloc-abc",
                    "NetworkInterfaceId": "eni-abc",
                    "PrivateIp": "10.0.0.1",
                    "PublicIp": "1.2.3.4",
                    "IsPrimary": True,
                },
            ],
        },
    ]
    result = transform_nat_gateways(raw, "us-east-1", "123456789012")

    assert len(result) == 1
    r = result[0]
    assert r["NatGatewayId"] == "nat-0abc"
    assert r["SubnetId"] == "subnet-123"
    assert r["VpcId"] == "vpc-456"
    assert r["State"] == "available"
    assert r["ConnectivityType"] == "public"
    assert r["Arn"] == "arn:aws:ec2:us-east-1:123456789012:natgateway/nat-0abc"
    assert r["AllocationId"] == "eipalloc-abc"
    assert r["AllocationIds"] == ["eipalloc-abc"]
    assert r["NetworkInterfaceId"] == "eni-abc"
    assert r["PrivateIp"] == "10.0.0.1"
    assert r["PublicIp"] == "1.2.3.4"


def test_transform_nat_gateways_isprimary_selection():
    """
    Verify that when multiple NatGatewayAddresses are present, the entry
    marked IsPrimary=True is selected over the first entry.
    """
    raw = [
        {
            "NatGatewayId": "nat-0multi",
            "SubnetId": "subnet-123",
            "VpcId": "vpc-456",
            "State": "available",
            "CreateTime": "2021-01-01T00:00:00+00:00",
            "ConnectivityType": "public",
            "NatGatewayAddresses": [
                {
                    "AllocationId": "eipalloc-secondary",
                    "NetworkInterfaceId": "eni-secondary",
                    "PrivateIp": "10.0.0.2",
                    "PublicIp": "2.2.2.2",
                    "IsPrimary": False,
                },
                {
                    "AllocationId": "eipalloc-primary",
                    "NetworkInterfaceId": "eni-primary",
                    "PrivateIp": "10.0.0.1",
                    "PublicIp": "1.1.1.1",
                    "IsPrimary": True,
                },
            ],
        },
    ]
    result = transform_nat_gateways(raw, "us-east-1", "123456789012")

    assert len(result) == 1
    r = result[0]
    assert r["AllocationId"] == "eipalloc-primary"
    assert r["AllocationIds"] == ["eipalloc-secondary", "eipalloc-primary"]
    assert r["NetworkInterfaceId"] == "eni-primary"
    assert r["PrivateIp"] == "10.0.0.1"
    assert r["PublicIp"] == "1.1.1.1"


def test_transform_nat_gateways_private_no_addresses():
    """
    Verify that a private NAT gateway (no NatGatewayAddresses) produces None
    for all address-related fields and still gets the correct ARN.
    """
    raw = [
        {
            "NatGatewayId": "nat-0prv",
            "SubnetId": "subnet-789",
            "VpcId": "vpc-012",
            "State": "available",
            "CreateTime": "2021-03-01T00:00:00+00:00",
            "ConnectivityType": "private",
            "NatGatewayAddresses": [],
        },
    ]
    result = transform_nat_gateways(raw, "eu-west-1", "123456789012")

    assert len(result) == 1
    r = result[0]
    assert r["NatGatewayId"] == "nat-0prv"
    assert r["Arn"] == "arn:aws:ec2:eu-west-1:123456789012:natgateway/nat-0prv"
    assert r["AllocationId"] is None
    assert r["AllocationIds"] == []
    assert r["NetworkInterfaceId"] is None
    assert r["PrivateIp"] is None
    assert r["PublicIp"] is None


def test_transform_nat_gateways_missing_create_time():
    """
    Verify that a missing CreateTime becomes None rather than causing an error.
    """
    raw = [
        {
            "NatGatewayId": "nat-0nct",
            "SubnetId": "subnet-abc",
            "VpcId": "vpc-def",
            "State": "pending",
            "ConnectivityType": "public",
            "NatGatewayAddresses": [],
        },
    ]
    result = transform_nat_gateways(raw, "us-west-2", "123456789012")

    assert len(result) == 1
    assert result[0]["CreateTime"] is None


def test_transform_nat_gateways_multiple():
    """
    Verify that multiple NAT gateways are all transformed independently.
    """
    raw = [
        {
            "NatGatewayId": f"nat-{i:04d}",
            "SubnetId": f"subnet-{i:04d}",
            "VpcId": f"vpc-{i:04d}",
            "State": "available",
            "CreateTime": "2021-01-01T00:00:00+00:00",
            "ConnectivityType": "public",
            "NatGatewayAddresses": [{"AllocationId": f"eipalloc-{i:04d}"}],
        }
        for i in range(3)
    ]
    result = transform_nat_gateways(raw, "ap-southeast-1", "999999999999")

    assert len(result) == 3
    for i, r in enumerate(result):
        assert r["NatGatewayId"] == f"nat-{i:04d}"
        assert r["AllocationId"] == f"eipalloc-{i:04d}"
        assert r["AllocationIds"] == [f"eipalloc-{i:04d}"]
        assert r["Arn"] == (
            f"arn:aws:ec2:ap-southeast-1:999999999999:natgateway/nat-{i:04d}"
        )
