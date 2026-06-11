from typing import Dict

from . import compute
from . import iam
from . import network
from . import storage


RESOURCE_FUNCTIONS: Dict = {
    "iam": iam.sync,
    "compute": compute.sync,
    "network": network.sync,
    "storage": storage.sync,
}
