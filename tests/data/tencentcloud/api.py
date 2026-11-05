"""Fake Tencent Cloud API 3.0 and COS responses for the tencentcloud module tests.

Payloads use the field names and types of the real API responses. Only `ap-guangzhou`
holds resources; every other region answers with empty result sets, and CLB answers
`UnsupportedRegion` outside `ap-guangzhou` so the region-skip path is exercised.
"""

import copy
from typing import Any
from unittest.mock import Mock

from tencentcloud.common.exception.tencent_cloud_sdk_exception import (
    TencentCloudSDKException,
)

ACCOUNT_ID = "100000000001"
APP_ID = 1250000000
RESOURCE_REGION = "ap-guangzhou"
REGIONS = ["ap-guangzhou", "ap-singapore"]

ALICE_UIN = 100000000011
CI_BOT_UIN = 100000000012
ADMINS_GROUP_ID = 2001
APP_ROLE_ID = "4611686018427397921"
AUDITOR_ROLE_ID = "4611686018427397922"
CUSTOM_POLICY_ID = 30001

GET_USER_APP_ID = {"Uin": "100000000002", "OwnerUin": ACCOUNT_ID, "AppId": APP_ID}

DESCRIBE_REGIONS = {
    "TotalCount": 3,
    "RegionSet": [
        {
            "Region": "ap-guangzhou",
            "RegionName": "South China(Guangzhou)",
            "RegionState": "AVAILABLE",
        },
        {
            "Region": "ap-singapore",
            "RegionName": "Southeast Asia(Singapore)",
            "RegionState": "AVAILABLE",
        },
        {
            "Region": "ap-mumbai",
            "RegionName": "South Asia(Mumbai)",
            "RegionState": "UNAVAILABLE",
        },
    ],
}

# ---------------------------------------------------------------------------
# CAM
# ---------------------------------------------------------------------------

USERS = [
    {
        "Uin": ALICE_UIN,
        "Name": "alice",
        "Uid": 11,
        "Remark": "",
        "ConsoleLogin": 1,
        "PhoneNum": "",
        "CountryCode": "86",
        "Email": "alice@example.com",
        "CreateTime": "2026-01-02 03:04:05",
        "NickName": "Alice",
    },
    {
        "Uin": CI_BOT_UIN,
        "Name": "ci-bot",
        "Uid": 12,
        "Remark": "Deploys from CI",
        "ConsoleLogin": 0,
        "PhoneNum": "",
        "CountryCode": "86",
        "Email": "",
        "CreateTime": "2026-01-03 03:04:05",
        "NickName": "",
    },
]

ACCESS_KEYS = {
    ALICE_UIN: [],
    CI_BOT_UIN: [
        {
            "AccessKeyId": "test-access-key-ci-bot",
            "Status": "Active",
            "CreateTime": "2026-02-01 00:00:00",
            "Description": "github actions",
        },
    ],
}

SECRET_ID_LAST_USED = [
    {
        "SecretId": "test-access-key-ci-bot",
        "LastUsedDate": "2026-10-30",
        "LastSecretUsedDate": 1793318400,
    },
]

GROUPS = [
    {
        "GroupId": ADMINS_GROUP_ID,
        "GroupName": "admins",
        "CreateTime": "2026-01-01 00:00:00",
        "Remark": "Administrators",
    },
]

GROUP_MEMBERS = {
    ADMINS_GROUP_ID: [
        {"Uid": 11, "Uin": ALICE_UIN, "Name": "alice", "UserType": 1},
    ],
}

ROLES = [
    {
        "RoleId": APP_ROLE_ID,
        "RoleName": "cvm-app-role",
        "PolicyDocument": (
            '{"version":"2.0","statement":[{"action":"name/sts:AssumeRole",'
            '"effect":"allow","principal":{"service":["cvm.qcloud.com"]}}]}'
        ),
        "Description": "Role for the web tier",
        "AddTime": "2026-01-05 00:00:00",
        "UpdateTime": "2026-01-05 00:00:00",
        "ConsoleLogin": 0,
        "RoleType": "user",
        "SessionDuration": 7200,
        "RoleArn": f"qcs::cam::uin/{ACCOUNT_ID}:roleName/cvm-app-role",
    },
    {
        "RoleId": AUDITOR_ROLE_ID,
        "RoleName": "cross-account-auditor",
        "PolicyDocument": (
            '{"version":"2.0","statement":[{"action":"name/sts:AssumeRole",'
            '"effect":"allow","principal":{"qcs":["qcs::cam::uin/200000000001:root"]}}]}'
        ),
        "Description": "",
        "AddTime": "2026-01-06 00:00:00",
        "UpdateTime": "2026-01-06 00:00:00",
        "ConsoleLogin": 1,
        "RoleType": "user",
        "SessionDuration": 3600,
        "RoleArn": f"qcs::cam::uin/{ACCOUNT_ID}:roleName/cross-account-auditor",
    },
]

