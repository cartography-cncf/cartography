from typing import Dict

from . import compute
from . import encryption
from . import iam
from . import monitoring
from . import network
from . import storage


RESOURCE_FUNCTIONS: Dict = {
    "iam": iam.sync,
    "compute": compute.sync,
    "network": network.sync,
    "storage": storage.sync,
    "encryption": encryption.sync,
    "monitoring": monitoring.sync,
}
