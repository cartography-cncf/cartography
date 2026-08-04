# LastPass Configuration

## Authentication

Obtain your LastPass CID (account number) and ProvHash by following
[Where can I find the CID and API secret?](https://support.lastpass.com/help/where-can-i-find-the-cid-and-api-secret).
Store each value in a separate environment variable.

```bash
export LASTPASS_CID="<your-cid>"
export LASTPASS_PROVHASH="<your-provhash>"
```

## Configure Cartography

Pass the names of the environment variables with `--lastpass-cid-env-var` and
`--lastpass-provhash-env-var`.

## Run Cartography

```bash
cartography \
  --selected-modules lastpass \
  --lastpass-cid-env-var LASTPASS_CID \
  --lastpass-provhash-env-var LASTPASS_PROVHASH
```

## References

- [LastPass CID and API secret documentation](https://support.lastpass.com/help/where-can-i-find-the-cid-and-api-secret)
