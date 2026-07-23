from typing import Any

SCAN_ID = "SCAN:stable-synthetic-scan"
IP_ID = "IP_ADDRESS:stable-google-dns"
IP_ADDRESS = "8.8.8.8"


def event(
    event_type: str,
    event_id: str,
    uuid: str,
    data: str | dict,
    *,
    timestamp: float,
    parent_uuid: str | None = None,
    **properties,
) -> dict:
    result = {
        "type": event_type,
        "id": event_id,
        "uuid": uuid,
        "scan": SCAN_ID,
        "timestamp": timestamp,
        "data_json" if isinstance(data, dict) else "data": data,
        **properties,
    }
    if parent_uuid:
        result["parent_uuid"] = parent_uuid
    return result


def scan_event(run: int, status: str, timestamp: float) -> dict:
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
    return event(
        "SCAN",
        SCAN_ID,
        f"SCAN:run-{run}-{status.lower()}",
        data,
        timestamp=timestamp,
    )


def scan_only_events(run: int) -> list[dict]:
    return [
        scan_event(run, "RUNNING", run * 100),
        scan_event(run, "FINISHED", run * 100 + 20),
    ]


def events(
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

    result = [
        scan_event(run, "RUNNING", run * 100),
        event(
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
        event(
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
        event(
            "IP_ADDRESS",
            IP_ID,
            ip_uuid,
            IP_ADDRESS,
            timestamp=run * 100 + 3,
            parent_uuid=dns_uuid,
            host=IP_ADDRESS,
            module="dnsresolve",
        ),
        event(
            "IP_RANGE",
            "IP_RANGE:stable",
            f"IP_RANGE:{prefix}",
            "8.8.8.0/24",
            timestamp=run * 100 + 4,
            parent_uuid=ip_uuid,
            module="speculate",
        ),
        event(
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
        event(
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
        event(
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
        event(
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
        event(
            "ORG_STUB",
            "ORG_STUB:stable-example",
            f"ORG_STUB:{prefix}",
            "Example Organization",
            timestamp=run * 100 + 9,
            parent_uuid=dns_uuid,
            module="speculate",
        ),
        event(
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
        event(
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
        event(
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
        result.append(
            event(
                "EMAIL_ADDRESS",
                "EMAIL_ADDRESS:stable-security",
                f"EMAIL_ADDRESS:{prefix}",
                "security@example.test",
                timestamp=run * 100 + 13,
                parent_uuid=dns_uuid,
                module="securitytxt",
            ),
        )
    result.append(scan_event(run, "FINISHED", run * 100 + 20))
    return result
