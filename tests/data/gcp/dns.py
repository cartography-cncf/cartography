# flake8: noqa
DNS_ZONES = [
    {
        "name": "test-zone-1",
        "dnsName": "zone-1.example.com.",
        "description": "A test zone",
        "id": "111111111111111111111",
        "nameServers": [
            "ns-cloud-e1.googledomains.com.",
            "ns-cloud-e2.googledomains.com.",
            "ns-cloud-e3.googledomains.com.",
            "ns-cloud-e4.googledomains.com.",
        ],
        "creationTime": "2020-04-02T14:00:00.0000Z",
        "dnssecConfig": {
            "state": "on",
            "nonExistence": "test",
            "kind": "dns#managedZoneDnsSecConfig",
        },
        "visibility": "public",
        "kind": "dns#managedZone",
    },
    {
        "name": "test-zone-2",
        "dnsName": "zone-2.example.com.",
        "description": "A test zone",
        "id": "2222222222222222222",
        "nameServers": [
            "ns-cloud-e1.googledomains.com.",
            "ns-cloud-e2.googledomains.com.",
            "ns-cloud-e3.googledomains.com.",
            "ns-cloud-e4.googledomains.com.",
        ],
        "creationTime": "2020-04-02T14:00:00.0000Z",
        "dnssecConfig": {
            "state": "on",
            "nonExistence": "test",
            "kind": "dns#managedZoneDnsSecConfig",
        },
        "visibility": "public",
        "kind": "dns#managedZone",
    },
]

DNS_RRS = [
    {
        "name": "a.zone-1.example.com.",
        "type": "TXT",
        "ttl": 300,
        "rrdatas": ['"test=test"'],
        "signatureRrdatas": [],
        "kind": "dns#resourceRecordSet",
        "zone": "111111111111111111111",
    },
    {
        "name": "b.zone-1.example.com.",
        "type": "TXT",
        "ttl": 300,
        "rrdatas": ['"test=test"'],
        "signatureRrdatas": [],
        "kind": "dns#resourceRecordSet",
        "zone": "111111111111111111111",
    },
    {
        "name": "a.zone-2.example.com.",
        "type": "TXT",
        "ttl": 300,
        "rrdatas": ['"test=test"'],
        "signatureRrdatas": [],
        "kind": "dns#resourceRecordSet",
        "zone": "2222222222222222222",
    },
]
