from digitalocean import Account

ACCOUNT_RESPONSE = Account(
    uuid="123-4567-8789",
    droplet_limit=1234,
    floating_ip_limit=123,
    status="active",
)
