import unittest
from unittest import mock

import neo4j
import pytest

from cartography.neo4j_session_factory import Neo4jSessionFactory


def test_initialize():
    # Arrange
    neo4j_session_factory = Neo4jSessionFactory()
    neo4j_driver_mock = mock.Mock(spec=neo4j.Driver)

    # Act
    neo4j_session_factory.initialize(neo4j_driver_mock, "test_db")

    # Assert
    assert neo4j_session_factory._driver == neo4j_driver_mock
    assert neo4j_session_factory._database == "test_db"


def test_get_new_session():
    # Arrange
    neo4j_session_factory = Neo4jSessionFactory()
    neo4j_driver_mock = mock.Mock(spec=neo4j.Driver)
    neo4j_session_factory.initialize(neo4j_driver_mock, "test_db")
    neo4j_session_mock = mock.Mock()
    neo4j_driver_mock.session.return_value = neo4j_session_mock

    # Act
    new_session = neo4j_session_factory.get_new_session()

    # Assert
    assert new_session == neo4j_session_mock


class TestNeo4jSessionFactory(unittest.TestCase):
    def setUp(self):
        self.driver_mock = mock.Mock(spec=neo4j.Driver)

    def test_reinitialize(self):
        # Arrange
        neo4j_session_factory = Neo4jSessionFactory()
        neo4j_session_factory.initialize(self.driver_mock, "test_db")

        # Act
        with self.assertLogs(level="WARNING") as log:
            neo4j_session_factory.initialize(self.driver_mock, "test_db")

        # Assert
        self.assertIn("Reinitializing the Neo4j session", log.output[0])


def test_neo4j_session_factory_get_new_session_not_initialized():
    neo4j_session_factory = Neo4jSessionFactory()

    with pytest.raises(RuntimeError, match="Neo4j session factory is not initialized"):
        new_session = neo4j_session_factory.get_new_session()
        assert new_session is None
