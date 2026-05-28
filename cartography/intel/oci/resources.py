from typing import Dict

from . import compute
from . import iam
from . import network


RESOURCE_FUNCTIONS: Dict = {
    "iam": iam.sync,
    "compute": compute.sync,
    "network": network.sync,
}
