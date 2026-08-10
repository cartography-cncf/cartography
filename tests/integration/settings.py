import os

DEFAULTS = {
    "DATABASE_BACKEND": "neo4j",
    "NEO4J_URL": "bolt://localhost:7687",
    "NEO4J_DOCKER_IMAGE": "neo4j:5-community",
    "ARCADEDB_DOCKER_IMAGE": "arcadedata/arcadedb:26.7.3",
    "ARCADEDB_USER": "root",
    "ARCADEDB_PASSWORD": "cartography-test-password",
    "ARCADEDB_DATABASE": "cartography",
}


def get(name):
    return os.environ.get(name, DEFAULTS.get(name))
