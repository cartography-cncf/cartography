## Duo Configuration

Follow these steps to analyze Duo objects with Cartography.

1. Prepare a [admin api creds](https://duo.com/docs/adminapi).
1. Set the Duo api host name in the `CARTOGRAPHY_DUO__API_HOSTNAME` variable.
1. Populate environment variables `CARTOGRAPHY_DUO__API_KEY` with the api key and `CARTOGRAPHY_DUO__API_SECRET` zithapi secret.

### Cartography Configuration

| Name | Type     | Description |
|------|----------|-------------|
| CARTOGRAPHY_DUO__API_KEY | `str` | The Duo api key. |
| CARTOGRAPHY_DUO__API_SECRET | `str` | The Duo api secret. |
| CARTOGRAPHY_DUO__API_HOSTNAME | `str` | The Duo api hostname. |
