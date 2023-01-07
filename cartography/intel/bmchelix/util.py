"""
cartography/intel/bmchelix/util
"""
import json
import logging
from array import array
from typing import Tuple

import pandas
import requests

logger = logging.getLogger(__name__)


def bmchelix_hosts(
    authorization: Tuple[str, str, bool],
    limit: int = 1000,
    bmchelix_timeout: int = 60,
) -> array:
    """
    Get BMC Helix assets inventory
    https://INSTANCE.onbmc.com/swagger-ui/
    """
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Authorization": f"Bearer {authorization[0]}",
    }
    json_query = {
        # This likely needs customization depending on context.
        # Note: no first seen (discovery access history seems limited to last 25)
        # pylint: disable=line-too-long
        "query": "search Host show name, os, vendor, virtual, partition, cloud, "
                 "#InferredElement:Inference:Associate:DiscoveryAccess.endpoint as 'Scanned via', "
                 "key as 'key', "
                 "#ContainedHost:HostContainment:HostContainer:VirtualMachine.name as 'Name', "
                 "#ContainedHost:HostContainment:HostContainer:VirtualMachine.key as 'VM_key', "
                 "#ContainedHost:HostContainment:HostContainer:VirtualMachine.type as 'Type', "
                 "#ContainedHost:HostContainment:HostContainer:VirtualMachine.short_name as 'short_hostname', "
                 "#ContainedHost:HostContainment:HostContainer:VirtualMachine.custom_attributes as "
                 "'Custom Attributes', "
                 "#ContainedHost:HostContainment:HostContainer:VirtualMachine.tags as 'Tags', "
                 "#ContainedHost:HostContainment:HostContainer:VirtualMachine.state as 'vm_power_state', "
                 "#ContainedHost:HostContainment:HostContainer:VirtualMachine.vm_management_ip as 'VM Management IP', "
                 "#ContainedHost:HostContainment:HostContainer:VirtualMachine.private_ip_addr as 'Private IP Address', "
                 "#ContainedHost:HostContainment:HostContainer:VirtualMachine.public_ip_addrs as "
                 "'Public IP Addresses', "
                 "#ContainedHost:HostContainment:HostContainer:VirtualMachine.os as 'vm_os', "
                 "#ContainedHost:HostContainment:HostContainer:VirtualMachine.os_build as 'vm_os_build', "
                 "#ContainedHost:HostContainment:HostContainer:VirtualMachine.os_type as 'vm_os_type', "
                 "#ContainedHost:HostContainment:HostContainer:VirtualMachine.os_vendor as 'vm_os_vendor', "
                 "#ContainedHost:HostContainment:HostContainer:VirtualMachine.os_version as 'vm_os_version', "
                 "#ContainedHost:HostContainment:HostContainer:VirtualMachine.last_update_success as "
                 "'Last Update Success', "
                 "last_access_response as 'Last Access Response', last_cmdb_sync_success as "
                 "'Last successful CMDB sync', "
                 "#ContainedHost:HostContainment:HostContainer:VirtualMachine.subscription_id as 'Subscription Id', "
                 "#ContainedHost:HostContainment:HostContainer:VirtualMachine.vm_uuid as 'VM UUID', "
                 "uuid as 'UUID', azure_vm_id as 'Azure VM ID', "
                 "#InferredElement:Inference:Associate:DiscoveryAccess.discovery_starttime as 'Discovery Start Time', "
                 "#InferredElement:Inference:Associate:DiscoveryAccess.discovery_endtime as 'Discovery End Time', "
                 "#InferredElement:Inference:Associate:DiscoveryAccess.kind as 'Kind', "
                 "#InferredElement:Inference:Associate:DiscoveryAccess.result as 'Result', "
                 "#InferredElement:Inference:Associate:DiscoveryAccess.scan_kind as 'Scan Kind'",
    }

    resp = requests.post(
        authorization[1] + "/data/search",
        headers=headers,
        json=json_query,
        params={"limit": limit},
        timeout=bmchelix_timeout,
    )
    logger.debug("url: %s", resp.url)

    resp.raise_for_status()

    data = resp.json()
    columns = data[0]["headings"]

    full_data = []
    full_data += data[0]["results"]

    j = 1
    while "next" in data[0]:
        logger.debug(
            "next present (%s, %s/%s): %s",
            j,
            data[0]["next_offset"],
            data[0]["count"],
            data[0]["next"],
        )
        logger.warning(
            "next present (%s, %s/%s): %s",
            j,
            data[0]["next_offset"],
            data[0]["count"],
            data[0]["next"],
        )
        try:
            # new offset and limit are already in "next"
            resp2 = requests.post(
                data[0]["next"],
                headers=headers,
                json=json_query,
                timeout=bmchelix_timeout,
            )
            resp2.raise_for_status()
            data = resp2.json()
            full_data += data[0]["results"]
            logger.info("BmcHelixHosts count: %s", len(full_data))
            j += 1
        except requests.HTTPError as exception:
            logger.exception("BmcHelixHosts exception: %s", exception)

    logger.info("BmcHelixHosts count final: %s", len(full_data))
    logger.warning("BmcHelixHosts count final: %s", len(full_data))
    # logger.debug("Example array: %s", full_data[0])

    df_bmchelix_tmp = pandas.DataFrame(full_data, columns=columns)
    df_bmchelix_tmp.rename(
        columns={
            "vendor": "hw_vendor",
            "Custom Attributes": "custom_attributes",
            "Tags": "tags",
            "Private IP Address": "private_ip",
            "Public IP Addresses": "public_ip",
            "Subscription Id": "subscription_id",
            "Azure VM ID": "instance_id",
            "UUID": "uuid",
            "Last successful CMDB sync": "tool_last_seen",
        },
        inplace=True,
    )
    df_bmchelix_tmp['short_hostname'] = df_bmchelix_tmp['short_hostname'].str.lower()
    logger.debug("Example df line: %s", df_bmchelix_tmp.head(1).T.to_string())
    logger.warning("Example df line: %s", df_bmchelix_tmp.head(1).T.to_string())

    # Remove uuid None or null
    df_bmchelix_tmp = df_bmchelix_tmp[df_bmchelix_tmp.uuid.notnull()]
    # Check no duplicated column
    if df_bmchelix_tmp.columns.duplicated().all():
        logger.warning(
            "Duplicated columns present - Removing: %s",
            df_bmchelix_tmp.columns.duplicated(),
        )
        logger.warning("Duplicated columns - shape before: %s", df_bmchelix_tmp.shape)
        # Remove duplicated column by name
        df_bmchelix_tmp = df_bmchelix_tmp.loc[
            :, ~df_bmchelix_tmp.columns.duplicated(),
        ].copy()
        logger.warning("Duplicated columns - shape after: %s", df_bmchelix_tmp.shape)

    try:
        # Extract some custom attributes
        df_bmchelix_tmp["tags_costcenter"] = df_bmchelix_tmp["custom_attributes"].apply(
            # lambda x: ("" if (not x and "costcenter" not in x) else x['costcenter'])
            lambda x: ("" if (not x or "costcenter" not in x) else x["costcenter"]),
        )
        df_bmchelix_tmp["tags_businesscontact"] = df_bmchelix_tmp[
            "custom_attributes"
        ].apply(
            lambda x: (
                "" if (not x or "businesscontact" not in x) else x["businesscontact"]
            ),
        )
        df_bmchelix_tmp["tags_engcontact"] = df_bmchelix_tmp["custom_attributes"].apply(
            lambda x: ("" if (not x or "engcontact" not in x) else x["engcontact"]),
        )
    except TypeError as exception:
        logger.exception("custom attributes exception: %s", exception)

    flatten_data = json.loads(df_bmchelix_tmp.to_json(orient="records"))
    logger.debug("Example: %s", flatten_data[0])

    # save to local csv for debugging?
    df_bmchelix_tmp.to_csv("/tmp/cartography-bmchelix.csv")

    return flatten_data