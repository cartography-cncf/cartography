import cartography.intel.bbot
import cartography.intel.ontology.dnsrecords
from cartography.analysis.ontology.analysis import BBOT_DNS_POINTS_TO_EC2_INSTANCE
from cartography.client.core.tx import ensure_indexes
from cartography.models.aws.ec2.instances import EC2InstanceSchema
from tests.data.bbot.events import event
from tests.data.bbot.events import scan_event
from tests.integration.util import check_rels

INSTANCE_DNS_NAME = "ec2-192-0-2-10.compute-1.amazonaws.com"
OTHER_DNS_NAME = "ec2-198-51-100-20.compute-1.amazonaws.com"


def _bbot_events(run: int, hostname: str) -> list[dict]:
    scan_uuid = f"SCAN:run-{run}-starting"
    return [
        scan_event(run, "STARTING", run * 100),
        event(
            "DNS_NAME",
            f"DNS_NAME:{hostname}",
            f"DNS_NAME:run-{run}",
            # BBOT reports what it resolved; ingestion normalizes the ontology name.
            f"{hostname.upper()}.",
            timestamp=run * 100 + 1,
            parent_uuid=scan_uuid,
            host=hostname,
            resolved_hosts=["192.0.2.10"],
            module="dnsresolve",
            scope_distance=0,
        ),
        scan_event(run, "FINISHED", run * 100 + 20),
    ]


def _sync_bbot(neo4j_session, hostname: str, update_tag: int, run: int = 1) -> None:
    cartography.intel.bbot.sync(
        neo4j_session,
        _bbot_events(run, hostname),
        "synthetic-bbot-output.json",
        update_tag,
        {"UPDATE_TAG": update_tag},
    )


def _sync_ontology_dns(neo4j_session, update_tag: int) -> None:
    cartography.intel.ontology.dnsrecords.sync(
        neo4j_session,
        update_tag,
        {"UPDATE_TAG": update_tag},
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
            id: $instance_id,
            instanceid: $instance_id,
            publicdnsname: $publicdnsname,
            state: $state,
            lastupdated: 1
        })
        """,
        instance_id=instance_id,
        publicdnsname=publicdnsname,
        state=state,
    )


def _bbot_ec2_links(neo4j_session) -> set[tuple[str, str]]:
    return check_rels(
        neo4j_session,
        "BbotDNSName",
        "_ont_name",
        "AWSEC2Instance",
        "id",
        "DNS_POINTS_TO",
    )


def test_sync_links_bbot_dns_name_to_ec2_instance_and_keeps_it_across_runs(
    neo4j_session,
):
    # Arrange
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    _sync_bbot(neo4j_session, INSTANCE_DNS_NAME, 101)
    _create_instance(neo4j_session, "i-01", INSTANCE_DNS_NAME)

    # Act
    _sync_ontology_dns(neo4j_session, 101)

    # Assert
    assert _bbot_ec2_links(neo4j_session) == {(INSTANCE_DNS_NAME, "i-01")}
    first_seen = neo4j_session.run(
        "MATCH (:BbotDNSName)-[r:DNS_POINTS_TO]->(:AWSEC2Instance) RETURN r.firstseen AS f",
    ).single()["f"]

    # Act: the generic DNSRecord to AWSEC2Instance cleanup runs again with a new tag.
    _sync_ontology_dns(neo4j_session, 202)

    # Assert: the edge is refreshed in place, not deleted and recreated.
    rel = neo4j_session.run(
        """
        MATCH (:BbotDNSName)-[r:DNS_POINTS_TO]->(:AWSEC2Instance)
        RETURN r.firstseen AS firstseen, r.lastupdated AS lastupdated
        """,
    ).single()
    assert rel["firstseen"] == first_seen
    assert rel["lastupdated"] == 202


def test_sync_skips_ec2_instance_with_different_public_dns_name(neo4j_session):
    # Arrange
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    _sync_bbot(neo4j_session, INSTANCE_DNS_NAME, 101)
    _create_instance(neo4j_session, "i-02", OTHER_DNS_NAME)

    # Act
    _sync_ontology_dns(neo4j_session, 101)

    # Assert
    assert _bbot_ec2_links(neo4j_session) == set()


def test_sync_removes_link_when_instance_releases_public_dns_name(neo4j_session):
    # Arrange
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    _sync_bbot(neo4j_session, INSTANCE_DNS_NAME, 101)
    _create_instance(neo4j_session, "i-01", INSTANCE_DNS_NAME)

    # Act
    _sync_ontology_dns(neo4j_session, 101)

    # Assert
    assert _bbot_ec2_links(neo4j_session) == {(INSTANCE_DNS_NAME, "i-01")}

    # Arrange: AWS returns an empty PublicDnsName once the instance loses its public IP.
    neo4j_session.run(
        "MATCH (i:AWSEC2Instance {id: 'i-01'}) SET i.publicdnsname = ''",
    )

    # Act
    _sync_ontology_dns(neo4j_session, 202)

    # Assert
    assert _bbot_ec2_links(neo4j_session) == set()


def test_sync_links_stopped_instance_that_keeps_its_public_dns_name(
    neo4j_session,
):
    # Arrange: a stopped instance with an Elastic IP keeps its public DNS name; a
    # terminated instance never has one.
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    _sync_bbot(neo4j_session, INSTANCE_DNS_NAME, 101)
    _create_instance(neo4j_session, "i-stopped", INSTANCE_DNS_NAME, state="stopped")
    _create_instance(neo4j_session, "i-terminated", "", state="terminated")

    # Act
    _sync_ontology_dns(neo4j_session, 101)

    # Assert
    assert _bbot_ec2_links(neo4j_session) == {(INSTANCE_DNS_NAME, "i-stopped")}


def test_bbot_ec2_match_seeks_public_dns_name_index(neo4j_session):
    # Arrange
    ensure_indexes(neo4j_session, EC2InstanceSchema())
    neo4j_session.run("CALL db.awaitIndexes()").consume()
    match = BBOT_DNS_POINTS_TO_EC2_INSTANCE.statements[0].match

    # Act
    plan = neo4j_session.run(f"EXPLAIN {match} RETURN dns, target").consume().plan

    # Assert
    seeks = _index_seeks(plan)
    assert any("AWSEC2Instance" in seek and "publicdnsname" in seek for seek in seeks)


def _index_seeks(plan) -> list[str]:
    seeks = []
    if plan["operatorType"].split("@")[0] == "NodeIndexSeek":
        seeks.append(plan["args"].get("Details", ""))
    for child in plan.get("children", []):
        seeks.extend(_index_seeks(child))
    return seeks
