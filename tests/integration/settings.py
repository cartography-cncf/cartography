import os

DEFAULTS = {
    "NEO4J_URL": "bolt://localhost:7687",
    "NEO4J_DOCKER_IMAGE": "neo4j:5-community",
}


def get(name):
    return os.environ.get(name, DEFAULTS.get(name))
