SHELL := /bin/bash
.PHONY: all install test 
lint:
	@echo -e "Running linter"
	@isort microbatcher
	@isort tests
	@black microbatcher
	@black tests
	@echo -e "Running type checker"

test: ## Run the tests.conf
	@poetry run pytest --cov=microbatcher --cov-report html --durations=5 --cov-report term:skip-covered tests/
	
install:
	@poetry install

all: lint test