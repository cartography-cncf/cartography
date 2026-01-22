import pytest

from cartography.config import Config
from cartography.intel.cloudflare import start_cloudflare_ingestion


def test_start_cloudflare_ingestion_requires_token():
    config = Config(neo4j_uri="bolt://localhost:7687")

    with pytest.raises(RuntimeError, match="Cloudflare import is not configured"):
        start_cloudflare_ingestion(None, config)