CUSTOM_POLICIES = [
    {
        "PolicyId": CUSTOM_POLICY_ID,
        "PolicyName": "cos-read-logs",
        "AddTime": "2026-01-07 00:00:00",
        "Type": 1,
        "Description": "Read the log bucket",
        "CreateMode": 2,
        "Attachments": 2,
        "ServiceType": "cos",
    },
]

POLICY_DOCUMENTS = {
    CUSTOM_POLICY_ID: {
        "PolicyName": "cos-read-logs",
        "Description": "Read the log bucket",
        "Type": 1,
        "AddTime": "2026-01-07 00:00:00",
        "UpdateTime": "2026-03-01 00:00:00",
        "PolicyDocument": (
            '{"version":"2.0","statement":[{"effect":"allow",'
            '"action":["name/cos:GetObject"],"resource":["*"]}]}'
        ),
    },
}

ADMINISTRATOR_ACCESS = {
    "PolicyId": 1,
    "PolicyName": "AdministratorAccess",
    "AddTime": "2026-01-01 00:00:00",
    "CreateMode": 2,
    "PolicyType": "QCS",
    "Remark": "Full read-write access to all products",
}
READ_ONLY_ACCESS = {
    "PolicyId": 4,
    "PolicyName": "ReadOnlyAccess",
    "AddTime": "2026-01-06 00:00:00",
    "PolicyType": "QCS",
    "CreateMode": 2,
    "Description": "Read-only access to all products",
}
COS_READ_LOGS_ATTACHMENT = {
    "PolicyId": CUSTOM_POLICY_ID,
    "PolicyName": "cos-read-logs",
    "AddTime": "2026-01-07 00:00:00",
    "CreateMode": 2,
    "PolicyType": "User",
    "Remark": "Read the log bucket",
}

USER_POLICIES = {
    ALICE_UIN: [],
    CI_BOT_UIN: [COS_READ_LOGS_ATTACHMENT],
}
GROUP_POLICIES = {ADMINS_GROUP_ID: [ADMINISTRATOR_ACCESS]}
ROLE_POLICIES = {
    APP_ROLE_ID: [COS_READ_LOGS_ATTACHMENT],
    AUDITOR_ROLE_ID: [READ_ONLY_ACCESS],
}

# ---------------------------------------------------------------------------
# VPC
# ---------------------------------------------------------------------------

VPCS = [
    {
        "VpcName": "prod",
        "VpcId": "vpc-prod0001",
        "CidrBlock": "10.0.0.0/16",
        "IsDefault": False,
        "EnableMulticast": False,
        "CreatedTime": "2026-01-10 00:00:00",
        "DnsServerSet": ["183.60.83.19", "183.60.82.98"],
        "DomainName": "",
        "DhcpOptionsId": "",
        "EnableDhcp": True,
        "Ipv6CidrBlock": "",
        "TagSet": [{"Key": "env", "Value": "prod"}],
        "AssistantCidrSet": [
            {"VpcId": "vpc-prod0001", "CidrBlock": "172.16.0.0/16", "AssistantType": 0},
        ],
    },
]

SUBNETS = [
    {
        "VpcId": "vpc-prod0001",
        "SubnetId": "subnet-web00001",
        "SubnetName": "prod-web",
        "CidrBlock": "10.0.1.0/24",
        "IsDefault": False,
        "EnableBroadcast": False,
        "Zone": "ap-guangzhou-3",
        "RouteTableId": "rtb-prod0001",
        "CreatedTime": "2026-01-10 00:00:00",
        "AvailableIpAddressCount": 250,
        "Ipv6CidrBlock": "",
        "NetworkAclId": "",
        "IsRemoteVpcSnat": False,
        "TotalIpAddressCount": 253,
        "TagSet": [],
    },
]

