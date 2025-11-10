"""
Mock data for Proxmox compute (VM/container) tests.
"""

MOCK_VM_DATA = {
    "node1": [
        {
            "node": "node1",
            "vmid": 100,
            "name": "test-vm-1",
            "status": "running",
            "maxmem": 4294967296,
            "maxdisk": 107374182400,
            "cpu": 0.15,
            "mem": 2147483648,
            "disk": 32212254720,
            "diskread": 1234567890,
            "diskwrite": 987654321,
            "netin": 123456789,
            "netout": 987654321,
            "uptime": 123456,
            "type": "qemu",
        },
        {
            "node": "node1",
            "vmid": 101,
            "name": "test-vm-2",
            "status": "stopped",
            "maxmem": 2147483648,
            "maxdisk": 53687091200,
            "cpu": 0,
            "mem": 0,
            "disk": 21474836480,
            "type": "qemu",
        },
    ],
    "node2": [
        {
            "node": "node2",
            "vmid": 200,
            "name": "test-container-1",
            "status": "running",
            "maxmem": 1073741824,
            "maxdisk": 10737418240,
            "cpu": 0.05,
            "mem": 536870912,
            "disk": 2147483648,
            "uptime": 654321,
            "type": "lxc",
        },
    ],
}

MOCK_VM_CONFIG = {
    100: {
        "cores": 2,
        "sockets": 1,
        "memory": 4096,
        "boot": "order=scsi0;ide2;net0",
        "scsihw": "virtio-scsi-single",
        "vmgenid": "12345678-1234-5678-1234-567812345678",
        "ostype": "l26",
        "onboot": 1,
        "protection": 0,
        "description": "Test VM 1",
        "machine": "pc-i440fx-8.0",
        "bios": "seabios",
        "cpu": "host",
        "cpulimit": 0,
        "cpuunits": 1024,
        "hotplug": "network,disk,usb",
        "balloon": 2048,
        "numa": 0,
        "kvm": 1,
        "watchdog": "i6300esb,action=reset",
        "rng0": "source=/dev/urandom",
        "hostpci0": "0000:01:00.0",
        "hostpci1": "0000:02:00.0",
        "usb0": "host=1-1.1",
        "serial0": "socket",
        "scsi0": "local-lvm:vm-100-disk-0,iothread=1,size=100G,format=qcow2,discard=on,ssd=1",
        "ide2": "local:iso/ubuntu-22.04.iso,media=cdrom",
        "net0": "virtio=BC:24:11:11:11:11,bridge=vmbr0,firewall=1,ip=192.168.1.100/24,gw=192.168.1.1",
        "net1": "virtio=BC:24:11:11:11:12,bridge=vmbr1",
    },
    101: {
        "cores": 1,
        "sockets": 2,
        "memory": 2048,
        "boot": "order=scsi0",
        "ostype": "win10",
        "onboot": 0,
        "protection": 1,
        "machine": "pc-q35-8.0",
        "bios": "ovmf",
        "efidisk0": "local-lvm:vm-101-disk-1,size=4M",
        "tpmstate0": "local-lvm:vm-101-disk-2,size=4M,version=v2.0",
        "scsi0": "local-lvm:vm-101-disk-0,size=50G,backup=0,cache=writeback",
        "net0": "virtio=BC:24:11:22:22:22,bridge=vmbr0",
    },
    200: {
        "cores": 1,
        "memory": 1024,
        "ostype": "debian",
        "onboot": 1,
        "rootfs": "local-lvm:vm-200-disk-0,size=10G",
        "net0": "name=eth0,bridge=vmbr0,hwaddr=BC:24:11:33:33:33,ip=192.168.1.200/24,gw=192.168.1.1,ip6=2001:db8::200/64,gw6=2001:db8::1",
    },
}

# Mock guest agent data
MOCK_GUEST_AGENT_OSINFO = {
    100: {
        "result": {
            "name": "Ubuntu",
            "id": "ubuntu",
            "version": "22.04",
            "version-id": "22.04",
            "kernel-release": "5.15.0-89-generic",
            "kernel-version": "#99-Ubuntu SMP Mon Oct 30 20:42:41 UTC 2023",
            "machine": "x86_64",
        },
    },
}

MOCK_GUEST_AGENT_HOSTNAME = {
    100: {
        "result": {
            "host-name": "test-vm-1.example.com",
        },
    },
}

MOCK_GUEST_AGENT_NETWORK = {
    100: {
        "result": [
            {
                "name": "lo",
                "hardware-address": "00:00:00:00:00:00",
                "ip-addresses": [
                    {
                        "ip-address": "127.0.0.1",
                        "ip-address-type": "ipv4",
                        "prefix": 8,
                    },
                    {
                        "ip-address": "::1",
                        "ip-address-type": "ipv6",
                        "prefix": 128,
                    },
                ],
            },
            {
                "name": "ens18",
                "hardware-address": "bc:24:11:11:11:11",
                "ip-addresses": [
                    {
                        "ip-address": "192.168.1.100",
                        "ip-address-type": "ipv4",
                        "prefix": 24,
                    },
                    {
                        "ip-address": "10.0.0.100",
                        "ip-address-type": "ipv4",
                        "prefix": 16,
                    },
                    {
                        "ip-address": "fe80::be24:11ff:fe11:1111",
                        "ip-address-type": "ipv6",
                        "prefix": 64,
                    },
                ],
            },
            {
                "name": "ens19",
                "hardware-address": "bc:24:11:11:11:12",
                "ip-addresses": [
                    {
                        "ip-address": "192.168.2.100",
                        "ip-address-type": "ipv4",
                        "prefix": 24,
                    },
                ],
            },
        ],
    },
}

MOCK_STORAGE_DATA = [
    {
        "storage": "local",
        "type": "dir",
        "content": "vztmpl,iso,backup",
        "path": "/var/lib/vz",
        "shared": 0,
        "active": 1,
        "avail": 536870912000,
        "total": 1073741824000,
        "used": 536870912000,
        "enabled": 1,
        "nodes": "node1,node2",
    },
    {
        "storage": "local-lvm",
        "type": "lvmthin",
        "content": "rootdir,images",
        "thinpool": "data",
        "vgname": "pve",
        "shared": 0,
        "active": 1,
        "avail": 429496729600,
        "total": 536870912000,
        "used": 107374182400,
        "enabled": 1,
        "nodes": "node1,node2",
    },
    {
        "storage": "nfs-backup",
        "type": "nfs",
        "content": "backup",
        "server": "192.168.1.50",
        "export": "/mnt/backup",
        "shared": 1,
        "active": 1,
        "avail": 2147483648000,
        "total": 4294967296000,
        "used": 2147483648000,
        "enabled": 1,
        "nodes": "node1,node2",
    },
]
