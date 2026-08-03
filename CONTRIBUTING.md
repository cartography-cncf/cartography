# Contributing to Cartography

Thank you for contributing to Cartography. Contributions include code,
documentation, issue reports, reviews, and helping users in public community
channels. Contributors do not need repository write access.

All contributors must follow the [CNCF Code of Conduct](CODE_OF_CONDUCT.md).

## Start Working Without Waiting for Assignment

Cartography does not assign issues to contributors. You do not need to ask for
permission or wait for approval before working on an open issue. Start the work
and open a pull request when it is ready.

If implementation details are unclear, discuss them in the `#cartography`
channel on [CNCF Slack](https://slack.cncf.io/) or in the issue. A discussion
does not reserve the issue, and multiple contributors may explore the same
problem. Maintainers will review the pull request that best addresses the
project's needs.

For larger changes, an issue or discussion can help establish context and
surface design constraints, but it is not an authorization step.

## Report Bugs, Request Features, and Discuss Changes

- Use [GitHub Issues](https://github.com/cartography-cncf/cartography/issues)
  for reproducible bugs and concrete feature requests.
- Use [GitHub Discussions](https://github.com/cartography-cncf/cartography/discussions)
  for broader design or usage questions.
- Do not report security vulnerabilities in a public issue. Follow
  [SECURITY.md](SECURITY.md) instead.

## Development Setup

### Requirements

- Python 3.13
- [uv](https://docs.astral.sh/uv/)
- Docker for integration tests

### Install the repository

```bash
git clone https://github.com/cartography-cncf/cartography.git
cd cartography
uv sync --frozen --dev
```

Verify the local installation:

```bash
uv run cartography --help
```

The [developer guide](docs/root/dev/developer-guide.md) contains additional
setup options and examples for running Cartography from source.

## Prioritize User Impact

Maintainers review Cartography mostly in their limited personal time. Submit a
polished change that makes its user value clear on the first review pass.

- Explain the concrete user need and how the change addresses it. Closing an
  issue is not, by itself, a user outcome.
- Prefer a small, complete solution over speculative abstractions. Follow KISS:
  simple code is easier to review, operate, and evolve.
- Low-impact maintenance can be valid, but it may wait behind fixes and
  features that materially help users.
- Read the existing documentation and improve it when your change reveals a
  relevant gap.
- Review the complete diff before submission. Remove debug code, unrelated
  edits, generated artifacts, and accidental formatting changes.

## Make a Focused Change

- Keep the pull request limited to one problem or closely related set of
  changes.
- Add or update tests that demonstrate the intended behavior.
- Update user-facing documentation when behavior or configuration changes.
- Follow existing module and data-model patterns. The
  [intel module guide](docs/root/dev/writing-intel-modules.md) describes the
  current `get`, `transform`, `load`, and cleanup architecture.
- Do not include unrelated formatting, generated files, or refactors.

### Data-model and schema changes

Schema pages under `docs/root/modules/*/schema.md` are generated during the
documentation build. Do not edit or commit generated schema pages. Update model
docstrings and `PropertyRef.description` values instead, then build the
documentation to verify the generated result.

When adding or changing a synced entity:

- use the declarative node and relationship schemas;
- include integration tests for nodes, properties, and relationships;
- document new configuration or permissions in the module's `config.md`;
- test the connector against a real provider environment and include sanitized
  evidence in the pull request.

### Connector changes require real-environment testing

Every addition or modification to an intel connector must be tested against a
real cloud, SaaS, or provider environment. Mocked unit tests and a local Neo4j
integration test are required where appropriate, but they are not sufficient
on their own to prove that a connector works with the provider API.

Include sanitized evidence in the pull request:

- sync logs showing the relevant job starting and completing without errors;
- counts of the nodes or relationships loaded;
- a query result or screenshot demonstrating the expected graph behavior when
  it adds useful evidence.

Remove credentials, tokens, personal data, account identifiers, and other
sensitive values before posting evidence.

A connector pull request without real-environment evidence will be labeled
`needs-tests` and will not be reviewed. If the evidence is not added within 30
days, the pull request may be closed.

## AI-Assisted Contributions

AI tools are welcome, but the contributor remains responsible for every line
submitted. Raw model output is not a finished contribution.

- Give the tool enough repository context to follow Cartography's current
  architecture and conventions.
- Review the complete output critically and remove unnecessary complexity.
- Do not submit code you do not understand.
- Verify API assumptions against authoritative documentation and a real
  environment.
- Run the required tests yourself and inspect their results.
- Make sure the change adds concrete user value rather than producing code or
  prose for its own sake.

Maintainers do not have capacity to validate an AI-generated implementation on
the contributor's behalf. A smaller change that is understood, tested, and
well explained is more valuable than a large unverified contribution.

## Run Tests

Run the checks relevant to your change:

```bash
make test_lint
make test_unit
make test_integration
```

Run the complete suite with:

```bash
make test
```

Integration tests start a disposable Neo4j test container by default, so
Docker must be running. If `NEO4J_URL` is set, integration tests use that
database and delete all nodes from it. Never point `NEO4J_URL` at a database
containing data you need.

For a targeted test:

```bash
uv run pytest tests/integration/cartography/intel/aws/iam/test_iam.py
uv run pytest tests/integration/cartography/intel/aws/iam/test_iam.py::test_load_groups
```

### Build documentation

For documentation or model changes:

```bash
uv sync --group doc
uv run ./docs/build.sh
```

The generated site is written to `generated/docs`.

## Sign Off Every Commit

Cartography uses the [Developer Certificate of Origin](https://developercertificate.org/).
Every commit must contain a `Signed-off-by` trailer certifying that you have the
right to submit the contribution.

Create signed-off commits with:

```bash
git commit -s -m "Describe the change"
```

The trailer uses the name and email from the commit author:

```text
Signed-off-by: Your Name <you@example.com>
```

Before pushing, inspect the commit message:

```bash
git log -1 --format=%B
```

If a commit is missing the trailer, follow the DCO check's instructions. Do not
copy another person's sign-off or add a sign-off for a contribution you do not
have the right to submit.

## Open a Pull Request

Open the pull request against the default branch and complete the repository's
pull request template. Include:

- what changed and why;
- a linked issue when one exists;
- the tests and documentation checks you ran;
- any migration or compatibility impact;
- proof of functionality appropriate to the change.

Draft pull requests are welcome for work that needs early technical feedback.
Maintainers may request changes to correctness, tests, compatibility,
documentation, or scope before merging.

By contributing, you agree that your contribution is licensed under the
project's [Apache License 2.0](LICENSE).
