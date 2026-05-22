from typing import Dict

from . import compute
from . import iam


RESOURCE_FUNCTIONS: Dict = {
    "iam": iam.sync,
    "compute": compute.sync,
}
