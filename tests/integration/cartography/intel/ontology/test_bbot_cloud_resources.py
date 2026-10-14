import pytest

import cartography.intel.bbot
import cartography.intel.ontology
import cartography.intel.ontology.dnsrecords
from cartography.analysis.ontology.analysis import BBOT_RESOURCE_JOBS
from cartography.analysis.ontology.analysis import (
    BBOT_STORAGE_BUCKET_MATCHES_OBJECT_STORAGE,
)
from cartography.analysis.ontology.analysis import DNS_RECORD_LINKING_JOBS
from cartography.client.core.tx import ensure_indexes
from cartography.config import Config
from cartography.models.aws.s3.bucket import S3BucketSchema
from cartography.models.gcp.storage.bucket import GCPBucketSchema
from cartography.util import run_typed_analysis_job
from tests.data.bbot.events import event
from tests.data.bbot.events import scan_event
from tests.integration.util import check_rels

WEB_IP = "203.0.113.10"
WEB_DNS_NAME = "ec2-203-0-113-10.compute-1.amazonaws.com"
OTHER_DNS_NAME = "ec2-198-51-100-20.compute-1.amazonaws.com"
# AWS keeps the load balancer name's case in its DNS name.
ALB_DNS_NAME = "Web-ALB-123.us-east-1.elb.amazonaws.com"
ALB_ID = (
    "arn:aws:elasticloadbalancing:us-east-1:000000000000:loadbalancer/app/web-alb/123"
)
APP_HOST = "app.example.com"
LB_HOST = "lb.example.com"
APP_URL = "https://app.example.com/login"


def _bbot_events(run: int) -> list[dict]:
    prefix = f"run-{run}"
    scan_uuid = f"SCAN:{prefix}-starting"
    app_port_uuid = f"OPEN_TCP_PORT:{prefix}-app-443"
    url_uuid = f"URL:{prefix}"
    bucket_uuid = f"STORAGE_BUCKET:{prefix}-aws"

    def dns_name(name: str, resolved_hosts: list[str]) -> dict:
        return event(
            "DNS_NAME",
            f"DNS_NAME:{name}",
            f"DNS_NAME:{prefix}-{name}",
            # BBOT reports what it resolved; ingestion normalizes the ontology name.
            f"{name.upper()}.",
            timestamp=run * 100 + 1,
            parent_uuid=scan_uuid,
            host=name,
            resolved_hosts=resolved_hosts,
            module="dnsresolve",
            scope_distance=0,
        )

    def open_port(host: str, port: int, uuid: str) -> dict:
        return event(
            "OPEN_TCP_PORT",
            f"OPEN_TCP_PORT:{host}:{port}",
            uuid,
            f"{host}:{port}",
            timestamp=run * 100 + 3,
            parent_uuid=scan_uuid,
            host=host,
            port=port,
            module="portscan",
        )

    def bucket(name: str, provider: str, url: str, uuid: str) -> dict:
        return event(
            "STORAGE_BUCKET",
            f"STORAGE_BUCKET:{provider}-{name}",
            uuid,
            {"name": name, "provider": provider, "url": url},
            timestamp=run * 100 + 6,
            parent_uuid=scan_uuid,
            module=f"bucket_{provider}",
        )

    return [
        scan_event(run, "STARTING", run * 100),
        dns_name(APP_HOST, [WEB_IP]),
        dns_name(WEB_DNS_NAME, [WEB_IP]),
        dns_name(LB_HOST, [ALB_DNS_NAME.lower()]),
        dns_name(ALB_DNS_NAME.lower(), []),
        event(
            "IP_ADDRESS",
            f"IP_ADDRESS:{WEB_IP}",
            f"IP_ADDRESS:{prefix}",
            WEB_IP,
            timestamp=run * 100 + 2,
            parent_uuid=scan_uuid,
            host=WEB_IP,
            module="dnsresolve",
        ),
        open_port(WEB_IP, 22, f"OPEN_TCP_PORT:{prefix}-ip-22"),
        open_port(APP_HOST, 443, app_port_uuid),
        open_port(LB_HOST, 443, f"OPEN_TCP_PORT:{prefix}-lb-443"),
        event(
            "URL",
            f"URL:{APP_URL}",
            url_uuid,
            APP_URL,
            timestamp=run * 100 + 4,
            parent_uuid=app_port_uuid,
            host=APP_HOST,
            port=443,
            module="http",
        ),
        event(
            "TECHNOLOGY",
            "TECHNOLOGY:app-nginx",
            f"TECHNOLOGY:{prefix}",
            {"technology": "nginx", "host": APP_HOST, "port": 443, "url": APP_URL},
            timestamp=run * 100 + 5,
            parent_uuid=url_uuid,
            host=APP_HOST,
            port=443,
            module="fingerprintx",
        ),
        event(
            "FINDING",
            "FINDING:app-login",
            f"FINDING:{prefix}-url",
            {
                "name": "Exposed login panel",
                "description": "Synthetic finding",
                "severity": "MEDIUM",
                "host": APP_HOST,
                "port": 443,
                "url": APP_URL,
            },
            timestamp=run * 100 + 5,
            parent_uuid=url_uuid,
            host=APP_HOST,
            port=443,
            module="nuclei",
        ),
        bucket(
            "example-assets",
            "aws",
            "https://example-assets.s3.amazonaws.com",
            bucket_uuid,
        ),
        bucket(
            "example-media",
            "gcp",
            "https://storage.googleapis.com/example-media",
            f"STORAGE_BUCKET:{prefix}-gcp",
        ),
        bucket(
            "example-files",
            "azure",
            "https://example-files.blob.core.windows.net/example-files",
            f"STORAGE_BUCKET:{prefix}-azure",
        ),
        event(
            "FINDING",
            "FINDING:open-bucket",
            f"FINDING:{prefix}-bucket",
            {
                "name": "Open storage bucket",
                "description": "Synthetic finding",
                "severity": "HIGH",
                "url": "https://example-assets.s3.amazonaws.com",
            },
            timestamp=run * 100 + 7,
            parent_uuid=bucket_uuid,
            module="bucket_amazon",
        ),
        scan_event(run, "FINISHED", run * 100 + 20),
    ]


