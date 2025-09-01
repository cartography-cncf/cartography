import json

import cartography.intel.gcp.compute
from tests.data.gcp.compute import LIST_FIREWALLS_RESPONSE
from tests.data.gcp.compute import VPC_RESPONSE
from tests.data.gcp.compute import VPC_SUBNET_RESPONSE


def test_transform_gcp_vpcs():
    """
    Ensure that transform_gcp_vpcs() returns a list of VPCs, computes correct partial_uris, and parses the nested
    objects correctly.
    """
    vpc_list = cartography.intel.gcp.compute.transform_gcp_vpcs(VPC_RESPONSE)
    assert len(vpc_list) == 1

    vpc = vpc_list[0]
    assert vpc["partial_uri"] == "projects/project-abc/global/networks/default"
    assert vpc["routing_config_routing_mode"] == "REGIONAL"


def test_transform_gcp_subnets():
    """
    Ensure that transform_gcp_subnets() returns a list of subnets with correct partial_uris and tests for the presence
    of some key members.
    """
    subnet_list = cartography.intel.gcp.compute.transform_gcp_subnets(
        VPC_SUBNET_RESPONSE,
    )
    assert len(subnet_list) == 1

    subnet = subnet_list[0]
    assert subnet["ip_cidr_range"] == "10.0.0.0/20"
    assert (
        subnet["partial_uri"]
        == "projects/project-abc/regions/europe-west2/subnetworks/default"
    )
    assert subnet["region"] == "europe-west2"
    assert not subnet["private_ip_google_access"]


def test_get_gcp_subnets_continues_on_timeout():
    class FakeRequest:
        def __init__(self, responses):
            self._responses = responses
            self._index = 0

        def execute(self, num_retries: int, timeout: int):
            resp = self._responses[self._index]
            self._index += 1
            if isinstance(resp, Exception):
                raise resp
            return resp

    class FakeSubnetworks:
        def __init__(self, responses):
            self._responses = responses

        def list(self, project: str, region: str):
            return FakeRequest(self._responses)

        def list_next(self, previous_request, previous_response):
            if previous_response.get("nextPageToken") and previous_request._index < len(
                self._responses
            ):
                return previous_request
            return None

    class FakeCompute:
        def __init__(self, responses):
            self._subnetworks = FakeSubnetworks(responses)

        def subnetworks(self):
            return self._subnetworks

    responses = [
        {
            "id": "projects/test/regions/us/subnetworks",
            "items": [{"name": "sub1"}],
            "nextPageToken": "tok",
        },
        TimeoutError(),
    ]
    compute = FakeCompute(responses)
    res = cartography.intel.gcp.compute.get_gcp_subnets("test", "us", compute)
    assert res["id"] == "projects/test/regions/us/subnetworks"
    assert res["items"] == [{"name": "sub1"}]


def test_get_gcp_instance_responses_skips_transient_errors():
    from googleapiclient.errors import HttpError
    from httplib2 import Response

    def make_http_error(status: int, reason: str) -> HttpError:
        content = json.dumps({"error": {"errors": [{"reason": reason}]}}).encode(
            "utf-8"
        )
        return HttpError(Response({"status": status}), content)

    class FakeRequest:
        def __init__(self, resp):
            self._resp = resp

        def execute(self, num_retries: int):
            if isinstance(self._resp, Exception):
                raise self._resp
            return self._resp

    class FakeInstances:
        def list(self, project: str, zone: str):
            if zone == "bad-zone":
                return FakeRequest(make_http_error(503, "backendError"))
            return FakeRequest({"id": zone, "items": [{"name": f"inst-{zone}"}]})

    class FakeCompute:
        def instances(self):
            return FakeInstances()

    zones = [{"name": "good-zone"}, {"name": "bad-zone"}]
    compute = FakeCompute()
    res = cartography.intel.gcp.compute.get_gcp_instance_responses(
        "proj", zones, compute
    )
    assert len(res) == 1
    assert res[0]["id"] == "good-zone"


def test_parse_compute_full_uri_to_partial_uri():
    subnet_uri = "https://www.googleapis.com/compute/v1/projects/project-abc/regions/europe-west2/subnetworks/default"
    inst_uri = "https://www.googleapis.com/compute/v1/projects/project-abc/zones/europe-west2-b/disks/instance-1"
    vpc_uri = "https://www.googleapis.com/compute/v1/projects/project-abc/global/networks/default"

    assert (
        cartography.intel.gcp.compute._parse_compute_full_uri_to_partial_uri(subnet_uri)
        == "projects/project-abc/regions/europe-west2/subnetworks/default"
    )
    assert (
        cartography.intel.gcp.compute._parse_compute_full_uri_to_partial_uri(inst_uri)
        == "projects/project-abc/zones/europe-west2-b/disks/instance-1"
    )
    assert (
        cartography.intel.gcp.compute._parse_compute_full_uri_to_partial_uri(vpc_uri)
        == "projects/project-abc/global/networks/default"
    )


def test_transform_gcp_firewall():
    fw_list = cartography.intel.gcp.compute.transform_gcp_firewall(
        LIST_FIREWALLS_RESPONSE,
    )

    # Default-allow-internal
    sample_fw = fw_list[1]
    assert len(sample_fw["transformed_deny_list"]) == 0

    sample_udp_all_rule = sample_fw["transformed_allow_list"][1]

    assert sample_udp_all_rule["protocol"] == "udp"
    assert sample_udp_all_rule["fromport"] == 0
    assert sample_udp_all_rule["toport"] == 65535

    sample_fw_icmp_rule = sample_fw["transformed_allow_list"][2]
    assert sample_fw_icmp_rule["protocol"] == "icmp"
    assert sample_fw_icmp_rule["fromport"] is None
    assert sample_fw_icmp_rule["toport"] is None
    assert sample_fw_icmp_rule["protocol"] == "icmp"
