# Debian Security Tracker Configuration

## Prerequisites

The Debian security tracker's data is public and needs no credentials.
Cartography must be able to make HTTPS requests to
`https://security-tracker.debian.org`.

Run a module that creates `CVE` nodes, such as Trivy, before this one or in an
earlier sync.

## Configure Cartography

Enable ingestion with `--debian-security-tracker-enabled`.

Each sync downloads the tracker's JSON export once, about 80 MB, and reads it
as a stream, keeping only the records of CVEs in the graph. It is not written
to disk. If the download fails, or the document is truncated, malformed or
holds no vulnerability records, the module raises an error before it changes
the graph, so the entries of the previous sync are kept.

The download URL is the module constant `DEBIAN_SECURITY_TRACKER_URL` in
`cartography.intel.debian.tracker`. A deployment that wraps Cartography can
point it at a mirror or caching proxy that serves the same document.

## Run Cartography

```bash
cartography \
  --selected-modules debian \
  --debian-security-tracker-enabled
```

## References

- [Debian security tracker](https://security-tracker.debian.org/tracker/)
- [Security tracker JSON export](https://security-tracker.debian.org/tracker/data/json)
- [Debian releases](https://www.debian.org/releases/)
