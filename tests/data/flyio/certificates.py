CERTIFICATES_RESPONSE = {
    "certificates": [
        {
            "hostname": "www.example.com",
            "status": "active",
            "dns_provider": "enom",
            "configured": True,
            "acme_dns_configured": True,
            "acme_alpn_configured": True,
            "acme_http_configured": True,
            "ownership_txt_configured": True,
            "acme_requested": True,
            "has_custom_certificate": False,
            "has_fly_certificate": True,
            "certificates": [
                {
                    "source": "fly",
                    "status": "active",
                    "created_at": "2026-07-31T06:53:00Z",
                    "expires_at": "2026-10-29T06:53:00Z",
                    "issuer": None,
                    "issued": [
                        {
                            "type": "ecdsa",
                            "expires_at": "2026-10-29T06:53:00Z",
                            "certificate_authority": "lets_encrypt",
                        },
                    ],
                },
            ],
            "created_at": "2026-07-31T06:53:00Z",
            "updated_at": "2026-07-31T07:00:00Z",
        },
    ],
    "total_count": 1,
}
