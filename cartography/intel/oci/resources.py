from typing import Dict

from . import compute
from . import iam
from . import oke
from . import storage


RESOURCE_FUNCTIONS: Dict = {
    "iam": iam.sync,
    "compute": compute.sync,
    "storage": storage.sync,
    "oke": oke.sync,
}
