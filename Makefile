.PHONY: lint type test ci install

install:
	pip install -r requirements/dev.txt

lint:
	ruff check .
	ruff format .

type:
	mypy .

test:
	pytest

ci:
	ruff check .
	ruff format --check .
	mypy .
	pytest
