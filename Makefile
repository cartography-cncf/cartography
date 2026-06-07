PYTEST_COV_FLAGS := --cov=cartography --cov-report term-missing
PYTEST_COV_BRANCH_FLAGS := $(PYTEST_COV_FLAGS) --cov-branch

test: test_lint test_unit test_integration

test_lint:
	uv run --frozen pre-commit run --all-files --show-diff-on-failure

test_unit:
	uv run --frozen pytest -vvv $(PYTEST_COV_FLAGS) tests/unit

test_integration:
	uv run --frozen pytest -vvv $(PYTEST_COV_FLAGS) tests/integration

test_coverage:
	rm -f .coverage .coverage.unit .coverage.integration coverage.xml
	COVERAGE_FILE=.coverage.unit uv run --frozen pytest -vvv $(PYTEST_COV_BRANCH_FLAGS) tests/unit
	COVERAGE_FILE=.coverage.integration uv run --frozen pytest -vvv $(PYTEST_COV_BRANCH_FLAGS) tests/integration
	uv run --frozen coverage combine .coverage.unit .coverage.integration
	uv run --frozen coverage xml -o coverage.xml
	uv run --frozen coverage report --show-missing
