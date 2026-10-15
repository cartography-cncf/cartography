import json

# Records from the public Debian security tracker JSON export, trimmed to a few
# releases each, with shortened descriptions.
DEBIAN_TRACKER_DATA = {
    "389-ds-base": {
        "CVE-2012-0833": {
            "description": "389 Directory Server before 1.2.10 mishandles certificate group ACIs.",
            "scope": "local",
            "releases": {
                "bookworm": {
                    "status": "resolved",
                    "repositories": {"bookworm": "2.3.1+dfsg1-1+deb12u1"},
                    "fixed_version": "0",
                    "urgency": "unimportant",
                },
            },
        },
        "CVE-2023-1055": {
            "description": "RHDS 11 and 12 – LDAP decodes userPassword instead of userCertificate.",
            "debianbug": 1034891,
            "scope": "local",
            "releases": {
                "bookworm": {
                    "status": "open",
                    "repositories": {"bookworm": "2.3.1+dfsg1-1+deb12u1"},
                    "urgency": "not yet assigned",
                    "nodsa": "Minor issue",
                    "nodsa_reason": "",
                },
                "trixie": {
                    "status": "resolved",
                    "repositories": {"trixie": "3.1.2+dfsg1-1+deb13u1"},
                    "fixed_version": "2.3.4+dfsg1-1",
                    "urgency": "not yet assigned",
                },
            },
        },
    },
    "7zip": {
        "CVE-2026-48092": {
            "description": "7-Zip 9.34 to 26.00 disclose heap memory via a SquashFS offset.",
            "scope": "local",
            "releases": {
                "trixie": {
                    "status": "open",
                    "repositories": {"trixie": "25.01+dfsg-1~deb13u2"},
                    "urgency": "unimportant",
                    "next_point_update": True,
                },
            },
        },
    },
    "dnsdist": {
        "CVE-2023-44487": {
            "description": "The HTTP/2 protocol allows a denial of service (rapid reset).",
            "scope": "local",
            "releases": {
                "bookworm": {
                    "status": "open",
                    "repositories": {"bookworm": "1.7.3-2"},
                    "urgency": "end-of-life",
                },
            },
        },
        "CVE-2025-30193": {
            "description": "A crafted TCP exchange can exhaust the stack and crash DNSdist.",
            "scope": "local",
            "releases": {
                "bookworm": {
                    "status": "open",
                    "repositories": {"bookworm": "1.7.3-2"},
                    "urgency": "end-of-life",
                },
            },
        },
    },
    "tar": {
        "CVE-2005-2541": {
            "description": "Tar 1.15.1 does not warn when extracting setuid files.",
            "debianbug": 328228,
            "scope": "local",
            "releases": {
                "bookworm": {
                    "status": "open",
                    "repositories": {"bookworm": "1.34+dfsg-1.2+deb12u1"},
                    "urgency": "unimportant",
                },
                "sid": {
                    "status": "open",
                    "repositories": {"sid": "1.35+dfsg-6"},
                    "urgency": "unimportant",
                },
            },
        },
        "TEMP-0290435-0B57B5": {
            "debianbug": 290435,
            "releases": {
                "bookworm": {
                    "status": "open",
                    "repositories": {"bookworm": "1.34+dfsg-1.2+deb12u1"},
                    "urgency": "unimportant",
                },
            },
        },
    },
}

# CVE-2025-30193 and the TEMP- record are left out, as if no scanner had reported them.
CVE_IDS_IN_GRAPH = {
    "CVE-2005-2541",
    "CVE-2012-0833",
    "CVE-2023-1055",
    "CVE-2023-44487",
    "CVE-2026-48092",
}


def tracker_document(indent: int | None = None) -> bytes:
    return json.dumps(DEBIAN_TRACKER_DATA, indent=indent, ensure_ascii=False).encode()
