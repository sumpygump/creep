# Makefile
# I created this makefile to streamline the usage of a few common tasks

ccyellow = $(shell echo "\033[33m")
ccend = $(shell tput op)

SRC_PATHS=creepclient qi

# Optional flag to pass into pytest
# Example: `TFLAGS=-v make tests`
TFLAGS?=

help:
	@echo "$(ccyellow)------------------------------------------$(ccend)"
	@echo "$(ccyellow)Creep client makefile$(ccend)"
	@echo "$(ccyellow)------------------------------------------$(ccend)"
	@echo "Usage:"
	@echo "  make environment : provision python virtual environment"
	@echo "  make deps : install python dependencies"
	@echo "  make lint : run linter"
	@echo "  make tests : run python tests, uses optional env var TFLAGS"
	@echo "               e.g. 'TFLAGS=-v make tests' will run in verbose mode"
	@echo "  make coverage : serve up coverage report from last test run"
	@echo

environment:
	@echo "$(ccyellow)> Creating python environment...$(ccend)"
	python3 -m venv .venv
	@echo "Run \`source .venv/bin/activate\` to activate environment"
	@echo "Run \`deactivate\` to deactivate environment"

deps:
	$(if $(value VIRTUAL_ENV),,$(error "First activate environment"))
	@echo "$(ccyellow)> Installing dependencies...$(ccend)"
	pip install -r requirements-dev.txt
	@echo

lint:
	@echo "$(ccyellow)> Running black...$(ccend)"
	black --exclude tools $(SRC_PATHS)
	@echo
	@echo "$(ccyellow)> Running pylint...$(ccend)"
	pylint $(SRC_PATHS)
	@echo

.PHONY: tests
tests:
	$(if $(value VIRTUAL_ENV),,$(error "First activate environment"))
	@echo "$(ccyellow)> Running tests...$(ccend)"
	-coverage run --branch --source=. .venv/bin/pytest $(TFLAGS)
	coverage html --skip-empty
	@echo

coverage:
	$(if $(value VIRTUAL_ENV),,$(error "First activate environment"))
	@echo "$(ccyellow)> Serving coverage report at localhost:8020...$(ccend)"
	cd htmlcov && python3 -m http.server 8020
	@echo
