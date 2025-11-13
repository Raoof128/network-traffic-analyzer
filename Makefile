.PHONY: help install install-dev clean lint format type-check security test test-coverage pre-commit run-analyzer docker-build docker-run

# Variables
PYTHON := python3
PIP := $(PYTHON) -m pip
PYTEST := $(PYTHON) -m pytest
PYLINT := $(PYTHON) -m pylint
MYPY := $(PYTHON) -m mypy
FLAKE8 := $(PYTHON) -m flake8
BLACK := $(PYTHON) -m black
ISORT := $(PYTHON) -m isort
BANDIT := $(PYTHON) -m bandit

# Directories
SRC_DIRS := capture features models detection visualization config utils
TEST_DIR := tests
ALL_DIRS := $(SRC_DIRS) $(TEST_DIR) analyzer.py train_model.py

# Default target
help:
	@echo "Network Traffic Analyzer - Development Commands"
	@echo "================================================"
	@echo ""
	@echo "Setup:"
	@echo "  make install          - Install production dependencies"
	@echo "  make install-dev      - Install development dependencies"
	@echo ""
	@echo "Code Quality:"
	@echo "  make lint             - Run all linters (pylint + flake8)"
	@echo "  make format           - Format code with black and isort"
	@echo "  make type-check       - Run mypy type checking"
	@echo "  make security         - Run security checks with bandit"
	@echo "  make quality          - Run all quality checks"
	@echo ""
	@echo "Testing:"
	@echo "  make test             - Run all tests"
	@echo "  make test-coverage    - Run tests with coverage report"
	@echo "  make test-fast        - Run tests without slow marks"
	@echo ""
	@echo "Pre-commit:"
	@echo "  make pre-commit-install - Install pre-commit hooks"
	@echo "  make pre-commit-run     - Run pre-commit on all files"
	@echo ""
	@echo "Docker:"
	@echo "  make docker-build     - Build Docker image"
	@echo "  make docker-run       - Run analyzer in Docker"
	@echo ""
	@echo "Cleanup:"
	@echo "  make clean            - Remove build artifacts and cache"
	@echo ""

# Installation
install:
	$(PIP) install -r requirements.txt

install-dev:
	$(PIP) install -r requirements-dev.txt
	make pre-commit-install

# Linting
lint:
	@echo "Running pylint..."
	$(PYLINT) $(SRC_DIRS) analyzer.py train_model.py --rcfile=.pylintrc || true
	@echo ""
	@echo "Running flake8..."
	$(FLAKE8) $(ALL_DIRS) || true

format:
	@echo "Running isort..."
	$(ISORT) $(ALL_DIRS) --profile black --line-length 120
	@echo ""
	@echo "Running black..."
	$(BLACK) $(ALL_DIRS) --line-length 120

format-check:
	@echo "Checking isort..."
	$(ISORT) $(ALL_DIRS) --profile black --line-length 120 --check-only
	@echo ""
	@echo "Checking black..."
	$(BLACK) $(ALL_DIRS) --line-length 120 --check

type-check:
	@echo "Running mypy type checking..."
	$(MYPY) $(SRC_DIRS) analyzer.py train_model.py --config-file mypy.ini || true

security:
	@echo "Running bandit security checks..."
	$(BANDIT) -r $(SRC_DIRS) analyzer.py train_model.py -c .bandit.yaml || true

quality: lint type-check security
	@echo ""
	@echo "All quality checks complete!"

# Testing
test:
	$(PYTEST) $(TEST_DIR) -v

test-coverage:
	$(PYTEST) $(TEST_DIR) --cov=. --cov-report=html --cov-report=term

test-fast:
	$(PYTEST) $(TEST_DIR) -v -m "not slow"

test-watch:
	$(PYTEST) $(TEST_DIR) -v --looponfail

# Pre-commit hooks
pre-commit-install:
	pre-commit install
	@echo "Pre-commit hooks installed!"

pre-commit-run:
	pre-commit run --all-files

pre-commit-update:
	pre-commit autoupdate

# Docker
docker-build:
	docker build -t network-traffic-analyzer:latest .

docker-run:
	docker run -it --rm --network host --cap-add=NET_ADMIN \
		network-traffic-analyzer:latest

docker-shell:
	docker run -it --rm --network host --cap-add=NET_ADMIN \
		network-traffic-analyzer:latest /bin/bash

# Cleanup
clean:
	@echo "Cleaning up..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "build" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "dist" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type f -name "*.pyo" -delete 2>/dev/null || true
	find . -type f -name ".coverage" -delete 2>/dev/null || true
	rm -rf htmlcov/ .tox/ .eggs/
	@echo "Cleanup complete!"

clean-logs:
	rm -rf logs/*.log
	@echo "Logs cleaned!"

# Development
run-analyzer:
	sudo $(PYTHON) analyzer.py --mode realtime --interface eth0

run-tests-verbose:
	$(PYTEST) $(TEST_DIR) -vv -s

# Documentation
docs:
	cd docs && make html

docs-serve:
	cd docs/_build/html && $(PYTHON) -m http.server 8000

# Release
build:
	$(PYTHON) setup.py sdist bdist_wheel

upload-test:
	$(PYTHON) -m twine upload --repository testpypi dist/*

upload:
	$(PYTHON) -m twine upload dist/*
