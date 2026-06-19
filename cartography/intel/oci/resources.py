from typing import Dict

from . import compute
from . import containerregistry
from . import encryption
from . import iam
from . import logging as ocilogging
from . import monitoring
from . import network
from . import oke
from . import storage


RESOURCE_FUNCTIONS: Dict = {
    "iam": iam.sync,
    "compute": compute.sync,
    "network": network.sync,
    "encryption": encryption.sync,
    "monitoring": monitoring.sync,
    "storage": storage.sync,
    "oke": oke.sync,
    "logging": ocilogging.sync,
    "containerregistry": containerregistry.sync,
}
