from typing import Dict

from . import apigateway
from . import bigtable
from . import cloudfunction
from . import cloudkms
from . import cloudrun
from . import compute
from . import dns
from . import firestore
from . import gke
from . import iam
from . import sql
from . import storage


RESOURCE_FUNCTIONS: Dict = {
    'iam': iam.sync,
    'bigtable': bigtable.sync,
    'cloudfunction': cloudfunction.sync,
    'cloudkms': cloudkms.sync,
    'cloudrun': cloudrun.sync,
    'compute': compute.sync,
    'dns': dns.sync,
    'firestore': firestore.sync,
    'gke': gke.sync,
    'sql': sql.sync,
    'storage': storage.sync,
    'apigateway': apigateway.sync,
}
