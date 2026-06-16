from typing import Dict

from . import compute
from . import encryption
from . import iam
from . import monitoring
from . import network


RESOURCE_FUNCTIONS: Dict = {
    "iam": iam.sync,
    "compute": compute.sync,
    "network": network.sync,
    "encryption": encryption.sync,
    "monitoring": monitoring.sync,
}
