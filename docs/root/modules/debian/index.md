# Debian Security Tracker

The Debian Security Tracker module ingests the
[Debian security tracker](https://security-tracker.debian.org/tracker/)'s view
of the CVEs already in the graph: for each source package and Debian release,
whether the release is affected, the urgency the Debian security team assigned,
the version that fixed it, and any decision not to issue a security advisory.

Like [CVE Metadata](../cve_metadata/index.md), this module does not import
every CVE. Modules such as Trivy, CrowdStrike, Semgrep, and SentinelOne must
create `CVE` nodes first, and the sync order places `debian` after them. When
the graph has no `CVE` nodes, the module skips the download and removes the
entries of earlier syncs.

## Entries

Each `DebianSecurityTrackerEntry` is one CVE in one source package and one
release, with the ID `<release>|<source package>|<CVE ID>`. A CVE tracked
under several source packages, such as `linux` and `linux-6.12`, has an entry
for each. The export covers the releases the tracker currently follows
(bookworm, trixie, forky and sid when this was written); a release drops out of
it after its end of life.

Entries keep the tracker's own values:

- `status` is `open`, `resolved` or `undetermined`.
- `urgency` is `unimportant`, `low`, `medium`, `high`, `not yet assigned`, or
  `end-of-life` when the package has no security support in that release.
- `fixed_version` is the version that fixed the CVE. The tracker writes `0`
  when the release never shipped the vulnerable code, which `not_affected`
  makes explicit.
- `nodsa` and `nodsa_reason` record a decision not to issue a Debian Security
  Advisory, with the security team's note, for example `Minor issue`.

`release` is the codename the tracker uses. `release_version` is that
release's major version (`12` for bookworm, `13` for trixie), from a mapping
kept in `cartography.intel.common.debian_releases`; it is unset for `sid`.

Entries carry no `CVE` label, because whether one applies to an image depends
on the image's release. They are read for CVE IDs only: the tracker's
`TEMP-` placeholders are skipped.

## Matching entries to images

Entries have no relationship to findings or images. [Trivy](../trivy/index.md)
records the Debian release of each scanned image on its `DEPLOYED`
relationships as `os_release`, normalized from the point release or the
`<codename>/sid` the image reports, so an image's findings match entries on
`cve_id` and `release_version`. Testing and unstable images both report
`<codename>/sid` and match the release in preparation, not `sid`.

The match does not include the source package yet. The tracker keys entries by
source package, Trivy reports binary packages, and Cartography does not record
which source package a binary package was built from. A finding therefore
matches the entry of every source package the tracker lists the CVE under, and
those entries can disagree. Do not combine their `status`, `urgency` or
`not_affected` values for one finding: a matching entry can belong to a source
package the image does not contain.

See [configuration](config.md) to enable the module, [queries](queries.md) for
example queries, and the generated [schema](schema.md) for fields and
relationships.

```{toctree}
config
schema
queries
```