def _sync_bbot(neo4j_session, update_tag: int, run: int = 1) -> None:
    cartography.intel.bbot.sync(
        neo4j_session,
        _bbot_events(run),
        "synthetic-bbot-output.json",
        update_tag,
        {"UPDATE_TAG": update_tag},
    )
    # TEST-NET addresses are not globally routable, so mark them as routable to stand
    # in for a public address.
    neo4j_session.run(
        "MATCH (ip:BbotIPAddress) SET ip.is_global = true, ip.public_ip_address = ip.ip_address",
    )


def _sync_ontology(neo4j_session, update_tag: int) -> None:
    cartography.intel.ontology.run(
        neo4j_session,
        Config(neo4j_uri="bolt://localhost:7687", update_tag=update_tag),
    )


def _create_cloud_resources(neo4j_session) -> None:
    neo4j_session.run(
        """
        CREATE (:AWSEC2Instance:ComputeInstance {
            id: 'i-web', instanceid: 'i-web', state: 'running',
            publicdnsname: $web_dns_name, publicipaddress: $web_ip,
            _ont_public_ip_address: $web_ip, lastupdated: 1
        })
        CREATE (:AWSLoadBalancerV2:LoadBalancer {
            id: $alb_id, dnsname: $alb_dns_name, lastupdated: 1
        })
        CREATE (:AWSS3Bucket:ObjectStorage {
            id: 'example-assets', name: 'example-assets', lastupdated: 1
        })
        CREATE (:GCPBucket:ObjectStorage {id: 'example-media', lastupdated: 1})
        CREATE (:AzureStorageBlobContainer:ObjectStorage {
            id: 'container-1', name: 'example-files', lastupdated: 1
        })
        """,
        web_dns_name=WEB_DNS_NAME,
        web_ip=WEB_IP,
        alb_id=ALB_ID,
        alb_dns_name=ALB_DNS_NAME,
    )


def _create_instance(
    neo4j_session,
    instance_id: str,
    publicdnsname: str,
    state: str = "running",
) -> None:
    neo4j_session.run(
        """
        CREATE (:AWSEC2Instance:ComputeInstance {
            id: $instance_id, instanceid: $instance_id,
            publicdnsname: $publicdnsname, state: $state, lastupdated: 1
        })
        """,
        instance_id=instance_id,
        publicdnsname=publicdnsname,
        state=state,
    )


