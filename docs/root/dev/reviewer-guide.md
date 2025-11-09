# Cartography Reviewer Guide

This checklist helps reviewers ensure that PRs meet Cartography's standards and best practices. Not all sections apply to every PR - reviewers should focus on relevant sections based on the PR type.

## A Note on Constructive Reviews

Cartography is an open-source project built by volunteers who generously contribute their time and expertise. Many contributors work on Cartography outside of their regular work hours, driven by passion for the project and desire to give back to the community.

**When reviewing pull requests, please remember:**

- **Be kind and respectful** - Contributors are offering their time freely. Treat their work with appreciation and respect.
- **Be constructive** - Focus on helping improve the code, not criticizing the person. Frame feedback as suggestions for improvement.
- **Be patient** - Contributors may be learning or working in their spare time. Allow time for responses and iterations.
- **Be collaborative** - Reviews are a conversation, not a gate. Work together to find the best solution.
- **Be appreciative** - Thank contributors for their time and effort. Positive feedback encourages continued participation.

Code reviews should foster a welcoming environment where contributors feel supported and motivated to continue contributing. A respectful, collaborative review process benefits everyone and strengthens our community.

Thank you for helping make Cartography better! 🙏


## Table of Contents

- [General](#general) - Applies to all PRs
- [New Intel Module](#new-intel-module) - For new data source integrations
- [Existing Intel Module Changes](#existing-intel-module-changes) - Modifications to existing modules
- [Breaking Changes](#breaking-changes) - Changes affecting existing users
- [Data Model Refactoring](#data-model-refactoring) - Legacy code to data model conversions
- [Bug Fixes](#bug-fixes) - Issue resolution
- [Reviewer Notes](#reviewer-notes) - Guidance for reviewers
- [Additional Resources](#additional-resources) - Helpful links and documentation

---

## General

Applies to all pull requests.

### Code Quality
- [ ] Code follows Python 3.9+ style (use built-in types like `dict[str, Any]`, not `Dict[str, Any]`)
- [ ] Code follows Python 3.9+ style (use `str | None` instead of `Optional[str]`)
- [ ] Linter passes without errors (`make lint`)
- [ ] No unnecessary emojis added to code or output (unless explicitly requested)
- [ ] Error handling is appropriate: specific exceptions are caught, not base `Exception`
- [ ] Required fields are accessed directly (`data["field"]`) to fail fast if missing
- [ ] Optional fields use `.get()` with None default, not empty strings

### Testing
- [ ] Tests pass locally (`pytest tests/`)
- [ ] Unit tests added/updated for new logic (if applicable)
- [ ] Integration tests added/updated that call the `sync()` function directly
- [ ] Integration tests use `check_nodes()` and `check_rels()` helpers instead of raw Neo4j queries
- [ ] Tests focus on **outcomes** (data in graph) not **implementation details** (mock call counts)
- [ ] Tests mock external APIs appropriately (AWS, Azure, third-party services)
- [ ] Tests use realistic mock data in `tests/data/` directory
- [ ] No tests for cleanup functions unless specific concern exists (data model handles this)

### Git Hygiene
- [ ] PR description explains the "why" behind changes
- [ ] Related issues are linked in PR description
- [ ] Branch is up to date with master

---

## New Intel Module

For PRs introducing a new data source integration.

### Configuration
- [ ] CLI arguments added to `cartography/cli.py`
- [ ] Config fields added to `cartography/config.py` Config dataclass
- [ ] Configuration validation implemented in module's `start_*_ingestion()` function
- [ ] Module gracefully skips if not configured (logs info message, doesn't fail)
- [ ] Environment variable pattern used for API keys/secrets

### Module Structure
- [ ] Follows standard sync pattern: `get()` → `transform()` → `load()` → `cleanup()`
- [ ] Main entry point at `cartography/intel/module_name/__init__.py` with `start_*_ingestion()`
- [ ] Domain-specific sync modules in separate files (e.g., `users.py`, `devices.py`)
- [ ] All sync functions decorated with `@timeit`

### Get Functions
- [ ] `get()` functions are "dumb" - just fetch and return data
- [ ] No try/except blocks in `get()` - let errors propagate
- [ ] For AWS modules, `@aws_handle_regions` decorator used
- [ ] Timeouts configured for HTTP requests (e.g., `timeout=(60, 60)`)
- [ ] API responses raise exceptions on failure (e.g., `response.raise_for_status()`)

### Transform Functions
- [ ] Required fields accessed directly: `data["id"]` (raises KeyError if missing)
- [ ] Optional fields use `.get()`: `data.get("name")` (returns None if missing)
- [ ] Consistent use of `None` for missing values, not empty strings
- [ ] No manual datetime parsing (Neo4j handles ISO 8601 and datetime objects natively)
- [ ] One-to-many relationships transformed to ID lists where needed

### Data Model
- [ ] Node schemas defined in `cartography/models/module_name/`
- [ ] All node properties inherit from `CartographyNodeProperties`
- [ ] Required properties: `id` (unique identifier), `lastupdated` (set_in_kwargs=True)
- [ ] Node schemas inherit from `CartographyNodeSchema` with proper labels
- [ ] `sub_resource_relationship` points to tenant-like object (Account, Project, Organization, etc.)
- [ ] NOT pointing to non-tenant resources (avoid sub_resource_relationship to task definitions, containers, etc.)
- [ ] `scoped_cleanup` defaults to `True` (tenant-scoped resources) or explicitly set to `False` only for global data (CVEs, threat intel)
- [ ] Relationship schemas properly defined with `target_node_label`, `target_node_matcher`, `direction`, `rel_label`, `properties`
- [ ] Relationship directions correct: `OUTWARD` for `(:Source)-[:REL]->(:Target)`, `INWARD` for `(:Source)<-[:REL]-(:Target)`
- [ ] Extra indexes specified with `extra_index=True` on frequently queried fields
- [ ] Type hints present on all dataclass fields
- [ ] All dataclasses use `frozen=True`

### Load Functions
- [ ] Uses `cartography.client.core.tx.load()` function
- [ ] Loads tenant/account nodes before child resources
- [ ] Passes `lastupdated=update_tag` to all `load()` calls
- [ ] Passes tenant ID via kwargs (e.g., `TENANT_ID=tenant_id`)
- [ ] MatchLinks only used when absolutely necessary (connecting existing nodes or rich relationship properties)
- [ ] MatchLink relationships include required properties: `lastupdated`, `_sub_resource_label`, `_sub_resource_id`

### Cleanup Functions
- [ ] Uses `GraphJob.from_node_schema()` for standard cleanups
- [ ] Uses `GraphJob.from_matchlink()` for MatchLink cleanups
- [ ] Cleanup receives `common_job_parameters` dict with `UPDATE_TAG` and tenant ID
- [ ] No manual cleanup queries (data model handles this)

### Ontology Integration (if applicable)
- [ ] Mapping defined in `cartography/models/ontology/mapping/data/{kind_of_nodes}.py`
- [ ] User nodes include `UserAccount` extra label
- [ ] Device nodes define relationship to `Device` ontology node
- [ ] Primary identifiers marked as `required=True` (email for users, hostname for devices)
- [ ] Mapping registered in `ALL_USER_MAPPINGS` or `ALL_DEVICE_MAPPINGS`
- [ ] `eligible_for_source` set appropriately (False if insufficient data for ontology node creation)
- [ ] Integration tested with ontology sync in tests

### Documentation
- [ ] Schema documented in `docs/root/modules/module_name/schema.md`
- [ ] Configuration documented in `docs/root/modules/module_name/config.md`
- [ ] Overview documented in `docs/root/modules/module_name/index.md`
- [ ] Module schema added to `docs/root/usage/schema.md`
- [ ] Module added to README.md supported platforms list
- [ ] Node and relationship diagrams included if helpful

### Test Coverage
- [ ] Mock data created in `tests/data/module_name/`
- [ ] Integration tests in `tests/integration/cartography/intel/module_name/`
- [ ] Tests verify nodes created with correct properties
- [ ] Tests verify relationships created between expected nodes
- [ ] Tests verify tenant/account nodes created
- [ ] Unit tests in `tests/unit/cartography/intel/module_name/` only if transform logic is complex
- [ ] Ontology integration tested if applicable

---

## Existing Intel Module Changes

For modifications to existing intel modules.

### Backwards Compatibility
- [ ] Existing node labels unchanged (unless breaking change is intentional and documented)
- [ ] Existing relationship types unchanged (unless breaking change is intentional and documented)
- [ ] New properties added don't break existing queries
- [ ] Default values provided for new optional properties

### Data Model Consistency
- [ ] Changes follow existing patterns in the module
- [ ] Property names consistent with module conventions
- [ ] Relationship directions consistent with module patterns
- [ ] Index additions appropriate (don't over-index)

### Testing
- [ ] Existing integration tests still pass
- [ ] New tests added for new functionality
- [ ] Tests updated if behavior changes
- [ ] Edge cases covered (missing data, API errors, etc.)

### Schema Updates
- [ ] Schema documentation updated for new/changed nodes
- [ ] Schema documentation updated for new/changed relationships
- [ ] Schema documentation updated for new/changed properties
- [ ] Example queries updated if needed

---

## Breaking Changes

For changes that affect existing users' graphs or queries.

### Change Documentation
- [ ] Breaking changes clearly documented in PR description
- [ ] Migration path provided for users
- [ ] Affected queries/use cases identified

### Communication
- [ ] Breaking change rationale explained
- [ ] Alternative approaches considered and documented
- [ ] Community notified (Slack, GitHub discussion) if major change

### Testing
- [ ] Tests demonstrate before/after behavior
- [ ] Migration path tested if provided
- [ ] Edge cases during migration covered

---

## Data Model Refactoring

For converting legacy code to use the modern data model (NodeSchema/RelSchema).

### Pre-Refactoring Requirements
- [ ] **CRITICAL**: Integration test exists and passes BEFORE any changes
- [ ] Integration test calls the `sync()` function directly
- [ ] Test covers all node types and relationships being refactored
- [ ] Mock data in `tests/data/` is realistic and complete

### Data Model Conversion
- [ ] Node schemas created in `cartography/models/module_name/`
- [ ] Properties migrated from Cypher to `CartographyNodeProperties`
- [ ] Relationships migrated to `CartographyRelSchema` objects
- [ ] `sub_resource_relationship` points to correct tenant-like object
- [ ] One-to-many relationships use `one_to_many=True` parameter
- [ ] MatchLinks used only when necessary (avoid if possible)

### Code Changes
- [ ] Legacy `load_*` functions converted to use `cartography.client.core.tx.load()`
- [ ] Legacy Cypher queries removed from load functions
- [ ] Legacy `cleanup_*` functions converted to use `GraphJob.from_node_schema()`
- [ ] Legacy cleanup JSON files removed from `cartography/data/jobs/cleanup/`
- [ ] Legacy index entries removed from `cartography/data/indexes.cypher`
- [ ] Transform functions updated to match new schema property names

### Testing & Validation
- [ ] Integration tests pass after conversion
- [ ] Test assertions updated if minor behavior changes
- [ ] No functional regressions introduced
- [ ] Cleanup behavior verified (stale nodes removed correctly)
- [ ] Performance not significantly degraded

### Cleanup
- [ ] All legacy Cypher removed
- [ ] All legacy cleanup JSON files deleted
- [ ] All legacy index entries removed
- [ ] No orphaned code left behind
- [ ] Comments/TODOs removed or updated

---

## Bug Fixes

For PRs that resolve issues or bugs.

### Issue Resolution
- [ ] Issue clearly referenced in PR (fixes #XXX)
- [ ] Root cause identified and explained
- [ ] Fix addresses root cause, not symptoms
- [ ] Similar issues in codebase checked and fixed if found

### Testing
- [ ] Regression test added to prevent recurrence
- [ ] Test reproduces original bug
- [ ] Test passes with fix applied
- [ ] Related edge cases tested

### Error Handling
- [ ] Fail-fast approach used (don't paper over errors)
- [ ] Appropriate exception types caught (not base Exception)
- [ ] Error messages clear and actionable
- [ ] No silent failures introduced

### Code Quality
- [ ] Fix is minimal and focused on the issue
- [ ] No unnecessary refactoring mixed in
- [ ] Code style consistent with surrounding code
- [ ] No new technical debt introduced

---

## Reviewer Notes

### When to Request Changes
- Tests failing or missing
- Security concerns identified
- Code quality issues (hard to maintain)
- Documentation inadequate
- Breaking changes without clear justification
- Data model antipatterns (e.g., sub_resource_relationship to non-tenant)

### When to Approve
- All relevant checklist items addressed
- Tests pass and provide good coverage
- Code follows Cartography patterns and conventions
- Documentation clear and complete
- No security or correctness concerns

### Review Focus Areas
1. **Correctness**: Does the code do what it claims?
2. **Testing**: Are tests comprehensive and meaningful?
3. **Maintainability**: Will future developers understand this?
4. **Performance**: Are there obvious performance issues?
5. **Security**: Any security vulnerabilities introduced?
6. **Documentation**: Can users/developers find what they need?

---

## Additional Resources

- [Writing Intel Modules Guide](https://cartography-cncf.github.io/cartography/dev/writing-intel-modules.html)
- [Developer Guide](https://cartography-cncf.github.io/cartography/dev/developer-guide.html)
- [AGENTS.md](AGENTS.md) - Comprehensive guide for AI-assisted development
- [Community Slack](https://cloud-native.slack.com/archives/cartography) - #cartography channel
