## Lastpass Configuration

Follow these steps to analyze Lastpass objects with Cartography.

1. Prepare your Lastpass CID & ProvHash key.
    1. Get your CID (account number) and ProvHash from Lastpass [Where can I find the CID and API secret?](https://support.lastpass.com/help/where-can-i-find-the-cid-and-api-secret)
    1. Populate `CARTOGRAPHY_LASTPASS__CID` variable with the CID and `CARTOGRAPHY_LASTPASS__PROVHASH` with Provhash.

### Cartography Configuration

| Name | Type     | Description |
|------|----------|-------------|
| CARTOGRAPHY_LASTPASS__CID | `str` | The Lastpass CID for authentication. |
| CARTOGRAPHY_LASTPASS__PROVHASH | `str` | The Lastpass provhash for authentication. |