def _bbot_dns_links(neo4j_session, target_label: str = "AWSEC2Instance") -> set:
    return check_rels(
        neo4j_session,
        "BbotDNSName",
        "_ont_name",
        target_label,
        "id",
        "DNS_POINTS_TO",
    )


def _bbot_ec2_rel(neo4j_session):
    return neo4j_session.run(
        """
        MATCH (:BbotDNSName)-[r:DNS_POINTS_TO]->(:AWSEC2Instance)
        RETURN r.firstseen AS firstseen, r.lastupdated AS lastupdated
        """,
    ).single()


@pytest.fixture
def bbot_and_cloud(neo4j_session):
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    _sync_bbot(neo4j_session, 101)
    _create_cloud_resources(neo4j_session)
    return neo4j_session


def test_bbot_dns_names_point_to_the_resources_they_name(bbot_and_cloud):
    # Act
    _sync_ontology(bbot_and_cloud, 101)

    # Assert
    assert _bbot_dns_links(bbot_and_cloud) == {(WEB_DNS_NAME, "i-web")}
    assert _bbot_dns_links(bbot_and_cloud, "AWSLoadBalancerV2") == {
        (ALB_DNS_NAME.lower(), ALB_ID),
    }


def test_bbot_open_ports_expose_the_resources_behind_them(bbot_and_cloud):
    # Act
    _sync_ontology(bbot_and_cloud, 101)

    # Assert: through the address, through the address a name resolves to, and
    # through the load balancer a name is a CNAME of.
    assert check_rels(
        bbot_and_cloud,
        "BbotOpenTCPPort",
        "endpoint",
        "AWSEC2Instance",
        "id",
        "EXPOSE",
    ) == {(f"{WEB_IP}:22", "i-web"), (f"{APP_HOST}:443", "i-web")}
    assert check_rels(
        bbot_and_cloud,
        "BbotOpenTCPPort",
        "endpoint",
        "AWSLoadBalancerV2",
        "id",
        "EXPOSE",
    ) == {(f"{LB_HOST}:443", ALB_ID)}


def test_bbot_urls_findings_and_technologies_attach_to_the_resource(
    bbot_and_cloud,
):
    # Act
    _sync_ontology(bbot_and_cloud, 101)

    # Assert
    assert check_rels(
        bbot_and_cloud, "BbotURL", "url", "AWSEC2Instance", "id", "EXPOSE"
    ) == {(APP_URL, "i-web")}
    assert check_rels(
        bbot_and_cloud,
        "BbotFinding",
        "finding_name",
        "AWSEC2Instance",
        "id",
        "AFFECTS",
    ) == {("Exposed login panel", "i-web")}
    assert check_rels(
        bbot_and_cloud,
        "BbotTechnology",
        "technology",
        "AWSEC2Instance",
        "id",
        "DETECTED_ON",
    ) == {("nginx", "i-web")}


def test_bbot_buckets_match_s3_and_gcs_buckets_by_name(bbot_and_cloud):
    # Act
    _sync_ontology(bbot_and_cloud, 101)

    # Assert: Azure is not matched, since container names repeat across accounts.
    assert check_rels(
        bbot_and_cloud,
        "BbotStorageBucket",
        "bucket_name",
        "ObjectStorage",
        "id",
        "MATCHES_OBJECT_STORAGE",
    ) == {("example-assets", "example-assets"), ("example-media", "example-media")}
    assert check_rels(
        bbot_and_cloud,
        "BbotFinding",
        "finding_name",
        "AWSS3Bucket",
        "id",
        "AFFECTS",
    ) == {("Open storage bucket", "example-assets")}


def test_bbot_resource_links_are_cleaned_up_when_the_resource_changes(
    bbot_and_cloud,
):
    # Arrange
    _sync_ontology(bbot_and_cloud, 101)
    bbot_and_cloud.run(
        """
        MATCH (i:AWSEC2Instance {id: 'i-web'})
        SET i.publicdnsname = '', i._ont_public_ip_address = null
        """,
    )
    bbot_and_cloud.run("MATCH (b:AWSS3Bucket) DETACH DELETE b")

    # Act
    _sync_ontology(bbot_and_cloud, 202)

    # Assert
    assert _bbot_dns_links(bbot_and_cloud) == set()
    for source_label in ("BbotOpenTCPPort", "BbotURL", "BbotFinding"):
        for rel in ("EXPOSE", "AFFECTS", "DETECTED_ON"):
            assert (
                check_rels(
                    bbot_and_cloud, source_label, "id", "AWSEC2Instance", "id", rel
                )
                == set()
            )
    assert check_rels(
        bbot_and_cloud,
        "BbotStorageBucket",
        "bucket_name",
        "ObjectStorage",
        "id",
        "MATCHES_OBJECT_STORAGE",
    ) == {("example-media", "example-media")}
    # The load balancer path is untouched.
    assert check_rels(
        bbot_and_cloud,
        "BbotOpenTCPPort",
        "endpoint",
        "AWSLoadBalancerV2",
        "id",
        "EXPOSE",
    ) == {(f"{LB_HOST}:443", ALB_ID)}


