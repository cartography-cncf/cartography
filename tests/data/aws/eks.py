import datetime

LIST_CLUSTERS = [
    "cluster_1",
    "cluster_2",
]

DESCRIBE_CLUSTERS = [
    {
        "name": "cluster_1",
        "arn": "arn:aws:eks:eu-west-1:111111111111:cluster/cluster_1",
        "createdAt": datetime.datetime(2019, 1, 1, 0, 0, 1),
        "endpoint": "https://1111111.sk1.eu-west-1.eks.amazonaws.com",
        "version": "1.14",
        "platformVersion": "eks.9",
        "roleArn": "arn:aws:iam::111111111111:role/cluster_1",
        "resourcesVpcConfig": {
            "subnetIds": ["subnet-1111", "subnet-2222", "subnet-3333"],
            "securityGroupIds": ["sg-1111"],
            "clusterSecurityGroupId": "sg-1111",
            "vpcId": "vpc-1111",
            "endpointPublicAccess": False,
            "endpointPrivateAccess": True,
            "publicAccessCidrs": [],
        },
        "logging": {
            "clusterLogging": [{
                "types": ["api", "audit"],
                "enabled": True,
            }],
        },
        "status": "ACTIVE",
        "certificateAuthority": {
            "data": "aaaaaaa",
        },
        "tags": {},
    },
    {
        "name": "cluster_2",
        "arn": "arn:aws:eks:eu-west-2:222222222222:cluster/cluster_2",
        "createdAt": datetime.datetime(2019, 1, 1, 0, 0, 1),
        "endpoint": "https://222222222222.sk1.eu-west-1.eks.amazonaws.com",
        "version": "1.14",
        "platformVersion": "eks.9",
        "roleArn": "arn:aws:iam::222222222222:role/cluster_2",
        "resourcesVpcConfig": {
            "subnetIds": ["subnet-1111", "subnet-2222", "subnet-3333"],
            "securityGroupIds": ["sg-1111"],
            "clusterSecurityGroupId": "sg-1111",
            "vpcId": "vpc-1111",
            "endpointPublicAccess": False,
            "endpointPrivateAccess": True,
            "publicAccessCidrs": [],
        },
        "logging": {
            "clusterLogging": [{
                "types": ["api", "audit"],
                "enabled": True,
            }],
        },
        "status": "ACTIVE",
        "certificateAuthority": {
            "data": "aaaaaaa",
        },
        "tags": {},
    },
]
