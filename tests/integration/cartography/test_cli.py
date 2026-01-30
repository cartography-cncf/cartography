import unittest.mock

import cartography.cli
from tests.integration import settings


def test_cli():
    sync = unittest.mock.MagicMock()
    cli = cartography.cli.CLI(sync, "test")
    cli.main(["--neo4j-uri", settings.get("NEO4J_URL")])
    sync.run.assert_called_once()
