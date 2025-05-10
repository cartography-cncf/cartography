import json
import os


class FileSystem:
    @classmethod
    def load(cls, file_path):
        """
        Loads a JSON object (dict) from a file.
        :type file_path: string.
        :param file_path: Filepath for the file.
        :return: Dictionary in JSON format.
        """
        with open(file_path) as json_file:
            data = json.load(json_file)
        return data

    @classmethod
    def write(cls, data, file_path):
        """
        Writes a JSON object (dict) to a file.
        :type data: Dict
        :param data: Dictionary in JSON format.
        :type file_path: string
        :param file_path: Filepath to be written to.
        :return:
        """
        with open(file_path, "w") as json_file:
            json.dump(data, json_file, sort_keys=True, indent=4)
            json_file.write("\n")

    @classmethod
    def walk(cls, drift_detection_directory):
        """
        Enables walking through drift detection.
        :type drift_detection_directory: String.
        :param drift_detection_directory: Path to drift detection directory.
        :yield: query directory.
        """
        for root, directories, _ in os.walk(drift_detection_directory):
            for directory in directories:
                yield os.path.join(root, directory)

    @classmethod
    def has_file(cls, filename):
        """
        Determines whether or not file exists.
        :type filename: string
        :param filename: filepath
        :return: Bool
        """
        return os.path.isfile(filename)
