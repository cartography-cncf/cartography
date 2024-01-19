# flake8: noqa
GET_CVE_API_DATA = {
    "resultsPerPage": 5,
    "startIndex": 0,
    "totalResults": 80,
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
                        "value": "\nThere is a DLL hijacking vulnerability in ZTE ZXCLOUD iRAI, an attacker could place a fake DLL file in a specific directory and successfully exploit this vulnerability to execute malicious code.\n\n",
                    },
                    {
                        "lang": "es",
                        "value": "Existe una vulnerabilidad de secuestro de DLL en ZTE ZXCLOUD iRAI. Un atacante podría colocar un archivo DLL falso en un directorio específico y explotar con éxito esta vulnerabilidad para ejecutar código malicioso.",
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
                            {
                                "lang": "en",
                                "value": "CWE-20",
                            },
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
                "id": "CVE-2023-6493",
                "sourceIdentifier": "security@wordfence.com",
                "published": "2024-01-05T02:15:07.740",
                "lastModified": "2024-01-10T15:10:40.807",
                "vulnStatus": "Analyzed",
                "descriptions": [
                    {
                        "lang": "en",
                        "value": "The Depicter Slider – Responsive Image Slider, Video Slider & Post Slider plugin for WordPress is vulnerable to Cross-Site Request Forgery in all versions up to, and including, 2.0.6. This is due to missing or incorrect nonce validation on the 'save' function. This makes it possible for unauthenticated attackers to modify the plugin's settings via a forged request granted they can trick a site administrator into performing an action such as clicking on a link. CVE-2023-51491 appears to be a duplicate of this issue.",
                    },
                    {
                        "lang": "es",
                        "value": "El complemento The Depicter Slider – Responsive Image Slider, Video Slider &amp; Post Slider para WordPress es vulnerable a Cross-Site Request Forgery en todas las versiones hasta la 2.0.6 incluida. Esto se debe a una validación nonce faltante o incorrecta en la función \"save\". Esto hace posible que atacantes no autenticados modifiquen la configuración del complemento mediante una solicitud falsificada, siempre que puedan engañar al administrador del sitio para que realice una acción como hacer clic en un enlace. CVE-2023-51491 parece ser un duplicado de este problema.",
                    },
                ],
                "metrics": {
                    "cvssMetricV31": [
                        {
                            "source": "nvd@nist.gov",
                            "type": "Primary",
                            "cvssData": {
                                "version": "3.1",
                                "vectorString": "CVSS:3.1/AV:N/AC:L/PR:N/UI:R/S:U/C:N/I:L/A:N",
                                "attackVector": "NETWORK",
                                "attackComplexity": "LOW",
                                "privilegesRequired": "NONE",
                                "userInteraction": "REQUIRED",
                                "scope": "UNCHANGED",
                                "confidentialityImpact": "NONE",
                                "integrityImpact": "LOW",
                                "availabilityImpact": "NONE",
                                "baseScore": 4.3,
                                "baseSeverity": "MEDIUM",
                            },
                            "exploitabilityScore": 2.8,
                            "impactScore": 1.4,
                        },
                        {
                            "source": "security@wordfence.com",
                            "type": "Secondary",
                            "cvssData": {
                                "version": "3.1",
                                "vectorString": "CVSS:3.1/AV:N/AC:L/PR:N/UI:R/S:U/C:N/I:L/A:N",
                                "attackVector": "NETWORK",
                                "attackComplexity": "LOW",
                                "privilegesRequired": "NONE",
                                "userInteraction": "REQUIRED",
                                "scope": "UNCHANGED",
                                "confidentialityImpact": "NONE",
                                "integrityImpact": "LOW",
                                "availabilityImpact": "NONE",
                                "baseScore": 4.3,
                                "baseSeverity": "MEDIUM",
                            },
                            "exploitabilityScore": 2.8,
                            "impactScore": 1.4,
                        },
                    ],
                },
                "weaknesses": [
                    {
                        "source": "nvd@nist.gov",
                        "type": "Primary",
                        "description": [
                            {
                                "lang": "en",
                                "value": "CWE-352",
                            },
                        ],
                    },
                ],
                "configurations": [
                    {
                        "nodes": [
                            {
                                "operator": "OR",
                                "negate": False,
                                "cpeMatch": [
                                    {
                                        "vulnerable": True,
                                        "criteria": "cpe:2.3:a:averta:depicter_slider:*:*:*:*:*:wordpress:*:*",
                                        "versionEndIncluding": "2.0.6",
                                        "matchCriteriaId": "7EC2E784-7E22-4632-BA4C-4B931749BD15",
                                    },
                                ],
                            },
                        ],
                    },
                ],
                "references": [
                    {
                        "url": "https://plugins.trac.wordpress.org/changeset/3013596/depicter/trunk/app/src/WordPress/Settings/Settings.php",
                        "source": "security@wordfence.com",
                        "tags": [
                            "Patch",
                        ],
                    },
                    {
                        "url": "https://www.wordfence.com/threat-intel/vulnerabilities/id/c9c907ea-3ab4-4674-8945-ade4f6ff2679?source=cve",
                        "source": "security@wordfence.com",
                        "tags": [
                            "Third Party Advisory",
                        ],
                    },
                ],
            },
        },
        {
            "cve": {
                "id": "CVE-2024-22075",
                "sourceIdentifier": "cve@mitre.org",
                "published": "2024-01-05T03:15:08.537",
                "lastModified": "2024-01-10T15:06:42.563",
                "vulnStatus": "Analyzed",
                "descriptions": [
                    {
                        "lang": "en",
                        "value": "Firefly III (aka firefly-iii) before 6.1.1 allows webhooks HTML Injection.",
                    },
                    {
                        "lang": "es",
                        "value": "Firefly III (aka firefly-iii) anterior a 6.1.1 permite la inyección HTML de webhooks.",
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
                "weaknesses": [
                    {
                        "source": "nvd@nist.gov",
                        "type": "Primary",
                        "description": [
                            {
                                "lang": "en",
                                "value": "CWE-79",
                            },
                        ],
                    },
                    {
                        "source": "nvd@nist.gov",
                        "type": "Primary",
                        "description": [
                            {
                                "lang": "en",
                                "value": "CWE-80",
                            },
                        ],
                    },
                ],
                "configurations": [
                    {
                        "nodes": [
                            {
                                "operator": "OR",
                                "negate": False,
                                "cpeMatch": [
                                    {
                                        "vulnerable": True,
                                        "criteria": "cpe:2.3:a:firefly-iii:firefly_iii:*:*:*:*:*:*:*:*",
                                        "versionEndExcluding": "6.1.1",
                                        "matchCriteriaId": "A6454D7F-5388-4519-AE45-11A8BD704D1E",
                                    },
                                ],
                            },
                        ],
                    },
                ],
                "references": [
                    {
                        "url": "https://github.com/firefly-iii/firefly-iii/releases/tag/v6.1.1",
                        "source": "cve@mitre.org",
                        "tags": [
                            "Release Notes",
                        ],
                    },
                ],
            },
        },
        {
            "cve": {
                "id": "CVE-2023-52323",
                "sourceIdentifier": "cve@mitre.org",
                "published": "2024-01-05T04:15:07.763",
                "lastModified": "2024-01-05T11:54:11.040",
                "vulnStatus": "Undergoing Analysis",
                "descriptions": [
                    {
                        "lang": "en",
                        "value": "PyCryptodome and pycryptodomex before 3.19.1 allow side-channel leakage for OAEP decryption, exploitable for a Manger attack.",
                    },
                    {
                        "lang": "es",
                        "value": "PyCryptodome y pycryptodomex anteriores a 3.19.1 permiten la fuga de canal lateral para el descifrado OAEP, explotable para un ataque Manger.",
                    },
                ],
                "metrics": {},
                "references": [
                    {
                        "url": "https://github.com/Legrandin/pycryptodome/blob/master/Changelog.rst",
                        "source": "cve@mitre.org",
                    },
                    {
                        "url": "https://pypi.org/project/pycryptodomex/#history",
                        "source": "cve@mitre.org",
                    },
                ],
            },
        },
        {
            "cve": {
                "id": "CVE-2024-22086",
                "sourceIdentifier": "cve@mitre.org",
                "published": "2024-01-05T04:15:07.833",
                "lastModified": "2024-01-05T11:54:11.040",
                "vulnStatus": "Undergoing Analysis",
                "descriptions": [
                    {
                        "lang": "en",
                        "value": "handle_request in http.c in cherry through 4b877df has an sscanf stack-based buffer overflow via a long URI, leading to remote code execution.",
                    },
                    {
                        "lang": "es",
                        "value": "handle_request en http.c en cherry hasta 4b877df tiene un desbordamiento de búfer en la región stack de la memoria sscanf a través de un URI largo, lo que lleva a la ejecución remota de código.",
                    },
                ],
                "metrics": {},
                "references": [
                    {
                        "url": "https://github.com/hayyp/cherry/issues/1",
                        "source": "cve@mitre.org",
                    },
                ],
            },
        },
    ],
}

