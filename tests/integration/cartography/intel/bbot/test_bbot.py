import time

import cartography.intel.ontology.publicips
from cartography.analysis.ontology.analysis import BBOT_DNS_MATCHES_PROVIDER
from cartography.analysis.ontology.analysis import BBOT_IP_MATCHES_PUBLIC_IP
from cartography.intel.bbot import sync
from cartography.util import run_typed_analysis_job
from tests.data.bbot.events import events as make_events
from tests.data.bbot.events import IP_ADDRESS
from tests.data.bbot.events import IP_ID
from tests.data.bbot.events import SCAN_ID
from tests.data.bbot.events import scan_only_events
from tests.integration.util import check_nodes
from tests.integration.util import check_rels


def _sync(neo4j_session, events: list[dict], update_tag: int) -> None:
    sync(
        neo4j_session,
        events,
        "synthetic-bbot-output.json",
        update_tag,
        {"UPDATE_TAG": update_tag},
    )


def _node_counts(neo4j_session) -> dict[str, int]:
    return {
        row["event_type"]: row["count"]
        for row in neo4j_session.run(
            """
            MATCH (n)
            WHERE n.event_type IS NOT NULL
            RETURN n.event_type AS event_type, count(n) AS count
            """,
        )
    }


def test_stable_identities_merge_and_stale_identities_are_cleaned(
    neo4j_session,
) -> None:
    # Arrange
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    first_events = make_events(1)

    # Act
    _sync(neo4j_session, first_events, 101)

    # Assert
    expected_counts = {
        "ASN": 1,
        "DNS_NAME": 1,
        "EMAIL_ADDRESS": 1,
        "FINDING": 1,
        "IP_ADDRESS": 1,
        "IP_RANGE": 1,
        "OPEN_TCP_PORT": 1,
        "ORG_STUB": 1,
        "SCAN": 1,
        "SOCIAL": 1,
        "STORAGE_BUCKET": 1,
        "TECHNOLOGY": 1,
        "URL": 1,
    }
    assert _node_counts(neo4j_session) == expected_counts

    first_dns = neo4j_session.run(
        """
        MATCH (dns:BbotDNSName {id: 'DNS_NAME:app'})
              -[observed:OBSERVED_IN]->(:BbotScan {id: $scan_id})
        RETURN elementId(dns) AS element_id,
               dns.firstseen AS firstseen,
               dns.lastupdated AS lastupdated,
               dns.occurrence_count AS occurrence_count,
               dns.occurrence_uuids AS occurrence_uuids,
               dns.tags AS tags,
               dns.modules AS modules,
               dns._ont_name AS ont_name,
               observed.firstseen AS rel_firstseen,
               observed.lastupdated AS rel_lastupdated
        """,
        scan_id=SCAN_ID,
    ).single()
    first_finding = neo4j_session.run(
        """
        MATCH (finding:BbotFinding)
        RETURN elementId(finding) AS element_id,
               finding.id AS id,
               finding.firstseen AS firstseen
        """,
    ).single()
    first_email = neo4j_session.run(
        """
        MATCH (email:BbotEmailAddress {id: 'EMAIL_ADDRESS:stable-security'})
        RETURN email.firstseen AS firstseen
        """,
    ).single()
    assert first_dns["lastupdated"] == 101
    assert first_dns["rel_lastupdated"] == 101
    assert first_dns["occurrence_count"] == 2
    assert first_dns["occurrence_uuids"] == [
        "DNS_NAME:run-1-one",
        "DNS_NAME:run-1-two",
    ]
    assert first_dns["ont_name"] == "app.example.test"

    # Act: the second report has new occurrence UUIDs, timestamps, tags, modules,
    # finding text, severity, confidence, and bucket endpoint URL.
    _sync(neo4j_session, make_events(2), 202)

    # Assert: stable assets and relationships were merged in place.
    assert _node_counts(neo4j_session) == expected_counts
    second_dns = neo4j_session.run(
        """
        MATCH (dns:BbotDNSName {id: 'DNS_NAME:app'})
              -[observed:OBSERVED_IN]->(:BbotScan {id: $scan_id})
        RETURN elementId(dns) AS element_id,
               dns.firstseen AS firstseen,
               dns.lastupdated AS lastupdated,
               dns.occurrence_count AS occurrence_count,
               dns.occurrence_uuids AS occurrence_uuids,
               dns.tags AS tags,
               dns.modules AS modules,
               observed.firstseen AS rel_firstseen,
               observed.lastupdated AS rel_lastupdated
        """,
        scan_id=SCAN_ID,
    ).single()
    second_finding = neo4j_session.run(
        """
        MATCH (finding:BbotFinding)
        RETURN elementId(finding) AS element_id,
               finding.id AS id,
               finding.firstseen AS firstseen,
               finding.lastupdated AS lastupdated,
               finding.severity AS severity,
               finding.confidence AS confidence,
               finding.description AS description
        """,
    ).single()
    assert second_dns["element_id"] == first_dns["element_id"]
    assert second_dns["firstseen"] == first_dns["firstseen"]
    assert second_dns["lastupdated"] == 202
    assert second_dns["rel_firstseen"] == first_dns["rel_firstseen"]
    assert second_dns["rel_lastupdated"] == 202
    assert second_dns["occurrence_count"] == 2
    assert second_dns["occurrence_uuids"] == [
        "DNS_NAME:run-2-one",
        "DNS_NAME:run-2-two",
    ]
    assert second_dns["tags"] == ["a-record", "in-scope", "run-2"]
    assert second_dns["modules"] == ["dnsresolve", "synthetic-module-2"]
    assert second_finding["element_id"] == first_finding["element_id"]
    assert second_finding["id"] == first_finding["id"]
    assert second_finding["firstseen"] == first_finding["firstseen"]
    assert second_finding["lastupdated"] == 202
    assert second_finding["severity"] == "HIGH"
    assert second_finding["confidence"] == "CONFIRMED"
    assert second_finding["description"] == "Explanation from run 2"

    expected_relationships = {
        ("BbotFinding", "BbotURL", "AFFECTS"): {
            (first_finding["id"], "URL:app-admin"),
        },
        ("BbotIPAddress", "BbotASN", "ANNOUNCED_BY"): {
            (IP_ID, "ASN:stable-15169"),
        },
        ("BbotTechnology", "BbotURL", "DETECTED_ON"): {
            ("TECHNOLOGY:app-443-nginx", "URL:app-admin"),
        },
        ("BbotDNSName", "BbotOpenTCPPort", "HAS_OPEN_PORT"): {
            ("DNS_NAME:app", "OPEN_TCP_PORT:app-443"),
        },
        ("BbotURL", "BbotOpenTCPPort", "HOSTED_BY"): {
            ("URL:app-admin", "OPEN_TCP_PORT:app-443"),
        },
        ("BbotDNSName", "BbotIPAddress", "RESOLVES_TO"): {
            ("DNS_NAME:app", IP_ID),
        },
    }
    for (
        source_label,
        target_label,
        relationship,
    ), expected in expected_relationships.items():
        assert (
            check_rels(
                neo4j_session,
                source_label,
                "id",
                target_label,
                "id",
                relationship,
            )
            == expected
        )

    # Act: true identity components change, and the email disappears.
    _sync(
        neo4j_session,
        make_events(3, changed_identities=True, include_email=False),
        303,
    )

    # Assert: replacements exist and old identities were removed by cleanup.
    assert (
        neo4j_session.run(
            """
            MATCH (n)
            WHERE n.id IN [
                'DNS_NAME:app',
                'OPEN_TCP_PORT:app-443',
                'URL:app-admin',
                'TECHNOLOGY:app-443-nginx',
                'EMAIL_ADDRESS:stable-security'
            ]
            RETURN count(n) AS count
            """,
        ).single()["count"]
        == 0
    )
    assert (
        neo4j_session.run(
            """
            MATCH (dns:BbotDNSName {id: 'DNS_NAME:api'}),
                  (port:BbotOpenTCPPort {id: 'OPEN_TCP_PORT:api-8443'}),
                  (url:BbotURL {id: 'URL:api-admin'}),
                  (technology:BbotTechnology {id: 'TECHNOLOGY:api-8443-nginx'})
            RETURN count(*) AS count
            """,
        ).single()["count"]
        == 1
    )
    assert _node_counts(neo4j_session)["FINDING"] == 1
    assert _node_counts(neo4j_session)["STORAGE_BUCKET"] == 1
    assert _node_counts(neo4j_session)["SOCIAL"] == 1
    assert "EMAIL_ADDRESS" not in _node_counts(neo4j_session)

    # Act: the missing email reappears in a later report.
    time.sleep(0.01)
    _sync(neo4j_session, make_events(4, changed_identities=True), 404)

    # Assert: it was recreated, with a new firstseen timestamp.
    recreated_email = neo4j_session.run(
        """
        MATCH (email:BbotEmailAddress {id: 'EMAIL_ADDRESS:stable-security'})
        RETURN email.firstseen AS firstseen, email.lastupdated AS lastupdated
        """,
    ).single()
    assert recreated_email["firstseen"] > first_email["firstseen"]
    assert recreated_email["lastupdated"] == 404


