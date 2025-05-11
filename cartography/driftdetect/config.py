from typing import Optional


class UpdateConfig:
    """
    A common interface for the drift-detection update configuration.

    All fields defined on this class must be present on a configuration object. Fields documented as required must
    contain valid values. Fields documented as optional may contain None, in which case drift-detection will choose a
    sensible default value for that piece of configuration.

    :type drift_detection_directory: string
    :param drift_detection_directory: Path to drift detection directory. Required.
    :type neo4j_uri: string
    :param neo4j_uri: URI for a Neo4j graph database service. Required.
    :type neo4j_user: string
    :param neo4j_user: User name for a Neo4j graph database service. Optional.
    :type neo4j_password: string
    :param neo4j_password: Password for a Neo4j graph database service. Optional.
    """

    def __init__(
        self,
        drift_detection_directory: str,
        neo4j_uri: str,
        neo4j_user: Optional[str] = None,
        neo4j_password: Optional[str] = None,
    ):
        self.neo4j_uri = neo4j_uri
        self.neo4j_user = neo4j_user
        self.neo4j_password = neo4j_password
        self.drift_detection_directory = drift_detection_directory


class GetDriftConfig:
    """
    A common interface for the drift-detection get-drift configuration.

    All fields defined on this class must be present on a configuration object. Fields documented as required must
    contain valid values.

    :type query_directory: string
    :param query_directory: Path to query directory. Required.
    :type start_state: string
    :param start_state: Filename (without the directory prefix) of the earlier state to be compared with. Required.
    :type end_state: string
    :param end_state: Filename (without the directory prefix) of the later state to be compared with. Required.
    """

    def __init__(
        self,
        query_directory: str,
        start_state: str,
        end_state: str,
    ):
        self.query_directory: str = query_directory
        self.start_state: str = start_state
        self.end_state: str = end_state


class AddShortcutConfig:
    """
    A common interface for the drift-detection add-shortcut configuration.

    All fields defined on this class must be present on a configuration object. Fields documented as required must
    contain valid values.

    :type query_directory: string
    :param query_directory: Path to query directory. Required.
    :type shortcut: string
    :param shortcut: Name of shortcut to access the file. Required.
    :type filename: string
    :param filename: Filename (without the directory prefix) of the state to be shortcut. Required.
    """

    def __init__(
        self,
        query_directory: str,
        shortcut: str,
        filename: str,
    ):
        self.query_directory: str = query_directory
        self.shortcut: str = shortcut
        self.filename: str = filename