_EMPTY_TEMPLATE_REFS = {
    "AddressTemplate": {"AddressId": "", "AddressGroupId": ""},
    "ServiceTemplate": {"ServiceId": "", "ServiceGroupId": ""},
}

SECURITY_GROUPS = [
    {
        "SecurityGroupId": "sg-web00001",
        "SecurityGroupName": "web",
        "SecurityGroupDesc": "Web tier",
        "ProjectId": "0",
        "IsDefault": False,
        "CreatedTime": "2026-01-10 00:00:00",
        "TagSet": [],
        "UpdateTime": "2026-02-10 00:00:00",
    },
]

SECURITY_GROUP_POLICIES = {
    "sg-web00001": {
        "Version": "3",
        "Ingress": [
            {
                "PolicyIndex": 0,
                "Protocol": "TCP",
                "Port": "443",
                "CidrBlock": "0.0.0.0/0",
                "Ipv6CidrBlock": "",
                "SecurityGroupId": "",
                "Action": "ACCEPT",
                "PolicyDescription": "https from anywhere",
                "ModifyTime": "2026-02-10 00:00:00",
                **_EMPTY_TEMPLATE_REFS,
            },
            {
                "PolicyIndex": 1,
                "Protocol": "TCP",
                "Port": "22",
                "CidrBlock": "0.0.0.0/0",
                "Ipv6CidrBlock": "",
                "SecurityGroupId": "",
                "Action": "DROP",
                "PolicyDescription": "no ssh",
                "ModifyTime": "2026-02-10 00:00:00",
                **_EMPTY_TEMPLATE_REFS,
            },
        ],
        "Egress": [
            {
                "PolicyIndex": 0,
                "Protocol": "ALL",
                "Port": "all",
                "CidrBlock": "0.0.0.0/0",
                "Ipv6CidrBlock": "",
                "SecurityGroupId": "",
                "Action": "ACCEPT",
                "PolicyDescription": "",
                "ModifyTime": "2026-02-10 00:00:00",
                **_EMPTY_TEMPLATE_REFS,
            },
        ],
    },
}

# ---------------------------------------------------------------------------
# CVM / CBS / CLB
# ---------------------------------------------------------------------------

INSTANCES = [
    {
        "Placement": {"Zone": "ap-guangzhou-3", "ProjectId": 0, "HostId": None},
        "InstanceId": "ins-web00001",
        "InstanceType": "S5.MEDIUM4",
        "CPU": 2,
        "Memory": 4,
        "RestrictState": "NORMAL",
        "InstanceName": "web-1",
        "InstanceChargeType": "POSTPAID_BY_HOUR",
        "SystemDisk": {
            "DiskType": "CLOUD_PREMIUM",
            "DiskId": "disk-web00001",
            "DiskSize": 50,
        },
        "DataDisks": None,
        "PrivateIpAddresses": ["10.0.1.10"],
        "PublicIpAddresses": ["203.0.113.10"],
        "InternetAccessible": {
            "InternetChargeType": "TRAFFIC_POSTPAID_BY_HOUR",
            "InternetMaxBandwidthOut": 10,
            "PublicIpAssigned": True,
        },
        "VirtualPrivateCloud": {
            "VpcId": "vpc-prod0001",
            "SubnetId": "subnet-web00001",
            "AsVpcGateway": False,
        },
        "ImageId": "img-9qrfy1xt",
        "RenewFlag": None,
        "CreatedTime": "2026-03-01T00:00:00Z",
        "ExpiredTime": None,
        "OsName": "TencentOS Server 3.1 (TK4)",
        "SecurityGroupIds": ["sg-web00001"],
        "LoginSettings": {
            "Password": None,
            "KeyIds": ["skey-web00001"],
            "KeepImageLogin": None,
        },
        "InstanceState": "RUNNING",
        "Tags": [{"Key": "app", "Value": "web"}],
        "StopChargingMode": "NOT_APPLICABLE",
        "Uuid": "0e3c7b52-8d7b-4a5e-9b0e-2f7f1d6c0a11",
        "LatestOperation": "RunInstances",
        "LatestOperationState": "SUCCESS",
        "IPv6Addresses": None,
        "CamRoleName": "cvm-app-role",
        "DisableApiTermination": False,
        "HostName": "web-1",
    },
]

