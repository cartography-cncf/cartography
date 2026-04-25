GET_NVD_API_DATA = {
    "resultsPerPage": 3,
    "startIndex": 0,
    "totalResults": 3,
    "format": "NVD_CVE",
    "version": "2.0",
    "timestamp": "2024-01-10T19:30:07.520",
    "vulnerabilities": [
        {
            "cve": {
                "id": "CVE-2023-41782",
                "sourceIdentifier": "psirt@zte.com.cn",
                "published": "2024-01-05T02:15:07.147",
                "lastModified": "2024-01-05T11:54:11.040",
                "vulnStatus": "Undergoing Analysis",
                "descriptions": [
                    {
                        "lang": "en",
                        "value": "There is a DLL hijacking vulnerability in ZTE ZXCLOUD iRAI.",
                    },
                    {
                        "lang": "es",
                        "value": "Existe una vulnerabilidad de secuestro de DLL.",
                    },
                ],
                "metrics": {
                    "cvssMetricV31": [
                        {
                            "source": "psirt@zte.com.cn",
                            "type": "Secondary",
                            "cvssData": {
                                "version": "3.1",
                                "vectorString": "CVSS:3.1/AV:L/AC:L/PR:L/UI:R/S:U/C:L/I:N/A:L",
                                "attackVector": "LOCAL",
                                "attackComplexity": "LOW",
                                "privilegesRequired": "LOW",
                                "userInteraction": "REQUIRED",
                                "scope": "UNCHANGED",
                                "confidentialityImpact": "LOW",
                                "integrityImpact": "NONE",
                                "availabilityImpact": "LOW",
                                "baseScore": 3.9,
                                "baseSeverity": "LOW",
                            },
                            "exploitabilityScore": 1.3,
                            "impactScore": 2.5,
                        },
                    ],
                },
                "weaknesses": [
                    {
                        "source": "psirt@zte.com.cn",
                        "type": "Secondary",
                        "description": [
                            {"lang": "en", "value": "CWE-20"},
                        ],
                    },
                ],
                "references": [
                    {
                        "url": "https://support.zte.com.cn/support/news/LoopholeInfoDetail.aspx?newsId=1032984",
                        "source": "psirt@zte.com.cn",
                    },
                ],
            },
        },
        {
            "cve": {
                "id": "CVE-2024-22075",
                "sourceIdentifier": "cve@mitre.org",
                "published": "2024-01-05T04:15:07.890",
                "lastModified": "2024-01-10T15:15:09.380",
                "vulnStatus": "Analyzed",
                "descriptions": [
                    {
                        "lang": "en",
                        "value": "An HTML injection vulnerability in Fireware.",
                    },
                ],
                "metrics": {
                    "cvssMetricV31": [
                        {
                            "source": "nvd@nist.gov",
                            "type": "Primary",
                            "cvssData": {
                                "version": "3.1",
                                "vectorString": "CVSS:3.1/AV:N/AC:L/PR:N/UI:R/S:C/C:L/I:L/A:N",
                                "attackVector": "NETWORK",
                                "attackComplexity": "LOW",
                                "privilegesRequired": "NONE",
                                "userInteraction": "REQUIRED",
                                "scope": "CHANGED",
                                "confidentialityImpact": "LOW",
                                "integrityImpact": "LOW",
                                "availabilityImpact": "NONE",
                                "baseScore": 6.1,
                                "baseSeverity": "MEDIUM",
                            },
                            "exploitabilityScore": 2.8,
                            "impactScore": 2.7,
                        },
                    ],
                },
                "weaknesses": [],
                "references": [
                    {
                        "url": "https://example.com/advisory/CVE-2024-22075",
                        "source": "cve@mitre.org",
                    },
                ],
                # CISA KEV fields embedded in NVD response
                "cisaExploitAdd": "2024-01-08",
                "cisaActionDue": "2024-01-29",
                "cisaRequiredAction": "Apply mitigations per vendor instructions.",
                "cisaVulnerabilityName": "Fireware HTML Injection Vulnerability",
            },
        },
        {
            "cve": {
                "id": "CVE-9999-0001",
                "sourceIdentifier": "cve@mitre.org",
                "published": "2024-01-06T00:00:00.000",
                "lastModified": "2024-01-06T00:00:00.000",
                "vulnStatus": "Awaiting Analysis",
                "descriptions": [
                    {
                        "lang": "en",
                        "value": "A CVE not in the graph, should be filtered out.",
                    },
                ],
                "metrics": {},
                "weaknesses": [],
                "references": [],
            },
        },
    ],
}