def test_bbot_dns_and_ip_correlate_and_public_ip_lifecycle(
    neo4j_session,
) -> None:
    # Arrange
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    _sync(neo4j_session, make_events(1), 101)
    neo4j_session.run(
        """
        CREATE (:AWSDNSRecord:DNSRecord {
            id: 'provider-dns-record',
            _ont_name: 'APP.EXAMPLE.TEST'
        })
        """,
    )

    # Act
    run_typed_analysis_job(
        BBOT_DNS_MATCHES_PROVIDER,
        neo4j_session,
        {"UPDATE_TAG": 101},
    )
    cartography.intel.ontology.publicips.sync(
        neo4j_session,
        101,
        {"UPDATE_TAG": 101},
    )
    run_typed_analysis_job(
        BBOT_IP_MATCHES_PUBLIC_IP,
        neo4j_session,
        {"UPDATE_TAG": 101},
    )

    # Assert
    assert check_nodes(neo4j_session, "PublicIP", ["id"]) == {(IP_ADDRESS,)}
    assert check_rels(
        neo4j_session,
        "BbotDNSName",
        "id",
        "AWSDNSRecord",
        "id",
        "MATCHES_DNS_RECORD",
    ) == {("DNS_NAME:app", "provider-dns-record")}
    assert check_rels(
        neo4j_session,
        "BbotIPAddress",
        "id",
        "PublicIP",
        "id",
        "MATCHES_PUBLIC_IP",
    ) == {(IP_ID, IP_ADDRESS)}
    first_public_ip = neo4j_session.run(
        """
        MATCH (ip:PublicIP {id: $ip})
        RETURN elementId(ip) AS element_id,
               ip.firstseen AS firstseen,
               ip.lastupdated AS lastupdated
        """,
        ip=IP_ADDRESS,
    ).single()
    assert first_public_ip["lastupdated"] == 101

    # Arrange: a provider now observes the same IP, while the next BBOT scan does not.
    neo4j_session.run(
        """
        CREATE (:AWSElasticIPAddress {
            id: 'provider-eip',
            public_ip: $ip
        })
        """,
        ip=IP_ADDRESS,
    )

    # Act
    _sync(neo4j_session, scan_only_events(2), 202)
    cartography.intel.ontology.publicips.sync(
        neo4j_session,
        202,
        {"UPDATE_TAG": 202},
    )

    # Assert: canonical identity is preserved while another source still observes it.
    assert check_nodes(neo4j_session, "BbotIPAddress", ["id"]) == set()
    second_public_ip = neo4j_session.run(
        """
        MATCH (ip:PublicIP {id: $ip})
        RETURN elementId(ip) AS element_id,
               ip.firstseen AS firstseen,
               ip.lastupdated AS lastupdated
        """,
        ip=IP_ADDRESS,
    ).single()
    assert second_public_ip["element_id"] == first_public_ip["element_id"]
    assert second_public_ip["firstseen"] == first_public_ip["firstseen"]
    assert second_public_ip["lastupdated"] == 202

    # Arrange: remove the final source observation.
    neo4j_session.run(
        "MATCH (ip:AWSElasticIPAddress {id: 'provider-eip'}) DETACH DELETE ip",
    )

    # Act
    cartography.intel.ontology.publicips.sync(
        neo4j_session,
        303,
        {"UPDATE_TAG": 303},
    )

    # Assert
    assert check_nodes(neo4j_session, "PublicIP", ["id"]) == set()