def test_bbot_resource_jobs_skip_addresses_that_are_not_globally_routable(
    neo4j_session,
):
    # Arrange: a private address that a stale PublicIP still points to an instance.
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    neo4j_session.run(
        """
        CREATE (ip:BbotIPAddress {id: 'ip-private', ip_address: '10.0.0.5', is_global: false})
        CREATE (ip)-[:HAS_OPEN_PORT]->(:BbotOpenTCPPort {id: 'port-private', endpoint: '10.0.0.5:22'})
        CREATE (ip)-[:MATCHES_PUBLIC_IP]->(p:PublicIP {id: '10.0.0.5', ip_address: '10.0.0.5'})
        CREATE (p)-[:POINTS_TO]->(:AWSEC2Instance:ComputeInstance {id: 'i-private'})
        """,
    )

    # Act
    for job in BBOT_RESOURCE_JOBS:
        run_typed_analysis_job(job, neo4j_session, {"UPDATE_TAG": 101})

    # Assert
    assert (
        check_rels(
            neo4j_session,
            "BbotOpenTCPPort",
            "id",
            "ComputeInstance",
            "id",
            "EXPOSE",
        )
        == set()
    )


@pytest.mark.parametrize("bbot_jobs_first", [True, False])
def test_bbot_dns_links_survive_ontology_sync_in_any_job_order(
    neo4j_session,
    monkeypatch,
    bbot_jobs_first,
):
    # Arrange: run the BBOT DNS jobs before or after the generic DNSRecord jobs, whose
    # cleanups must leave BBOT edges alone either way.
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    _sync_bbot(neo4j_session, 101)
    _create_cloud_resources(neo4j_session)
    bbot_jobs = tuple(
        job
        for job in DNS_RECORD_LINKING_JOBS
        if job.statements[0].effects[0].source_label == "BbotDNSName"
    )
    other_jobs = tuple(job for job in DNS_RECORD_LINKING_JOBS if job not in bbot_jobs)
    monkeypatch.setattr(
        cartography.intel.ontology.dnsrecords,
        "DNS_RECORD_LINKING_JOBS",
        bbot_jobs + other_jobs if bbot_jobs_first else other_jobs + bbot_jobs,
    )
    _sync_ontology(neo4j_session, 101)
    first_seen = _bbot_ec2_rel(neo4j_session)["firstseen"]

    # Act
    _sync_ontology(neo4j_session, 202)

    # Assert: the edge is refreshed in place, not deleted and recreated.
    rel = _bbot_ec2_rel(neo4j_session)
    assert rel["firstseen"] == first_seen
    assert rel["lastupdated"] == 202


def test_sync_still_cleans_up_provider_dns_record_to_ec2_links(neo4j_session):
    # Arrange: a provider record and a BBOT name both point to the instance.
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    _sync_bbot(neo4j_session, 101)
    _create_cloud_resources(neo4j_session)
    neo4j_session.run(
        """
        CREATE (:CloudflareDNSRecord:DNSRecord {
            id: 'www.example.com+CNAME', _ont_name: 'www.example.com',
            _ont_value: $value, lastupdated: 1
        })
        """,
        value=WEB_DNS_NAME,
    )
    _sync_ontology(neo4j_session, 101)
    assert _provider_dns_links(neo4j_session) == {("www.example.com+CNAME", "i-web")}

    # Act: the provider record stops pointing to the instance.
    neo4j_session.run(
        "MATCH (d:CloudflareDNSRecord) SET d._ont_value = $value",
        value=OTHER_DNS_NAME,
    )
    _sync_ontology(neo4j_session, 202)

    # Assert
    assert _provider_dns_links(neo4j_session) == set()
    assert _bbot_dns_links(neo4j_session) == {(WEB_DNS_NAME, "i-web")}


