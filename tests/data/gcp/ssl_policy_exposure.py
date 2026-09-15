from typing import Any

SSL_POLICY_RESPONSE: dict[str, Any] = {
    "id": "projects/sample-project-123456/aggregated/sslPolicies",
    "items": {
        "global": {
            "sslPolicies": [
                {
                    "name": "legacy-ssl-policy",
                    "selfLink": "https://www.googleapis.com/compute/v1/projects/"
                    "sample-project-123456/global/sslPolicies/legacy-ssl-policy",
                    "profile": "CUSTOM",
                    "minTlsVersion": "TLS_1_0",
                    "enabledFeatures": [
                        "TLS_RSA_WITH_3DES_EDE_CBC_SHA",
                    ],
                    "customFeatures": [
                        "TLS_RSA_WITH_3DES_EDE_CBC_SHA",
                    ],
                },
            ],
        },
    },
}

REGIONAL_SSL_POLICY_RESPONSE: dict[str, Any] = {
    "id": "projects/sample-project-123456/aggregated/sslPolicies",
    "items": {
        "regions/us-central1": {
            "sslPolicies": [
                {
                    "name": "regional-modern-ssl-policy",
                    "selfLink": "https://www.googleapis.com/compute/v1/projects/"
                    "sample-project-123456/regions/us-central1/sslPolicies/"
                    "regional-modern-ssl-policy",
                    "profile": "MODERN",
                    "minTlsVersion": "TLS_1_2",
                },
            ],
        },
    },
}

SSL_POLICY_AGGREGATED_RESPONSE: dict[str, Any] = {
    "id": "projects/sample-project-123456/aggregated/sslPolicies",
    "items": {
        "global": SSL_POLICY_RESPONSE["items"]["global"],
        "regions/us-central1": REGIONAL_SSL_POLICY_RESPONSE["items"][
            "regions/us-central1"
        ],
    },
}

# A target HTTPS proxy referencing the (weak) SSL policy above.
TARGET_HTTPS_PROXY_RESPONSE: dict[str, Any] = {
    "id": "projects/sample-project-123456/aggregated/targetHttpsProxies",
    "items": {
        "global": {
            "targetHttpsProxies": [
                {
                    "name": "test-https-proxy",
                    "selfLink": "https://www.googleapis.com/compute/v1/projects/"
                    "sample-project-123456/global/targetHttpsProxies/test-https-proxy",
                    "urlMap": "https://www.googleapis.com/compute/v1/projects/"
                    "sample-project-123456/global/urlMaps/test-url-map",
                    "sslPolicy": "https://www.googleapis.com/compute/v1/projects/"
                    "sample-project-123456/global/sslPolicies/legacy-ssl-policy",
                },
            ],
        },
    },
}

REGIONAL_TARGET_HTTPS_PROXY_RESPONSE: dict[str, Any] = {
    "id": "projects/sample-project-123456/aggregated/targetHttpsProxies",
    "items": {
        "regions/us-central1": {
            "targetHttpsProxies": [
                {
                    "name": "regional-https-proxy",
                    "selfLink": "https://www.googleapis.com/compute/v1/projects/"
                    "sample-project-123456/regions/us-central1/targetHttpsProxies/"
                    "regional-https-proxy",
                    "urlMap": "https://www.googleapis.com/compute/v1/projects/"
                    "sample-project-123456/regions/us-central1/urlMaps/regional-url-map",
                    "sslPolicy": "https://www.googleapis.com/compute/v1/projects/"
                    "sample-project-123456/regions/us-central1/sslPolicies/"
                    "regional-modern-ssl-policy",
                },
            ],
        },
    },
}

TARGET_HTTPS_PROXY_AGGREGATED_RESPONSE: dict[str, Any] = {
    "id": "projects/sample-project-123456/aggregated/targetHttpsProxies",
    "items": {
        "global": TARGET_HTTPS_PROXY_RESPONSE["items"]["global"],
        "regions/us-central1": REGIONAL_TARGET_HTTPS_PROXY_RESPONSE["items"][
            "regions/us-central1"
        ],
    },
}

# A target SSL proxy with NO sslPolicy set and pointed at the backend service
# defined in tests/data/gcp/compute_exposure.py.
TARGET_SSL_PROXY_RESPONSE = {
    "id": "projects/sample-project-123456/global/targetSslProxies",
    "items": [
        {
            "name": "test-ssl-proxy",
            "selfLink": "https://www.googleapis.com/compute/v1/projects/"
            "sample-project-123456/global/targetSslProxies/test-ssl-proxy",
            "service": "https://www.googleapis.com/compute/v1/projects/"
            "sample-project-123456/global/backendServices/test-backend-service",
        },
    ],
}

# A global forwarding rule fronting the HTTPS proxy above.
HTTPS_FORWARDING_RULE_RESPONSE = {
    "id": "projects/sample-project-123456/global/forwardingRules",
    "items": [
        {
            "name": "https-fr",
            "IPAddress": "35.1.2.4",
            "IPProtocol": "TCP",
            "loadBalancingScheme": "EXTERNAL",
            "target": "https://www.googleapis.com/compute/v1/projects/"
            "sample-project-123456/global/targetHttpsProxies/test-https-proxy",
            "selfLink": "https://www.googleapis.com/compute/v1/projects/"
            "sample-project-123456/global/forwardingRules/https-fr",
        },
    ],
}

# A regional forwarding rule fronting the regional HTTPS proxy above.
REGIONAL_HTTPS_FORWARDING_RULE_RESPONSE = {
    "id": "projects/sample-project-123456/regions/us-central1/forwardingRules",
    "items": [
        {
            "name": "regional-https-fr",
            "IPAddress": "10.1.2.4",
            "IPProtocol": "TCP",
            "loadBalancingScheme": "INTERNAL_MANAGED",
            "target": "https://www.googleapis.com/compute/v1/projects/"
            "sample-project-123456/regions/us-central1/targetHttpsProxies/"
            "regional-https-proxy",
            "selfLink": "https://www.googleapis.com/compute/v1/projects/"
            "sample-project-123456/regions/us-central1/forwardingRules/"
            "regional-https-fr",
        },
    ],
}
