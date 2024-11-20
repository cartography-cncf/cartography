test: test_lint test_unit test_integration

test_lint:
	pre-commit run --all-files --show-diff-on-failure

test_unit:
	pytest -vvv --cov-report term-missing --cov=cartography tests/unit

test_integration:
	pytest -vvv --cov-report term-missing --cov=cartography tests/integration

build_py_pkg: clean
	python -m ensurepip --default-pip --upgrade
	python -m pip install --upgrade build twine
	python -m build
	python -m twine check dist/*

build_docker_image: build_py_pkg
	docker buildx build --provenance=false --platform linux/amd64 --pull --load -t cartography:latest -f Dockerfile.multistage .

clean:
	rm -rf dist
	rm -rf cartography.egg-info

clean_all: clean
	rm -rf .venv
	rm -f Pipfile.lock
	rm -rf .mypy_cache
	rm -rf .pytest_cache
	rm -rf tests/__pycache__
	rm -rf tests/integration/__pycache__
	rm -rf tests/unit/__pycache__
