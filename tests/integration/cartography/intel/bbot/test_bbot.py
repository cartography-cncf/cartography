import time
from typing import Any

from cartography.analysis.ontology.analysis import BBOT_DNS_MATCHES_PROVIDER
from cartography.analysis.ontology.analysis import BBOT_IP_MATCHES_PUBLIC_IP
from cartography.intel.bbot import sync
from cartography.util import run_typed_analysis_job

SCAN_ID = "SCAN:stable-synthetic-scan"
IP_ID = "IP_ADDRESS:stable-google-dns"
IP_ADDRESS = "8.8.8.8"


def _event(
    event_type: str,
    event_id: str,
    uuid: str,
    data: str | dict,
    *,
    timestamp: float,
    parent_uuid: str | None = None,
    **properties,
) -> dict:
    event = {
        "type": event_type,
        "id": event_id,
        "uuid": uuid,
        "scan": SCAN_ID,
        "timestamp": timestamp,
        "data_json" if isinstance(data, dict) else "data": data,
        **properties,
    }
    if parent_uuid:
        event["parent_uuid"] = parent_uuid
    return event


def _scan_event(run: int, status: str, timestamp: float) -> dict:
    data: dict[str, Any] = {
        "name": "synthetic-scan",
        "status": status,
        "started_at": f"2026-01-0{run}T00:00:00Z",
        "target": {"seeds": ["example.test"]},
    }
    if status == "FINISHED":
        data.update(
            {
                "finished_at": f"2026-01-0{run}T00:01:00Z",
                "duration_seconds": 60,
            },
        )
    return _event(
        "SCAN",
        SCAN_ID,
        f"SCAN:run-{run}-{status.lower()}",
        data,
        timestamp=timestamp,
    )


