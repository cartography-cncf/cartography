test: test_lint test_unit test_integration

test_lint:
	uv run --frozen pre-commit run --all-files --show-diff-on-failure

test_unit:
	uv run --frozen pytest -vvv --cov-report term-missing --cov=cartography tests/unit

test_integration:
	uv run --frozen pytest -vvv --cov-report term-missing --cov=cartography tests/integration
