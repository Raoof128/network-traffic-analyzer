# Contributing to Network Traffic Analyzer

Thank you for your interest in contributing to the Network Traffic Analyzer! This document provides guidelines and instructions for contributing to this project.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Environment](#development-environment)
- [How to Contribute](#how-to-contribute)
- [Coding Standards](#coding-standards)
- [Testing Requirements](#testing-requirements)
- [Commit Message Guidelines](#commit-message-guidelines)
- [Pull Request Process](#pull-request-process)
- [Code Review Guidelines](#code-review-guidelines)

## Code of Conduct

This project adheres to a Code of Conduct that all contributors are expected to follow. Please read [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) before contributing.

## Getting Started

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/YOUR_USERNAME/network-traffic-analyzer.git
   cd network-traffic-analyzer
   ```
3. **Add the upstream repository**:
   ```bash
   git remote add upstream https://github.com/Raoof128/network-traffic-analyzer.git
   ```
4. **Create a feature branch**:
   ```bash
   git checkout -b feature/your-feature-name
   ```

## Development Environment

### Prerequisites

- Python 3.8 or higher
- pip and virtualenv
- Git
- Docker (optional, for containerized development)

### Setup

1. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dev.txt
   ```

3. **Install pre-commit hooks**:
   ```bash
   pre-commit install
   ```

4. **Verify installation**:
   ```bash
   make test
   make lint
   ```

## How to Contribute

### Reporting Bugs

- Use the [Bug Report template](.github/ISSUE_TEMPLATE/bug_report.md)
- Search existing issues to avoid duplicates
- Include:
  - Clear description of the bug
  - Steps to reproduce
  - Expected vs actual behavior
  - System information (OS, Python version)
  - Relevant logs and error messages

### Suggesting Enhancements

- Use the [Feature Request template](.github/ISSUE_TEMPLATE/feature_request.md)
- Clearly describe the feature and its use case
- Explain why this enhancement would be useful
- Include examples if applicable

### Contributing Code

1. **Check existing issues** or create a new one to discuss your changes
2. **Fork and clone** the repository
3. **Create a feature branch** from `main`
4. **Make your changes** following our coding standards
5. **Add tests** for new functionality
6. **Run the test suite** and ensure all tests pass
7. **Update documentation** as needed
8. **Submit a pull request**

## Coding Standards

### Python Style Guide

We follow **PEP 8** with some modifications:

- **Line length**: Maximum 120 characters
- **Indentation**: 4 spaces (no tabs)
- **Imports**: Grouped and sorted (use `isort`)
- **String quotes**: Double quotes preferred
- **Docstrings**: Google style

### Code Quality Tools

All code must pass the following checks:

```bash
make lint        # Pylint + Flake8
make format      # Black + isort (auto-format)
make type-check  # Mypy type checking
make security    # Bandit security scanning
```

### Type Hints

- All public functions must have type hints
- Use `typing` module for complex types
- Example:
  ```python
  from typing import List, Optional, Dict, Any

  def process_packets(
      packets: List[Packet],
      filter_rule: Optional[str] = None
  ) -> Dict[str, Any]:
      """Process packets and return analysis results."""
      pass
  ```

### Docstrings

All public modules, classes, and functions must have docstrings:

```python
def extract_features(packet: Packet) -> Dict[str, float]:
    """
    Extract statistical features from a network packet.

    Args:
        packet: Scapy packet object to analyze

    Returns:
        Dictionary containing extracted features with feature names as keys
        and numerical values as values

    Raises:
        ValueError: If packet is invalid or missing required layers

    Example:
        >>> from scapy.all import IP, TCP, Ether
        >>> packet = Ether()/IP()/TCP()
        >>> features = extract_features(packet)
        >>> print(features['packet_length'])
        54
    """
    pass
```

## Testing Requirements

### Test Coverage

- **Minimum coverage**: 70% overall
- **New features**: Must have >80% coverage
- **Critical paths**: Must have 100% coverage

### Writing Tests

1. **Unit tests** for individual functions and classes
2. **Integration tests** for cross-module interactions
3. **E2E tests** for complete workflows

```python
# tests/test_feature_extraction.py
import pytest
from features.extractor import FeatureExtractor

class TestFeatureExtractor:
    """Test suite for FeatureExtractor class."""

    def test_extract_basic_features(self, sample_packet):
        """Test basic feature extraction from a packet."""
        extractor = FeatureExtractor()
        features = extractor.extract(sample_packet)

        assert 'packet_length' in features
        assert features['packet_length'] > 0
        assert isinstance(features, dict)
```

### Running Tests

```bash
# Run all tests
make test

# Run with coverage
make test-coverage

# Run specific test file
pytest tests/test_features.py -v

# Run specific test
pytest tests/test_features.py::TestFeatureExtractor::test_extract_basic_features
```

## Commit Message Guidelines

We follow the **Conventional Commits** specification:

### Format

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Types

- **feat**: New feature
- **fix**: Bug fix
- **docs**: Documentation changes
- **style**: Code style changes (formatting, no logic change)
- **refactor**: Code refactoring
- **perf**: Performance improvements
- **test**: Adding or updating tests
- **build**: Build system changes
- **ci**: CI/CD changes
- **chore**: Maintenance tasks

### Examples

```bash
# Feature
feat(detection): add support for custom detection rules

# Bug fix
fix(capture): resolve packet loss on high-speed interfaces

# Documentation
docs(api): add examples for REST API endpoints

# Multiple paragraphs
feat(models): implement ensemble model training

Add support for training ensemble models that combine multiple
base classifiers for improved accuracy.

- Random Forest
- SVM
- Gradient Boosting

Closes #123
```

## Pull Request Process

### Before Submitting

1. **Update your branch** with latest `main`:
   ```bash
   git fetch upstream
   git rebase upstream/main
   ```

2. **Run all checks**:
   ```bash
   make quality    # Linting, formatting, type checking
   make test       # Test suite
   make security   # Security scanning
   ```

3. **Update documentation**:
   - README.md (if adding features)
   - CHANGELOG.md (add entry under "Unreleased")
   - API documentation (if applicable)
   - Docstrings

4. **Squash commits** if needed (keep history clean)

### PR Description Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix (non-breaking change which fixes an issue)
- [ ] New feature (non-breaking change which adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] Documentation update

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] All tests pass locally
- [ ] Test coverage maintained/improved

## Checklist
- [ ] Code follows project style guidelines
- [ ] Self-review completed
- [ ] Comments added for complex code
- [ ] Documentation updated
- [ ] No new warnings generated
- [ ] CHANGELOG.md updated
```

### Review Process

1. **Automated checks** must pass (CI/CD)
2. **At least one approval** from maintainers required
3. **All conversations resolved** before merging
4. **Maintainer will merge** once approved

## Code Review Guidelines

### For Contributors

- Respond to feedback promptly
- Be open to suggestions
- Ask questions if feedback is unclear
- Mark conversations as resolved once addressed

### For Reviewers

- Be respectful and constructive
- Focus on code quality, not personal preferences
- Explain the "why" behind suggestions
- Approve when ready, request changes if needed
- Test locally for complex changes

## Additional Resources

- [README.md](README.md) - Project overview and usage
- [ARCHITECTURE.md](docs/architecture.md) - System architecture
- [API_REFERENCE.md](docs/API_REFERENCE.md) - API documentation
- [GitHub Issues](https://github.com/Raoof128/network-traffic-analyzer/issues) - Bug reports and feature requests

## Questions?

If you have questions about contributing, please:

1. Check existing documentation
2. Search closed issues
3. Open a new issue with the "question" label
4. Join our community discussions

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

Thank you for contributing to Network Traffic Analyzer!
