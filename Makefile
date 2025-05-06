test: test_lint test_unit test_integration

test_lint:
	pre-commit run --all-files --show-diff-on-failure

test_unit:
	pytest -vvv --cov-report term-missing --cov=cartography tests/unit

test_integration:
	pytest -vvv --cov-report term-missing --cov=cartography tests/integration

build-docs:
	./docs/build.sh
