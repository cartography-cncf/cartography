from cartography.util import run_analysis_job

TEST_UPDATE_TAG = 123456789


def test_link_tailscale_devices_to_cloud_instances(neo4j_session):
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    stale_tag = TEST_UPDATE_TAG - 1

    # Arrange
    neo4j_session.run(
        """
        CREATE (:TailscaleDevice {
            id: 'ts-ec2-host',
            hostname: 'ip-10-0-0-5',
            name: 'ip-10-0-0-5.example.ts.net',
            lastupdated: $update_tag
        })
        CREATE (:EC2Instance:ComputeInstance {
            id: 'i-host-match',
            publicdnsname: 'ip-10-0-0-5.ec2.internal',
            publicipaddress: '198.51.100.10',
            lastupdated: $update_tag
        })

        CREATE (:TailscaleDevice {
            id: 'ts-gcp-ip',
            hostname: 'unrelated-host',
            name: 'unrelated-host.example.ts.net',
            client_connectivity_endpoints: ['203.0.113.10:41641'],
            lastupdated: $update_tag
        })
        CREATE (:GCPInstance:ComputeInstance {
            id: 'projects/test/zones/us-central1-a/instances/gcp-instance',
            instancename: 'gcp-instance',
            hostname: 'gcp-instance.c.test.internal',
            public_ip: '203.0.113.10',
            lastupdated: $update_tag
        })

        CREATE (:TailscaleDevice {
            id: 'ts-stale',
            hostname: 'stale-host',
            lastupdated: $update_tag
        })-[stale:IS_INSTANCE]->(:EC2Instance:ComputeInstance {
            id: 'i-stale',
            publicdnsname: 'different-host.ec2.internal',
            lastupdated: $update_tag
        })
        SET stale.lastupdated = $stale_tag
        """,
        update_tag=TEST_UPDATE_TAG,
        stale_tag=stale_tag,
    )

    # Act
    run_analysis_job(
        "tailscale_device_instance_linking.json",
        neo4j_session,
        {"UPDATE_TAG": TEST_UPDATE_TAG},
    )

    # Assert
    result = neo4j_session.run(
        """
        MATCH (device:TailscaleDevice)-[:IS_INSTANCE]->(instance:ComputeInstance)
        RETURN device.id AS device_id, instance.id AS instance_id
        """
    )
    assert {(r["device_id"], r["instance_id"]) for r in result} == {
        ("ts-ec2-host", "i-host-match"),
        ("ts-gcp-ip", "projects/test/zones/us-central1-a/instances/gcp-instance"),
    }


def test_tailscale_device_instance_linking_skips_ambiguous_hostnames(
    neo4j_session,
):
    neo4j_session.run("MATCH (n) DETACH DELETE n")

    # Arrange
    neo4j_session.run(
        """
        CREATE (:TailscaleDevice {
            id: 'ts-duplicate',
            hostname: 'shared-host',
            lastupdated: $update_tag
        })
        CREATE (:EC2Instance:ComputeInstance {
            id: 'i-duplicate-a',
            publicdnsname: 'shared-host.ec2.internal',
            lastupdated: $update_tag
        })
        CREATE (:GCPInstance:ComputeInstance {
            id: 'projects/test/zones/us-central1-a/instances/shared-host',
            instancename: 'shared-host',
            lastupdated: $update_tag
        })
        """,
        update_tag=TEST_UPDATE_TAG,
    )

    # Act
    run_analysis_job(
        "tailscale_device_instance_linking.json",
        neo4j_session,
        {"UPDATE_TAG": TEST_UPDATE_TAG},
    )

    # Assert
    count = neo4j_session.run(
        """
        MATCH (:TailscaleDevice)-[r:IS_INSTANCE]->(:ComputeInstance)
        RETURN count(r) AS count
        """
    ).single()["count"]
    assert count == 0