def test_sync_skips_ec2_instance_with_different_public_dns_name(neo4j_session):
    # Arrange
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    _sync_bbot(neo4j_session, 101)
    _create_instance(neo4j_session, "i-other", OTHER_DNS_NAME)

    # Act
    _sync_ontology(neo4j_session, 101)

    # Assert
    assert _bbot_dns_links(neo4j_session) == set()


def test_sync_links_stopped_instance_that_keeps_its_public_dns_name(neo4j_session):
    # Arrange: AWS clears the public DNS name when an instance loses its public IP, so
    # a stopped instance that still has one holds an Elastic IP and owns the name. A
    # terminated instance never has one.
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    _sync_bbot(neo4j_session, 101)
    _create_instance(neo4j_session, "i-stopped", WEB_DNS_NAME, state="stopped")
    _create_instance(neo4j_session, "i-terminated", "", state="terminated")

    # Act
    _sync_ontology(neo4j_session, 101)

    # Assert
    assert _bbot_dns_links(neo4j_session) == {(WEB_DNS_NAME, "i-stopped")}


def test_bbot_dns_matches_seek_dns_record_name_index(neo4j_session):
    # Arrange
    neo4j_session.run(
        "CREATE INDEX dns_record_ont_name IF NOT EXISTS "
        "FOR (n:DNSRecord) ON (n._ont_name)"
    ).consume()
    neo4j_session.run("CALL db.awaitIndexes()").consume()
    matches = [
        statement.match
        for job in DNS_RECORD_LINKING_JOBS
        for statement in job.statements
        if "WHERE dns:BbotDNSName" in statement.match
    ]

    # Act
    plans = {
        match: neo4j_session.run(f"EXPLAIN {match} RETURN dns, target").consume().plan
        for match in matches
    }

    # Assert: one match per hostname property in DNS_RECORD_TARGETS.
    assert len(plans) == 17
    for match, plan in plans.items():
        assert any(
            "DNSRecord" in seek and "_ont_name" in seek for seek in _index_seeks(plan)
        ), match


def test_bbot_bucket_matches_seek_bucket_id_index(neo4j_session):
    # Arrange
    ensure_indexes(neo4j_session, S3BucketSchema())
    ensure_indexes(neo4j_session, GCPBucketSchema())
    neo4j_session.run("CALL db.awaitIndexes()").consume()

    for statement, label in zip(
        BBOT_STORAGE_BUCKET_MATCHES_OBJECT_STORAGE.statements,
        ("AWSS3Bucket", "GCPBucket"),
    ):
        # Act
        plan = (
            neo4j_session.run(f"EXPLAIN {statement.match} RETURN bucket, target")
            .consume()
            .plan
        )

        # Assert
        assert any(label in seek and "id" in seek for seek in _index_seeks(plan))


def test_bbot_resource_traversals_start_from_bbot_nodes(neo4j_session):
    # The port, URL, finding and technology matches have no property to seek on. They
    # start from a BBOT label and only expand relationships from there.
    matches = [
        statement.match
        for job in BBOT_RESOURCE_JOBS
        if job is not BBOT_STORAGE_BUCKET_MATCHES_OBJECT_STORAGE
        for statement in job.statements
    ]
    assert len(matches) == 74

    for match in matches:
        # Act
        plan = neo4j_session.run(f"EXPLAIN {match} RETURN target").consume().plan

        # Assert
        operators = _operator_names(plan)
        assert "AllNodesScan" not in operators, match
        assert "CartesianProduct" not in operators, match


def _provider_dns_links(neo4j_session) -> set:
    return check_rels(
        neo4j_session,
        "CloudflareDNSRecord",
        "id",
        "AWSEC2Instance",
        "id",
        "DNS_POINTS_TO",
    )


def _operator_names(plan) -> set[str]:
    names = {plan["operatorType"].split("@")[0]}
    for child in plan.get("children", []):
        names |= _operator_names(child)
    return names


def _index_seeks(plan) -> list[str]:
    seeks = []
    if plan["operatorType"].split("@")[0] == "NodeIndexSeek":
        seeks.append(plan["args"].get("Details", ""))
    for child in plan.get("children", []):
        seeks.extend(_index_seeks(child))
    return seeks
