from urllib.parse import urlparse

TENABLE_DEFAULT_URL = "https://cloud.tenable.com"


def get_tenant_id_from_url(base_url: str) -> str:
    """Return the hostname portion of a Tenable base URL for tenant scoping."""
    url = base_url if "://" in base_url else f"https://{base_url}"
    parsed = urlparse(url)
    return parsed.hostname or parsed.path.rstrip("/")


def make_tenable_id(tenant_id: str, provider_id: object) -> str:
    return f"{tenant_id}:{provider_id}"
