import json
import logging
from marshmallow import Schema, fields, post_load
from enum import IntEnum


logger = logging.getLogger(__name__)


class DriftDetectorType(IntEnum):
    EXPOSURE = 1


class DriftState(object):
    def __init__(self,
                 name,
                 validation_query,
                 properties,
                 expectations,
                 detector_type):

        self.name = name
        self.validation_query = validation_query
        self.properties = properties
        self.expectations = expectations
        self.detector_type = detector_type

    def run(self, session, update):
        """
        Performs Detection
        :type neo4j session
        :param session: graph session
        :param update: boolean
        :return:
        """

        results = session.run(self.validation_query)
        logger.debug("Running validation for {0}".format(self.name))

        for record in results:
            values = []
            for field in record.values():
                if isinstance(field, list):
                    s = "|".join(field)
                    values.append(s)
                else:
                    values.append(field)
            if values not in self.expectations:
                if update:
                    self.expectations.append(values)
                yield _build_drift_insight(record)

    def update(self, session):
        """

        :param session:
        :return:
        """

        results = session.run(self.validation_query)
        logger.debug("Updating results for {0}".format(self.name))

        new_expectations = []

        for record in results:
            values = []
            for field in record.values():
                if isinstance(field, list):
                    s = "|".join(field)
                    values.append(s)
                else:
                    values.append(field)
            new_expectations.append(values)

        self.expectations = new_expectations


class DriftStateSchema(Schema):
    name = fields.Str()
    validation_query = fields.Str()
    properties = fields.List(fields.Str())
    detector_type = fields.Int()
    expectations = fields.List(fields.List(fields.Str()))

    @post_load
    def make_driftstate(self, data, **kwargs):
        return DriftState(data['name'],
                          data['validation_query'],
                          data['properties'],
                          data['expectations'],
                          DriftDetectorType(data['detector_type']))


def load_detector_from_json_file(file_path):
    """
    Creates Detector from Json File
    :type string
    :param file_path:
    :return: DriftDetector
    """
    logger.debug("Creating from json file {0}".format(file_path))
    with open(file_path) as j_file:
        data = json.load(j_file)
    schema = DriftStateSchema()
    detector = schema.load(data)
    return detector


def write_state_to_json_file(detector, file_path):
    """
    Saves detector to json file
    :param detector: Detector to be saved
    :param file_path: file_path to store detector
    :return: None
    """
    logger.debug("Saving to json file {0}".format(file_path))
    schema = DriftStateSchema()
    data = schema.dump(detector)
    with open(file_path, 'w') as j_file:
        json.dump(data, j_file, indent=4)


def _build_drift_insight(graph_result):
    """
    Build drift insight
    :type BoltStatementResult
    :param graph_result: Graph data returned by the validation_query
    :return: Dictionary representing the addition data we have on the drift
    """

    data = {}
    for k in graph_result.keys():
        data[k] = graph_result[k]

    return data