def test_tailscale_device_instance_linking_requires_one_to_one_final_match(
    neo4j_session,
):
    neo4j_session.run("MATCH (n) DETACH DELETE n")

    # Arrange
    neo4j_session.run(
        """
        CREATE (:TailscaleDevice {
            id: 'ts-conflicting',
            hostname: 'ec2-host',
            name: 'gcp-host.example.ts.net',
            lastupdated: $update_tag
        })
        CREATE (:EC2Instance:ComputeInstance {
            id: 'i-conflicting',
            publicdnsname: 'ec2-host.ec2.internal',
            lastupdated: $update_tag
        })
        CREATE (:GCPInstance:ComputeInstance {
            id: 'projects/test/zones/us-central1-a/instances/gcp-host',
            instancename: 'gcp-host',
            lastupdated: $update_tag
        })

        CREATE (:TailscaleDevice {
            id: 'ts-shared-a',
            hostname: 'shared-instance',
            lastupdated: $update_tag
        })
        CREATE (:TailscaleDevice {
            id: 'ts-shared-b',
            hostname: 'shared-instance',
            lastupdated: $update_tag
        })
        CREATE (:EC2Instance:ComputeInstance {
            id: 'i-shared',
            publicdnsname: 'shared-instance.ec2.internal',
            lastupdated: $update_tag
        })
        """,
        update_tag=TEST_UPDATE_TAG,
    )

    # Act
    run_analysis_job(
        "tailscale_device_instance_linking.json",
        neo4j_session,
        {"UPDATE_TAG": TEST_UPDATE_TAG},
    )

    # Assert
    count = neo4j_session.run(
        """
        MATCH (:TailscaleDevice)-[r:IS_INSTANCE]->(:ComputeInstance)
        RETURN count(r) AS count
        """
    ).single()["count"]
    assert count == 0


def test_tailscale_device_instance_linking_matches_ec2_private_ip(
    neo4j_session,
):
    neo4j_session.run("MATCH (n) DETACH DELETE n")

    # Arrange
    neo4j_session.run(
        """
        CREATE (:TailscaleDevice {
            id: 'ts-private-ip',
            client_connectivity_endpoints: ['10.0.0.5:41641'],
            lastupdated: $update_tag
        })
        CREATE (:EC2Instance:ComputeInstance {
            id: 'i-private-ip',
            privateipaddress: '10.0.0.5',
            lastupdated: $update_tag
        })
        """,
        update_tag=TEST_UPDATE_TAG,
    )

    # Act
    run_analysis_job(
        "tailscale_device_instance_linking.json",
        neo4j_session,
        {"UPDATE_TAG": TEST_UPDATE_TAG},
    )

    # Assert
    result = neo4j_session.run(
        """
        MATCH (device:TailscaleDevice)-[:IS_INSTANCE]->(instance:EC2Instance)
        RETURN device.id AS device_id, instance.id AS instance_id
        """
    ).single()
    assert result["device_id"] == "ts-private-ip"
    assert result["instance_id"] == "i-private-ip"


def test_tailscale_device_instance_linking_keeps_valid_stale_source_edges(
    neo4j_session,
):
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    stale_tag = TEST_UPDATE_TAG - 1

    # Arrange
    neo4j_session.run(
        """
        CREATE (:TailscaleDevice {
            id: 'ts-old-source',
            client_connectivity_endpoints: ['10.0.0.6:41641'],
            lastupdated: $stale_tag
        })-[old_edge:IS_INSTANCE]->(:EC2Instance:ComputeInstance {
            id: 'i-old-source',
            privateipaddress: '10.0.0.6',
            lastupdated: $stale_tag
        })
        SET old_edge.lastupdated = $stale_tag
        """,
        stale_tag=stale_tag,
    )

    # Act
    run_analysis_job(
        "tailscale_device_instance_linking.json",
        neo4j_session,
        {"UPDATE_TAG": TEST_UPDATE_TAG},
    )

    # Assert
    result = neo4j_session.run(
        """
        MATCH (:TailscaleDevice {id: 'ts-old-source'})
              -[r:IS_INSTANCE]->
              (:EC2Instance {id: 'i-old-source'})
        RETURN r.lastupdated AS lastupdated
        """
    ).single()
    assert result["lastupdated"] == TEST_UPDATE_TAG


def test_tailscale_device_instance_linking_skips_ambiguous_private_ips(
    neo4j_session,
):
    neo4j_session.run("MATCH (n) DETACH DELETE n")

    # Arrange
    neo4j_session.run(
        """
        CREATE (:TailscaleDevice {
            id: 'ts-overlapping-private-ip',
            client_connectivity_endpoints: ['10.0.0.7:41641'],
            lastupdated: $update_tag
        })
        CREATE (:EC2Instance:ComputeInstance {
            id: 'i-overlap-a',
            privateipaddress: '10.0.0.7',
            lastupdated: $update_tag
        })
        CREATE (:GCPInstance:ComputeInstance {
            id: 'projects/test/zones/us-central1-a/instances/i-overlap-b',
            private_ip: '10.0.0.7',
            lastupdated: $update_tag
        })
        """,
        update_tag=TEST_UPDATE_TAG,
    )

    # Act
    run_analysis_job(
        "tailscale_device_instance_linking.json",
        neo4j_session,
        {"UPDATE_TAG": TEST_UPDATE_TAG},
    )

    # Assert
    count = neo4j_session.run(
        """
        MATCH (:TailscaleDevice)-[r:IS_INSTANCE]->(:ComputeInstance)
        RETURN count(r) AS count
        """
    ).single()["count"]
    assert count == 0