DISKS = [
    {
        "DiskId": "disk-web00001",
        "DiskName": "web-1-system",
        "DiskUsage": "SYSTEM_DISK",
        "DiskType": "CLOUD_PREMIUM",
        "DiskSize": 50,
        "DiskState": "ATTACHED",
        "Attached": True,
        "InstanceId": "ins-web00001",
        "InstanceIdList": [],
        "Encrypt": False,
        "KmsKeyId": "",
        "Shareable": False,
        "Portable": False,
        "DeleteWithInstance": True,
        "SnapshotCount": 0,
        "DiskChargeType": "POSTPAID_BY_HOUR",
        "Placement": {"Zone": "ap-guangzhou-3", "ProjectId": 0},
        "Tags": [],
        "CreateTime": "2026-03-01 00:00:00",
    },
    {
        "DiskId": "disk-orphan01",
        "DiskName": "old-data",
        "DiskUsage": "DATA_DISK",
        "DiskType": "CLOUD_SSD",
        "DiskSize": 200,
        "DiskState": "UNATTACHED",
        "Attached": False,
        "InstanceId": "",
        "InstanceIdList": [],
        "Encrypt": True,
        "KmsKeyId": "kms-key00001",
        "Shareable": False,
        "Portable": True,
        "DeleteWithInstance": False,
        "SnapshotCount": 2,
        "DiskChargeType": "POSTPAID_BY_HOUR",
        "Placement": {"Zone": "ap-guangzhou-3", "ProjectId": 0},
        "Tags": [{"Key": "owner", "Value": "data-team"}],
        "CreateTime": "2025-06-01 00:00:00",
    },
]

LOAD_BALANCERS = [
    {
        "LoadBalancerId": "lb-web00001",
        "LoadBalancerName": "web-public",
        "LoadBalancerType": "OPEN",
        "Forward": 1,
        "Domain": "",
        "LoadBalancerVips": ["203.0.113.20"],
        "Status": 1,
        "CreateTime": "2026-03-02 00:00:00",
        "ProjectId": 0,
        "VpcId": "vpc-prod0001",
        "SubnetId": "",
        "Isolation": 0,
        "SecureGroups": ["sg-web00001"],
        "MasterZone": {
            "ZoneId": 100003,
            "Zone": "ap-guangzhou-3",
            "ZoneName": "Guangzhou Zone 3",
        },
        "AddressIPVersion": "ipv4",
        "AddressIPv6": None,
        "ChargeType": "POSTPAID_BY_HOUR",
        "Tags": [{"TagKey": "app", "TagValue": "web"}],
        "LoadBalancerDomain": "lb-web00001-1250000000.clb.gz-tencentclb.com",
    },
]

LOAD_BALANCER_TARGETS = {
    "lb-web00001": [
        {
            "ListenerId": "lbl-https001",
            "Protocol": "HTTPS",
            "Port": 443,
            "Rules": [
                {
                    "LocationId": "loc-root0001",
                    "Domain": "www.example.com",
                    "Url": "/",
                    "Targets": [
                        {
                            "Type": "CVM",
                            "InstanceId": "ins-web00001",
                            "Port": 8080,
                            "Weight": 10,
                            "PublicIpAddresses": ["203.0.113.10"],
                            "PrivateIpAddresses": ["10.0.1.10"],
                        },
                    ],
                },
            ],
            "Targets": None,
            "EndPort": 0,
        },
        {
            "ListenerId": "lbl-tcp00001",
            "Protocol": "TCP",
            "Port": 9000,
            "Rules": None,
            "Targets": [
                {
                    "Type": "ENI",
                    "InstanceId": "eni-other001",
                    "Port": 9000,
                    "Weight": 10,
                    "PrivateIpAddresses": ["10.0.1.50"],
                },
            ],
            "EndPort": 0,
        },
    ],
}

# ---------------------------------------------------------------------------
# COS
# ---------------------------------------------------------------------------

