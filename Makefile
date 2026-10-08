.PHONY: test test-e2e run migrate upgrade current

test:
	python -m pytest tests/ -q --ignore=tests/e2e

test-e2e:
	python -m pytest tests/e2e -q

run:
	python run.py

migrate:
	flask db migrate

upgrade:
	flask db upgrade

current:
	flask db current
