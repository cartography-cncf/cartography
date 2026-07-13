from cartography.client.core.tx import read_list_of_dicts_tx
from cartography.rules.data.rules.compute_instance_exposed import (
    _scaleway_instance_internet_exposed,
)
from cartography.rules.data.rules.compute_instance_exposed import (
    _scaleway_instance_pat_exposed,
)


def _reset_graph(neo4j_session) -> None:
    neo4j_session.run("MATCH (n) DETACH DELETE n")


def _seed_scaleway_exposure(neo4j_session) -> None:
    # - direct: running instance with a public IP + SG accepting 0.0.0.0/0 on 22
    # - pat: private instance (no public IP) reachable via a gateway PAT rule
    #        forwarding to its private IP on port 22
    # - pat_high_port: private instance whose PAT rule targets a non-management
    #        port (8080) -> must NOT be flagged
    # - safe: private instance with no exposure at all
    neo4j_session.run(
        """
        CREATE (prj:ScalewayProject {id: 'proj-1'})

        CREATE (direct:ScalewayInstance {id: 'i-direct', name: 'direct',
            state: 'running', private_ip: '172.16.0.5', public_ips: ['ip-1']})
        CREATE (sg:ScalewaySecurityGroup {id: 'sg-open'})
        CREATE (rule:ScalewaySecurityGroupRule {id: 'r-open', direction: 'inbound',
            action: 'accept', ip_range: '0.0.0.0/0', protocol: 'tcp',
            dest_port_from: 22, dest_port_to: 22})
        CREATE (direct)-[:MEMBER_OF_SCALEWAY_SECURITY_GROUP]->(sg)
        CREATE (rule)-[:MEMBER_OF_SCALEWAY_SECURITY_GROUP]->(sg)

        CREATE (pat:ScalewayInstance {id: 'i-pat', name: 'pat',
            state: 'running', private_ip: '172.16.0.10', public_ips: []})
        CREATE (pat_high:ScalewayInstance {id: 'i-pat-high', name: 'pat-high',
            state: 'running', private_ip: '172.16.0.11', public_ips: []})
        CREATE (safe:ScalewayInstance {id: 'i-safe', name: 'safe',
            state: 'running', private_ip: '172.16.0.99', public_ips: []})

        CREATE (gw:ScalewayPublicGateway {id: 'gw-1', name: 'gw'})
        CREATE (patrule:ScalewayPublicGatewayPatRule {id: 'pat-22',
            public_port: 2222, private_ip: '172.16.0.10', private_port: 22,
            protocol: 'tcp'})
        CREATE (patrule_high:ScalewayPublicGatewayPatRule {id: 'pat-8080',
            public_port: 8080, private_ip: '172.16.0.11', private_port: 8080,
            protocol: 'tcp'})
        CREATE (gw)-[:HAS]->(patrule)
        CREATE (gw)-[:HAS]->(patrule_high)

        MERGE (prj)-[:RESOURCE]->(direct)
        MERGE (prj)-[:RESOURCE]->(sg)
        MERGE (prj)-[:RESOURCE]->(pat)
        MERGE (prj)-[:RESOURCE]->(pat_high)
        MERGE (prj)-[:RESOURCE]->(safe)
        MERGE (prj)-[:RESOURCE]->(gw)
        """
    )


def test_scaleway_direct_public_ip_exposure(neo4j_session) -> None:
    _reset_graph(neo4j_session)
    _seed_scaleway_exposure(neo4j_session)

    findings = neo4j_session.execute_read(
        read_list_of_dicts_tx, _scaleway_instance_internet_exposed.cypher_query
    )

    # Only the instance with a direct public IP + permissive SG is flagged.
    assert {(f["instance_id"], f["port"]) for f in findings} == {("i-direct", 22)}


def test_scaleway_pat_backed_exposure(neo4j_session) -> None:
    _reset_graph(neo4j_session)
    _seed_scaleway_exposure(neo4j_session)

    findings = neo4j_session.execute_read(
        read_list_of_dicts_tx, _scaleway_instance_pat_exposed.cypher_query
    )

    # The private instance reachable via a PAT rule on port 22 is flagged;
    # the PAT rule targeting a non-management port (8080) is not, and the
    # direct-public-IP instance is covered by the other fact, not this one.
    assert {(f["instance_id"], f["port"]) for f in findings} == {("i-pat", 22)}
    assert findings[0]["security_group"] == "gw-1"
