import datetime

VALID_CA_CERTIFICATE_DATA_BASE64_DER = (
    "MIIDYTCCAkmgAwIBAgIUPRum6bC1jjYK2ZwSQwmY6514A4UwDQYJKoZIhvcNAQELBQAwQDEfMB0GA1UEAwwW"
    "Y2FydG9ncmFwaHktZml4dHVyZS1jYTEdMBsGA1UECgwUQ2FydG9ncmFwaHkgRml4dHVyZXMwHhcNMjMxMjMx"
    "MDAwMDAwWhcNMzMxMjI5MDAwMDAwWjBAMR8wHQYDVQQDDBZjYXJ0b2dyYXBoeS1maXh0dXJlLWNhMR0wGwYD"
    "VQQKDBRDYXJ0b2dyYXBoeSBGaXh0dXJlczCCASIwDQYJKoZIhvcNAQEBBQADggEPADCCAQoCggEBAORNQKdU"
    "W3YYF1Kq4IClFed05tTO5vaCmtCANTNhyIAmnrAlohsojdb1sKUg6/EK22VfHxNaha1lLItIG8+OORt8ZXSK"
    "qP/lIqTztJnwPUp8gWZoq1FireYvCfm14SKTeeT/qfP/M6CrPNPinBIQctdN1SvJaqD2itoKC1IsktZcARSV"
    "0OIzgNEftuNFqaX6clpEnpT27D+wZMeLQCPEytd21L6q6n2Kg5sRW3IBSPXXEwVrMJJlaBrwxc3U2mLlApf7"
    "69Chdc5W/QuuNtz4dB074fc4C2tV4JcTiMcCuAZhkiyhZBXGWo/yGcXYZmwnIrgJOAJKpvYjtZ3uHqp+aDkC"
    "AwEAAaNTMFEwDwYDVR0TAQH/BAUwAwEB/zAdBgNVHQ4EFgQUSsexprOPEMRxGjt4D+3Gx42dnXYwHwYDVR0j"
    "BBgwFoAUSsexprOPEMRxGjt4D+3Gx42dnXYwDQYJKoZIhvcNAQELBQADggEBAJU53qcA+lr4YInAkdD3lzHm"
    "IqF8+HK5AGvOSwt8ZcTC5n//AT/qUpdrTBbADdB2P1AHho6PPxIzEh97zEeV+amiW3uZp3lD4FIsF/vSACHu"
    "jNbOcka1UPeL0ljQ+eQCiclXvyHozRZ+Cors/SLl6VOteaglVIAwQRuLK6ZwztzB/FVCJk7CrOPG33K8Opb3"
    "42+g1ufbeiFkQNAjDO2ofiBfUCWiWpw7hpzDLPnGvE/e/VhGpXX1TM/7VGE6QtcDiVyWuDgk7hyBXrhIXTzu"
    "A3R4KF/vS6EC5aw+sT57VPywYj9jOZdJFv5mN2DjUu17q/1E2HsBo7g0olUKTgWGvjY="
)

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
            "clusterLogging": [
                {
                    "types": ["api", "audit"],
                    "enabled": True,
                },
            ],
        },
        "status": "ACTIVE",
        "certificateAuthority": {
            "data": VALID_CA_CERTIFICATE_DATA_BASE64_DER,
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
            "clusterLogging": [
                {
                    "types": ["api", "audit"],
                    "enabled": True,
                },
            ],
        },
        "status": "ACTIVE",
        "certificateAuthority": {
            "data": "aaaaaaa",
        },
        "tags": {},
    },
]