def _events(
    run: int,
    *,
    changed_identities: bool = False,
    include_email: bool = True,
) -> list[dict]:
    host = "api.example.test" if changed_identities else "app.example.test"
    port = 8443 if changed_identities else 443
    url = (
        "https://api.example.test:8443/admin"
        if changed_identities
        else "https://app.example.test/admin"
    )
    dns_id = "DNS_NAME:api" if changed_identities else "DNS_NAME:app"
    port_id = (
        "OPEN_TCP_PORT:api-8443" if changed_identities else "OPEN_TCP_PORT:app-443"
    )
    url_id = "URL:api-admin" if changed_identities else "URL:app-admin"
    technology_id = (
        "TECHNOLOGY:api-8443-nginx"
        if changed_identities
        else "TECHNOLOGY:app-443-nginx"
    )
    prefix = f"run-{run}"
    scan_uuid = f"SCAN:{prefix}-running"
    dns_uuid = f"DNS_NAME:{prefix}-one"
    ip_uuid = f"IP_ADDRESS:{prefix}"
    port_uuid = f"OPEN_TCP_PORT:{prefix}"
    url_uuid = f"URL:{prefix}"

    events = [
        _scan_event(run, "RUNNING", run * 100),
        _event(
            "DNS_NAME",
            dns_id,
            dns_uuid,
            host,
            timestamp=run * 100 + 1,
            parent_uuid=scan_uuid,
            host=host,
            resolved_hosts=[IP_ADDRESS],
            tags=[f"run-{run}", "a-record"],
            module="dnsresolve",
            scope_distance=1,
        ),
        _event(
            "DNS_NAME",
            dns_id,
            f"DNS_NAME:{prefix}-two",
            host,
            timestamp=run * 100 + 2,
            parent_uuid=scan_uuid,
            host=host,
            resolved_hosts=[IP_ADDRESS],
            tags=["in-scope"],
            module=f"synthetic-module-{run}",
            scope_distance=0,
        ),
        _event(
            "IP_ADDRESS",
            IP_ID,
            ip_uuid,
            IP_ADDRESS,
            timestamp=run * 100 + 3,
            parent_uuid=dns_uuid,
            host=IP_ADDRESS,
            module="dnsresolve",
        ),
        _event(
            "IP_RANGE",
            "IP_RANGE:stable",
            f"IP_RANGE:{prefix}",
            "8.8.8.0/24",
            timestamp=run * 100 + 4,
            parent_uuid=ip_uuid,
            module="speculate",
        ),
        _event(
            "OPEN_TCP_PORT",
            port_id,
            port_uuid,
            f"{host}:{port}",
            timestamp=run * 100 + 5,
            parent_uuid=dns_uuid,
            host=host,
            port=port,
            module="portscan",
        ),
        _event(
            "URL",
            url_id,
            url_uuid,
            url,
            timestamp=run * 100 + 6,
            parent_uuid=port_uuid,
            host=host,
            port=port,
            module="http",
        ),
        _event(
            "ASN",
            "ASN:stable-15169",
            f"ASN:{prefix}",
            {
                "asn": 15169,
                "name": "GOOGLE",
                "country": "US",
                "description": "Synthetic ASN fixture",
                "subnet": "8.8.8.0/24",
            },
            timestamp=run * 100 + 7,
            parent_uuid=ip_uuid,
            module="asn",
        ),
        _event(
            "TECHNOLOGY",
            technology_id,
            f"TECHNOLOGY:{prefix}",
            {"technology": "nginx", "host": host, "port": port, "url": url},
            timestamp=run * 100 + 8,
            parent_uuid=url_uuid,
            host=host,
            port=port,
            module="fingerprintx",
        ),
        _event(
            "ORG_STUB",
            "ORG_STUB:stable-example",
            f"ORG_STUB:{prefix}",
            "Example Organization",
            timestamp=run * 100 + 9,
            parent_uuid=dns_uuid,
            module="speculate",
        ),
        _event(
            "SOCIAL",
            f"SOCIAL:bbot-{run}",
            f"SOCIAL:{prefix}",
            {
                "platform": "github",
                "profile_name": "example-security",
                "url": (
                    "https://github.com/example-security-new"
                    if changed_identities
                    else "https://github.com/example-security"
                ),
            },
            timestamp=run * 100 + 10,
            parent_uuid=dns_uuid,
            module="social",
        ),
        _event(
            "STORAGE_BUCKET",
            f"STORAGE_BUCKET:bbot-{run}",
            f"STORAGE_BUCKET:{prefix}",
            (
                {
                    "name": "example-bucket-new",
                    "provider": "gcp",
                    "url": "https://storage.googleapis.com/example-bucket-new",
                }
                if changed_identities
                else {
                    "name": "example-bucket",
                    "provider": "aws",
                    "url": f"https://example-bucket.s3.us-west-{run}.amazonaws.com",
                }
            ),
            timestamp=run * 100 + 11,
            parent_uuid=dns_uuid,
            module="bucket_amazon" if not changed_identities else "bucket_google",
        ),
        _event(
            "FINDING",
            f"FINDING:bbot-{run}",
            f"FINDING:{prefix}",
            {
                "name": "Exposed admin panel",
                "description": f"Explanation from run {run}",
                "severity": "HIGH" if run > 1 else "MEDIUM",
                "confidence": "CONFIRMED" if run > 1 else "MEDIUM",
                "host": host,
                "port": port,
                "url": url,
                "cves": [],
            },
            timestamp=run * 100 + 12,
            parent_uuid=url_uuid,
            host=host,
            port=port,
            module="nuclei",
        ),
    ]
    if include_email:
        events.append(
            _event(
                "EMAIL_ADDRESS",
                "EMAIL_ADDRESS:stable-security",
                f"EMAIL_ADDRESS:{prefix}",
                "security@example.test",
                timestamp=run * 100 + 13,
                parent_uuid=dns_uuid,
                module="securitytxt",
            ),
        )
    events.append(_scan_event(run, "FINISHED", run * 100 + 20))
    return events


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
    first_events = _events(1)

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
    _sync(neo4j_session, _events(2), 202)

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
        "AFFECTS": ("BbotFinding", "BbotURL"),
        "ANNOUNCED_BY": ("BbotIPAddress", "BbotASN"),
        "DETECTED_ON": ("BbotTechnology", "BbotURL"),
        "HAS_OPEN_PORT": ("BbotDNSName", "BbotOpenTCPPort"),
        "HOSTED_BY": ("BbotURL", "BbotOpenTCPPort"),
        "RESOLVES_TO": ("BbotDNSName", "BbotIPAddress"),
    }
    for relationship, (source_label, target_label) in expected_relationships.items():
        count = neo4j_session.run(
            f"MATCH (:{source_label})-[:{relationship}]->(:{target_label}) RETURN count(*) AS count",
        ).single()["count"]
        assert count == 1

    # Act: true identity components change, and the email disappears.
    _sync(
        neo4j_session,
        _events(3, changed_identities=True, include_email=False),
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
    _sync(neo4j_session, _events(4, changed_identities=True), 404)

    # Assert: it was recreated, with a new firstseen timestamp.
    recreated_email = neo4j_session.run(
        """
        MATCH (email:BbotEmailAddress {id: 'EMAIL_ADDRESS:stable-security'})
        RETURN email.firstseen AS firstseen, email.lastupdated AS lastupdated
        """,
    ).single()
    assert recreated_email["firstseen"] > first_email["firstseen"]
    assert recreated_email["lastupdated"] == 404


def test_bbot_dns_and_ip_correlate_to_provider_ontology_nodes(
    neo4j_session,
) -> None:
    # Arrange
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    _sync(neo4j_session, _events(1), 101)
    neo4j_session.run(
        """
        CREATE (:AWSDNSRecord:DNSRecord {
            id: 'provider-dns-record',
            _ont_name: 'APP.EXAMPLE.TEST'
        })
        CREATE (:PublicIP {id: $ip, ip_address: $ip})
        """,
        ip=IP_ADDRESS,
    )

    # Act
    run_typed_analysis_job(
        BBOT_DNS_MATCHES_PROVIDER,
        neo4j_session,
        {"UPDATE_TAG": 101},
    )
    run_typed_analysis_job(
        BBOT_IP_MATCHES_PUBLIC_IP,
        neo4j_session,
        {"UPDATE_TAG": 101},
    )

    # Assert
    assert (
        neo4j_session.run(
            """
            MATCH (:BbotDNSName {id: 'DNS_NAME:app'})
                  -[:MATCHES_DNS_RECORD]->(:AWSDNSRecord {id: 'provider-dns-record'})
            RETURN count(*) AS count
            """,
        ).single()["count"]
        == 1
    )
    assert (
        neo4j_session.run(
            """
            MATCH (:BbotIPAddress {id: $bbot_id})
                  -[:MATCHES_PUBLIC_IP]->(:PublicIP {id: $ip})
            RETURN count(*) AS count
            """,
            bbot_id=IP_ID,
            ip=IP_ADDRESS,
        ).single()["count"]
        == 1
    )
