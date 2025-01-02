test: test_lint test_unit test_integration

test_lint:
	uv run pre-commit run --all-files --show-diff-on-failure

test_unit:
	uv run pytest -vvv --cov-report term-missing --cov=cartography tests/unit

test_integration:
	uv run pytest -vvv --cov-report term-missing --cov=cartography tests/integration
