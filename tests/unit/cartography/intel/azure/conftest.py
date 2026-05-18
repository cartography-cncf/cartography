"""
Mock unavailable third-party dependencies so azure unit tests can run
without the full production install (cloudconsolelink, adal, msrestazure,
azure-mgmt-*, msgraph, etc.).
"""
import sys
from unittest.mock import MagicMock

_MISSING_DEPS = [
    "cloudconsolelink",
    "cloudconsolelink.clouds",
    "cloudconsolelink.clouds.azure",
    "adal",
    "msrestazure",
    "msrestazure.azure_active_directory",
    "azure.common",
    "azure.common.credentials",
    "azure.mgmt.containerinstance",
    "azure.mgmt.containerregistry",
    "azure.mgmt.network",
    "azure.mgmt.storage",
    "azure.mgmt.sql",
    "azure.mgmt.cosmosdb",
    "azure.mgmt.keyvault",
    "azure.mgmt.monitor",
    "azure.mgmt.authorization",
    "azure.mgmt.subscription",
    "azure.mgmt.web",
    "azure.mgmt.containerservice",
    "azure.mgmt.compute",
    "azure.mgmt.security",
    "azure.mgmt.msi",
    "azure.graphrbac",
    "azure.keyvault",
    "azure.keyvault.certificates",
    "azure.mgmt.rdbms",
    "azure.mgmt.rdbms.mysql",
    "azure.mgmt.rdbms.mysql_flexibleservers",
    "azure.mgmt.rdbms.postgresql",
    "azure.mgmt.rdbms.postgresql_flexibleservers",
    "azure.mgmt.sql.models",
    "msrestazure.azure_exceptions",
    "netaddr",
    "msgraph",
    "msgraph.generated",
    "msgraph.generated.users",
    "msgraph.generated.users.users_request_builder",
    "msgraph.generated.groups",
    "msgraph.generated.groups.groups_request_builder",
]

for _mod in _MISSING_DEPS:
    if _mod not in sys.modules:
        sys.modules[_mod] = MagicMock()