LIST_BUCKETS_XML = f"""<?xml version="1.0" encoding="UTF-8"?>
<ListAllMyBucketsResult>
  <Owner>
    <ID>qcs::cam::uin/{ACCOUNT_ID}:uin/{ACCOUNT_ID}</ID>
    <DisplayName>{ACCOUNT_ID}</DisplayName>
  </Owner>
  <Buckets>
    <Bucket>
      <Name>app-logs-{APP_ID}</Name>
      <Location>ap-guangzhou</Location>
      <CreationDate>2026-01-15T08:00:00Z</CreationDate>
      <BucketType>cos</BucketType>
    </Bucket>
    <Bucket>
      <Name>public-assets-{APP_ID}</Name>
      <Location>ap-singapore</Location>
      <CreationDate>2026-02-15T08:00:00Z</CreationDate>
      <BucketType>cos</BucketType>
    </Bucket>
    <Bucket>
      <Name>locked-down-{APP_ID}</Name>
      <Location>ap-guangzhou</Location>
      <CreationDate>2026-03-15T08:00:00Z</CreationDate>
      <BucketType>cos</BucketType>
    </Bucket>
  </Buckets>
</ListAllMyBucketsResult>
"""

_OWNER_GRANT = f"""
    <Grant>
      <Grantee xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:type="CanonicalUser">
        <ID>qcs::cam::uin/{ACCOUNT_ID}:uin/{ACCOUNT_ID}</ID>
        <DisplayName>qcs::cam::uin/{ACCOUNT_ID}:uin/{ACCOUNT_ID}</DisplayName>
      </Grantee>
      <Permission>FULL_CONTROL</Permission>
    </Grant>"""

PRIVATE_ACL_XML = f"""<?xml version="1.0" encoding="UTF-8"?>
<AccessControlPolicy>
  <Owner>
    <ID>qcs::cam::uin/{ACCOUNT_ID}:uin/{ACCOUNT_ID}</ID>
    <DisplayName>qcs::cam::uin/{ACCOUNT_ID}:uin/{ACCOUNT_ID}</DisplayName>
  </Owner>
  <AccessControlList>{_OWNER_GRANT}
  </AccessControlList>
</AccessControlPolicy>
"""

PUBLIC_READ_ACL_XML = f"""<?xml version="1.0" encoding="UTF-8"?>
<AccessControlPolicy>
  <Owner>
    <ID>qcs::cam::uin/{ACCOUNT_ID}:uin/{ACCOUNT_ID}</ID>
    <DisplayName>qcs::cam::uin/{ACCOUNT_ID}:uin/{ACCOUNT_ID}</DisplayName>
  </Owner>
  <AccessControlList>{_OWNER_GRANT}
    <Grant>
      <Grantee xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:type="Group">
        <URI>http://cam.qcloud.com/groups/global/AllUsers</URI>
      </Grantee>
      <Permission>READ</Permission>
    </Grant>
  </AccessControlList>
</AccessControlPolicy>
"""

ACCESS_DENIED_XML = """<?xml version="1.0" encoding="UTF-8"?>
<Error><Code>AccessDenied</Code><Message>Access Denied.</Message></Error>
"""

BUCKET_ACLS = {
    f"app-logs-{APP_ID}.cos.ap-guangzhou.myqcloud.com": (200, PRIVATE_ACL_XML),
    f"public-assets-{APP_ID}.cos.ap-singapore.myqcloud.com": (200, PUBLIC_READ_ACL_XML),
    f"locked-down-{APP_ID}.cos.ap-guangzhou.myqcloud.com": (403, ACCESS_DENIED_XML),
}


# ---------------------------------------------------------------------------
# Fakes
# ---------------------------------------------------------------------------


def _offset_page(key: str, items: list[dict[str, Any]]) -> dict[str, Any]:
    return {key: copy.deepcopy(items), "TotalCount": len(items)}


def _page(key: str, items: list[dict[str, Any]]) -> dict[str, Any]:
    return {key: copy.deepcopy(items), "TotalNum": len(items)}


