# Testing Guide for Theo-van-Gogh

## Overview

This project uses **pytest** for testing with comprehensive coverage of core functionality.

## Setup

### Install Test Dependencies

```bash
# Activate your virtual environment
source venv/bin/activate

# Install test dependencies
pip install -r requirements-dev.txt
```

## Running Tests

### Run All Tests
```bash
pytest
```

### Run with Coverage
```bash
pytest --cov=src --cov=config --cov-report=html
```

Then open `htmlcov/index.html` in your browser to see coverage report.

### Run Specific Test Files
```bash
pytest tests/test_file_manager.py
pytest tests/test_upload_tracker.py
```

### Run Tests by Marker
```bash
pytest -m unit              # Only unit tests
pytest -m integration       # Only integration tests
pytest -m "not slow"        # Skip slow tests
pytest -m file_ops          # Only file operation tests
```

### Run Tests in Parallel
```bash
pytest -n auto  # Use all available CPU cores
pytest -n 4     # Use 4 cores
```

### Verbose Output
```bash
pytest -v      # Verbose
pytest -vv     # Very verbose
pytest -s      # Show print statements
```

## Test Structure

```
tests/
├── conftest.py              # Shared fixtures
├── test_file_manager.py     # FileManager tests
├── test_upload_tracker.py   # UploadTracker tests
├── test_file_organizer.py   # FileOrganizer tests
├── test_metadata_manager.py # MetadataManager tests (TODO)
├── test_cli_interface.py    # CLI tests (TODO)
└── test_integration.py      # End-to-end tests (TODO)
```

## Test Markers

Tests are organized with markers for selective running:

- `@pytest.mark.unit` - Fast unit tests
- `@pytest.mark.integration` - Integration tests
- `@pytest.mark.cli` - CLI interface tests
- `@pytest.mark.file_ops` - File operation tests
- `@pytest.mark.slow` - Slow-running tests
- `@pytest.mark.api` - Tests using external APIs

## Coverage Goals

- **Target**: >70% code coverage
- **Critical modules**: >80% coverage
- **CI fails if**: Coverage drops below 70%

View current coverage:
```bash
pytest --cov=src --cov-report=term-missing
```

## GitHub Actions CI/CD

Tests run automatically on:
- Every push to `main` or `develop`
- Every pull request

The CI pipeline:
1. Tests on Python 3.9, 3.10, 3.11, 3.12
2. Runs linting (flake8)
3. Runs type checking (mypy)
4. Runs full test suite with coverage
5. Uploads coverage to Codecov
6. Runs security scans (safety, bandit)

### Add Status Badge to README

```markdown
![Tests](https://github.com/YOUR_USERNAME/Theo-van-Gogh/workflows/Theo-van-Gogh%20CI/badge.svg)
```

## Resources

- [pytest documentation](https://docs.pytest.org/)
- [pytest-cov documentation](https://pytest-cov.readthedocs.io/)
- [Coverage.py](https://coverage.readthedocs.io/)
