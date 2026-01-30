from digitalocean import Droplet
from digitalocean import Image
from digitalocean import Region

DROPLETS_RESPONSE = [
    Droplet(
        id="12345678",
        name="test-droplet-1",
        locked=False,
        status="active",
        features=[],
        region=Region(slug="nyc1").__dict__,
        created_at="2021-03-03T21:29:35Z",
        image=Image(slug="ubuntu-18-04-x64").__dict__,
        size_slug="s-1vcpu-2gb",
        kernel=None,
        tags=[],
        volume_ids=[
            "dfa32d234-2418-112b-af81-0a584fe1449b9",
            "cca32d234-2418-112b-af81-12ab4fe1449b9",
        ],
        vpc_uuid="123445bc-dcd4-12e8-80bc-3dfea149fba1",
        ip_address="30.1.2.3",
        ip_v6_address="",
        private_ip_address="192.128.10.1",
    ),
]
