import pytest

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.cloudflare.dnsrecord import CloudflareDNSRecordSchema
from tests.data.cloudflare.dnsrecords import CLOUDFLARE_DNSRECORDS

TEST_UPDATE_TAG = 1234567890


@pytest.fixture
def root_dir(request):
    return request.config.rootpath


def test_analysis_jobs_cypher_syntax(neo4j_session, root_dir):
    load(
        neo4j_session,
        CloudflareDNSRecordSchema(),
        CLOUDFLARE_DNSRECORDS,
        lastupdated=TEST_UPDATE_TAG,
        zone_id="cf_zone_id",
    )

    # no links
    assert get_dns_points_to(neo4j_session) == []

    # run the job
    job_file = (
        root_dir
        / "cartography"
        / "data"
        / "jobs"
        / "analysis"
        / "dnsrecord_cname_linking.json"
    )
    job = GraphJob.from_json_file(job_file)
    job.merge_parameters({"UPDATE_TAG": TEST_UPDATE_TAG})
    job.run(neo4j_session)

    actual = get_dns_points_to(neo4j_session)
    expected = [("www.simpson.corp", "simpson.corp")]

    assert actual == expected


def get_dns_points_to(neo4j_session):
    query = neo4j_session.run(
        "MATCH (s:DNSRecord) -[p:DNS_POINTS_TO]- (t:DNSRecord) RETURN s.name, t.name"
    )
    return [(r["s.name"], r["t.name"]) for r in query]
