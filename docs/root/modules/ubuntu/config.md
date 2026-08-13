# Ubuntu Security Configuration

## Prerequisites

The default Ubuntu Security API is public and does not require credentials.
Cartography must be able to make HTTPS requests to `https://ubuntu.com`.

## Configure Cartography

Enable ingestion with `--ubuntu-security-enabled`.

By default, Cartography requests CVEs and notices from
`https://ubuntu.com`. To use a compatible mirror or proxy, set its base URL
with `--ubuntu-security-api-url`. The server must expose these endpoints:

- `/security/cves.json`
- `/security/notices.json`

## Run Cartography

```bash
cartography \
  --selected-modules ubuntu \
  --ubuntu-security-enabled
```

To use a different API base URL:

```bash
cartography \
  --selected-modules ubuntu \
  --ubuntu-security-enabled \
  --ubuntu-security-api-url https://ubuntu-security.example.com
```
