from datetime import datetime

from dateutil.tz import tzutc
from scaleway.instance.v1 import Image
from scaleway.instance.v1 import SecurityGroupSummary
from scaleway.instance.v1 import Server
from scaleway.instance.v1 import ServerIp
from scaleway.instance.v1 import ServerLocation
from scaleway.instance.v1 import ServerSummary
from scaleway.instance.v1 import VolumeServer
from scaleway.instance.v1 import VolumeSummary

SCALEWAY_INSTANCES = [
    Server(
        id="345627e9-18ff-47e0-b73d-3f38fddb4390",
        name="demo-server",
        organization="0681c477-fbb9-4820-b8d6-0eef10cfcd6d",
        project="0681c477-fbb9-4820-b8d6-0eef10cfcd6d",
        allowed_actions=["poweroff", "terminate", "reboot", "stop_in_place", "backup"],
        tags=["demo"],
        commercial_type="DEV1-S",
        creation_date=datetime(2025, 3, 20, 14, 49, 48, 107731, tzinfo=tzutc()),
        dynamic_ip_required=False,
        hostname="demo-server",
        protected=False,
        routed_ip_enabled=True,
        enable_ipv6=False,
        image=Image(
            id="",
            name="Ubuntu 24.04 Noble Numbat",
            arch="x86_64",
            extra_volumes={},
            from_server="",
            organization="51b656e3-4865-41e8-adbc-0c45bdd780db",
            creation_date=datetime(2025, 2, 3, 13, 36, 27, 705911, tzinfo=tzutc()),
            modification_date=datetime(2025, 2, 3, 13, 36, 27, 705911, tzinfo=tzutc()),
            default_bootscript=None,
            public=True,
            state="available",
            project="51b656e3-4865-41e8-adbc-0c45bdd780db",
            tags=[],
            zone="fr-par-1",
            root_volume=VolumeSummary(
                id="",
                name="Ubuntu 24.04 Noble Numbat",
                size=10000000000,
                volume_type="l_ssd",
            ),
        ),
        private_ip=None,
        public_ip=ServerIp(
            id="",
            address="51.1.2.8",
            gateway="62.210.0.1",
            netmask="32",
            family="inet",
            dynamic=False,
            provisioning_mode="dhcp",
            tags=[],
            ipam_id="",
            state="attached",
        ),
        public_ips=[
            ServerIp(
                id="",
                address="51.1.2.8",
                gateway="62.210.0.1",
                netmask="32",
                family="inet",
                dynamic=False,
                provisioning_mode="dhcp",
                tags=[],
                ipam_id="",
                state="attached",
            )
        ],
        mac_address="de:00:00:9d:9a:7d",
        state="running",
        boot_type="local",
        volumes={
            "0": VolumeServer(
                id="7c37b328-247c-4668-8ee1-701a3a3cc2e4",
                name="Ubuntu 24.04 Noble Numbat",
                export_uri=None,
                organization="0681c477-fbb9-4820-b8d6-0eef10cfcd6d",
                server=ServerSummary(
                    id="345627e9-18ff-47e0-b73d-3f38fddb4390", name="demo-server"
                ),
                size=20000000000,
                volume_type="l_ssd",
                boot=False,
                zone="fr-par-1",
                creation_date=datetime(2025, 3, 20, 14, 49, 48, 107731, tzinfo=tzutc()),
                modification_date=datetime(
                    2025, 6, 20, 12, 30, 5, 316608, tzinfo=tzutc()
                ),
                state="available",
                project="0681c477-fbb9-4820-b8d6-0eef10cfcd6d",
            )
        },
        modification_date=datetime(2025, 4, 24, 8, 2, 19, 46852, tzinfo=tzutc()),
        location=ServerLocation(
            cluster_id="32",
            hypervisor_id="804",
            node_id="2",
            platform_id="14",
            zone_id="fr-par-1",
        ),
        ipv6=None,
        maintenances=[],
        state_detail="booted",
        arch="x86_64",
        private_nics=[],
        zone="fr-par-1",
        security_group=SecurityGroupSummary(id="", name="demo"),
        placement_group=None,
        admin_password_encryption_ssh_key_id=None,
        admin_password_encrypted_value=None,
        filesystems=[],
        end_of_service=None,
    )
]