GET_CVE_API_DATA_BATCH_2 = {
    "resultsPerPage": 5,
    "startIndex": 5,
    "totalResults": 80,
    "format": "NVD_CVE",
    "version": "2.0",
    "timestamp": "2024-01-10T19:42:01.957",
    "vulnerabilities": [
        {
            "cve": {
                "id": "CVE-2024-22086",
                "sourceIdentifier": "cve@mitre.org",
                "published": "2024-01-05T04:15:07.833",
                "lastModified": "2024-01-05T11:54:11.040",
                "vulnStatus": "Undergoing Analysis",
                "descriptions": [
                    {
                        "lang": "en",
                        "value": "handle_request in http.c in cherry through 4b877df has an sscanf stack-based buffer overflow via a long URI, leading to remote code execution.",
                    },
                    {
                        "lang": "es",
                        "value": "handle_request en http.c en cherry hasta 4b877df tiene un desbordamiento de búfer en la región stack de la memoria sscanf a través de un URI largo, lo que lleva a la ejecución remota de código.",
                    },
                ],
                "metrics": {},
                "references": [
                    {
                        "url": "https://github.com/hayyp/cherry/issues/1",
                        "source": "cve@mitre.org",
                    },
                ],
            },
        },
        {
            "cve": {
                "id": "CVE-2024-22087",
                "sourceIdentifier": "cve@mitre.org",
                "published": "2024-01-05T04:15:07.880",
                "lastModified": "2024-01-05T11:54:11.040",
                "vulnStatus": "Undergoing Analysis",
                "descriptions": [
                    {
                        "lang": "en",
                        "value": "route in main.c in Pico HTTP Server in C through f3b69a6 has an sprintf stack-based buffer overflow via a long URI, leading to remote code execution.",
                    },
                    {
                        "lang": "es",
                        "value": "La ruta en main.c en Pico HTTP Server en C hasta f3b69a6 tiene un desbordamiento de búfer en la región stack de la memoria sprintf a través de un URI largo, lo que lleva a la ejecución remota de código.",
                    },
                ],
                "metrics": {},
                "references": [
                    {
                        "url": "https://github.com/foxweb/pico/issues/31",
                        "source": "cve@mitre.org",
                    },
                ],
            },
        },
        {
            "cve": {
                "id": "CVE-2024-22088",
                "sourceIdentifier": "cve@mitre.org",
                "published": "2024-01-05T04:15:07.930",
                "lastModified": "2024-01-05T11:54:11.040",
                "vulnStatus": "Undergoing Analysis",
                "descriptions": [
                    {
                        "lang": "en",
                        "value": "Lotos WebServer through 0.1.1 (commit 3eb36cc) has a use-after-free in buffer_avail() at buffer.h via a long URI, because realloc is mishandled.",
                    },
                    {
                        "lang": "es",
                        "value": "Lotos WebServer hasta 0.1.1 (commit 3eb36cc) tiene un use after free en buffer_avail() en buffer.h a través de un URI largo, porque la realloc no se maneja correctamente.",
                    },
                ],
                "metrics": {},
                "references": [
                    {
                        "url": "https://github.com/chendotjs/lotos/issues/7",
                        "source": "cve@mitre.org",
                    },
                ],
            },
        },
        {
            "cve": {
                "id": "CVE-2023-51277",
                "sourceIdentifier": "cve@mitre.org",
                "published": "2024-01-05T05:15:08.793",
                "lastModified": "2024-01-05T11:54:11.040",
                "vulnStatus": "Undergoing Analysis",
                "descriptions": [
                    {
                        "lang": "en",
                        "value": "nbviewer-app (aka Jupyter Notebook Viewer) before 0.1.6 has the get-task-allow entitlement for release builds.",
                    },
                    {
                        "lang": "es",
                        "value": "nbviewer-app (aka Jupyter Notebook Viewer) anterior a 0.1.6 tiene el derecho get-task-allow para las versiones de lanzamiento.",
                    },
                ],
                "metrics": {},
                "references": [
                    {
                        "url": "https://developer.apple.com/documentation/security/notarizing_macos_software_before_distribution/resolving_common_notarization_issues#3087731",
                        "source": "cve@mitre.org",
                    },
                    {
                        "url": "https://github.com/tuxu/nbviewer-app/commit/dc1e4ddf64c78e13175a39b076fa0646fc62e581",
                        "source": "cve@mitre.org",
                    },
                    {
                        "url": "https://github.com/tuxu/nbviewer-app/compare/0.1.5...0.1.6",
                        "source": "cve@mitre.org",
                    },
                    {
                        "url": "https://www.youtube.com/watch?v=c0nawqA_bdI",
                        "source": "cve@mitre.org",
                    },
                ],
            },
        },
        {
            "cve": {
                "id": "CVE-2020-13878",
                "sourceIdentifier": "cve@mitre.org",
                "published": "2024-01-05T08:15:41.840",
                "lastModified": "2024-01-05T11:54:11.040",
                "vulnStatus": "Undergoing Analysis",
                "descriptions": [
                    {
                        "lang": "en",
                        "value": "IrfanView B3D PlugIns before version 4.56 has a B3d.dll!+27ef heap-based out-of-bounds write.",
                    },
                    {
                        "lang": "es",
                        "value": "IrfanView B3D PlugIns anteriores a la versión 4.56 tienen una escritura fuera de los límites basada en montón B3d.dll!+27ef.",
                    },
                ],
                "metrics": {},
                "references": [
                    {
                        "url": "https://gist.github.com/oicu0619/2b0eb7dd447aca8f4ab398a99f47488b",
                        "source": "cve@mitre.org",
                    },
                ],
            },
        },
        {
            "cve": {
                "id": "CVE-2020-13879",
                "sourceIdentifier": "cve@mitre.org",
                "published": "2024-01-05T08:15:42.663",
                "lastModified": "2024-01-05T11:54:11.040",
                "vulnStatus": "Undergoing Analysis",
                "descriptions": [
                    {
                        "lang": "en",
                        "value": "IrfanView B3D PlugIns before version 4.56 has a B3d.dll!+214f heap-based out-of-bounds write.",
                    },
                    {
                        "lang": "es",
                        "value": "rfanView B3D PlugIns anteriores a la versión 4.56 tienen una escritura fuera de los límites basada en montón B3d.dll!+214f.",
                    },
                ],
                "metrics": {},
                "references": [
                    {
                        "url": "https://gist.github.com/oicu0619/878b8c37f238f4de5ff543973ef083f5",
                        "source": "cve@mitre.org",
                    },
                ],
            },
        },
    ],
}