class FakeTencentCloudAPI:
    """Stands in for `CommonClient.call_json` and for the HTTP calls COS makes.

    Tests mutate the public attributes to simulate resources changing between syncs.
    """

    def __init__(self) -> None:
        self.instances = copy.deepcopy(INSTANCES)

    def call_json(
        self,
        client: Any,
        action: str,
        params: dict[str, Any],
        headers: Any = None,
        options: Any = None,
    ) -> dict[str, Any]:
        response = self._respond(client._service, client.region, action, params)
        return {"Response": {**response, "RequestId": "fake-request-id"}}

    def _respond(
        self,
        service: str,
        region: str,
        action: str,
        params: dict[str, Any],
    ) -> dict[str, Any]:
        in_resource_region = region == RESOURCE_REGION
        if service == "cam":
            return self._cam(action, params)
        if service == "cvm" and action == "DescribeRegions":
            return copy.deepcopy(DESCRIBE_REGIONS)
        if service == "cvm" and action == "DescribeInstances":
            return _offset_page(
                "InstanceSet", self.instances if in_resource_region else []
            )
        if service == "vpc" and action == "DescribeVpcs":
            return _offset_page("VpcSet", VPCS if in_resource_region else [])
        if service == "vpc" and action == "DescribeSubnets":
            return _offset_page("SubnetSet", SUBNETS if in_resource_region else [])
        if service == "vpc" and action == "DescribeSecurityGroups":
            return _offset_page(
                "SecurityGroupSet",
                SECURITY_GROUPS if in_resource_region else [],
            )
        if service == "vpc" and action == "DescribeSecurityGroupPolicies":
            return {
                "SecurityGroupPolicySet": copy.deepcopy(
                    SECURITY_GROUP_POLICIES[params["SecurityGroupId"]],
                ),
            }
        if service == "cbs" and action == "DescribeDisks":
            return _offset_page("DiskSet", DISKS if in_resource_region else [])
        if service == "clb":
            if not in_resource_region:
                raise TencentCloudSDKException(
                    "UnsupportedRegion",
                    "The service is not supported in this region.",
                    "fake-request-id",
                )
            if action == "DescribeLoadBalancers":
                return _offset_page("LoadBalancerSet", LOAD_BALANCERS)
            if action == "DescribeTargets":
                return {
                    "Listeners": copy.deepcopy(
                        LOAD_BALANCER_TARGETS[params["LoadBalancerId"]],
                    ),
                }
        raise AssertionError(f"Unexpected call {service}.{action} in {region!r}")

    def _cam(self, action: str, params: dict[str, Any]) -> dict[str, Any]:
        if action == "GetUserAppId":
            return copy.deepcopy(GET_USER_APP_ID)
        if action == "ListUsers":
            return {"Data": copy.deepcopy(USERS)}
        if action == "ListAccessKeys":
            return {"AccessKeys": copy.deepcopy(ACCESS_KEYS[params["TargetUin"]])}
        if action == "GetSecurityLastUsed":
            return {
                "SecretIdLastUsedRows": [
                    row
                    for row in copy.deepcopy(SECRET_ID_LAST_USED)
                    if row["SecretId"] in params["SecretIdList"]
                ],
            }
        if action == "ListGroups":
            return _page("GroupInfo", GROUPS)
        if action == "ListUsersForGroup":
            return _page("UserInfo", GROUP_MEMBERS[params["GroupId"]])
        if action == "DescribeRoleList":
            return _page("List", ROLES)
        if action == "ListPolicies":
            assert params["Scope"] == "Local"
            return _page("List", CUSTOM_POLICIES)
        if action == "GetPolicy":
            return copy.deepcopy(POLICY_DOCUMENTS[params["PolicyId"]])
        if action == "ListAttachedUserPolicies":
            return _page("List", USER_POLICIES[params["TargetUin"]])
        if action == "ListAttachedGroupPolicies":
            return _page("List", GROUP_POLICIES[params["TargetGroupId"]])
        if action == "ListAttachedRolePolicies":
            return _page("List", ROLE_POLICIES[params["RoleId"]])
        raise AssertionError(f"Unexpected call cam.{action}")

    def requests_get(self, url: str, params: dict[str, str], **kwargs: Any) -> Mock:
        host = url.removeprefix("https://").rstrip("/")
        if host == "service.cos.myqcloud.com":
            return _http_response(200, LIST_BUCKETS_XML)
        assert params == {"acl": ""}
        status, body = BUCKET_ACLS[host]
        return _http_response(status, body)


def _http_response(status_code: int, body: str) -> Mock:
    response = Mock()
    response.status_code = status_code
    response.content = body.encode()
    if status_code >= 400:
        response.raise_for_status.side_effect = AssertionError(
            f"unexpected raise_for_status() on HTTP {status_code}",
        )
    return response
