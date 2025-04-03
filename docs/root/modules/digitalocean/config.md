## Configuration

Follow these steps to analyze GitHub repos and other objects with Cartography.

1. Prepare your DigitalOcean credentials. Visit [official docs](https://cloud.digitalocean.com/account/api/tokens) for
more up to date info.
    1. Login into your DigitalOcean Account
    1. Visit Account -> API -> Tokens section
    1. Click on `Generate New Token` to create a personal access token
    1. Make sure the scope of the token is set to `READ`
1. Populate the `CARTOGRAPHY_DIGITALOCEAN__TOKEN` environment variable with the access token generated in the previous step.
1. `Cartography` will then load your graph with data from the account linked to the token you specified.

### Cartography Configuration

| Name | Type     | Description |
|------|----------|-------------|
| CARTOGRAPHY_DIGITALOCEAN__TOKEN | `str` | The DigitalOcean access token. |
