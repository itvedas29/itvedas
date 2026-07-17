# Contributing to ITVedas

Thank you for your interest in contributing to ITVedas! This document provides guidelines and instructions for contributing.

## Code of Conduct

- Be respectful and inclusive
- Provide constructive feedback
- Focus on improvements, not criticisms
- Help others learn and grow

## How to Contribute

### Reporting Bugs

1. Check existing issues to avoid duplicates
2. Provide detailed description of the bug
3. Include steps to reproduce
4. Provide expected vs actual behavior
5. Include relevant system information

**Bug Report Template:**
```
**Title**: One-line summary

**Description**: Detailed description

**Steps to Reproduce**:
1. Step one
2. Step two
3. Step three

**Expected Behavior**: What should happen

**Actual Behavior**: What actually happens

**Environment**:
- OS: 
- Browser: 
- Version: 
```

### Suggesting Features

1. Check existing issues/discussions
2. Clearly describe the feature
3. Explain the use case
4. Describe expected benefits
5. Propose implementation if possible

**Feature Request Template:**
```
**Title**: Feature title

**Description**: What would you like to see?

**Use Case**: Why is this needed?

**Benefits**: What problems does this solve?

**Implementation**: How could this be done?
```

### Submitting Pull Requests

1. Fork the repository
2. Create feature branch: `git checkout -b feature/description`
3. Make changes with clear commit messages
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit pull request with detailed description

**PR Guidelines:**
- Keep PRs focused (single feature per PR)
- Write clear commit messages
- Reference related issues
- Include tests
- Update documentation
- Follow code style

## Development Setup

### Prerequisites
- Python 3.8+
- Node.js 16+
- Git

### Local Development

```bash
# Clone repository
git clone https://github.com/itvedas29/itvedas.git
cd itvedas

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -r tests/requirements-test.txt

# Run tests
pytest

# Start development server (if applicable)
# See README.md for specific setup instructions
```

## Code Style

### Python
- Follow [PEP 8](https://www.python.org/dev/peps/pep-0008/)
- Use type hints where possible
- Comment complex logic
- Docstrings for functions/classes

### JavaScript
- Use modern ES6+ syntax
- Use consistent naming (camelCase for functions, UPPER_CASE for constants)
- Comment complex logic
- Use JSDoc for functions

### HTML/CSS
- Use semantic HTML
- Follow accessibility best practices
- Use meaningful class names
- Use CSS custom properties for theming

## Testing

### Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_api_subscribe.py

# Run with coverage
pytest --cov=tests

# Run specific test
pytest tests/test_api_subscribe.py::TestAPIInputValidation::test_json_parsing_required
```

### Writing Tests

```python
import unittest

class TestFeatureName(unittest.TestCase):
    def test_something_works(self):
        """Test description"""
        result = feature_function()
        self.assertTrue(result)

    def test_error_handling(self):
        """Test error handling"""
        with self.assertRaises(ValueError):
            bad_function("invalid")
```

## Documentation

- Update README.md for major changes
- Update API.md for API changes
- Add to CHANGELOG.md
- Include docstrings in code
- Comment complex logic

## Performance Considerations

- Profile changes for performance impact
- Minimize bundle sizes
- Optimize database queries
- Cache appropriately
- Consider mobile performance

## Accessibility

- Follow WCAG 2.1 guidelines
- Test with screen readers
- Ensure keyboard navigation
- Provide alt text for images
- Use semantic HTML

## Security

- Never commit secrets (API keys, passwords)
- Use environment variables for sensitive data
- Validate all inputs
- Sanitize output for HTML
- Follow OWASP guidelines
- Report security issues privately

## Commit Messages

Use clear, descriptive commit messages:

```
feat: Add new feature description

- Bullet point with details
- Another detail
- Links to related issues

Closes #123
```

**Conventions:**
- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation
- `style:` Code style (no functional change)
- `refactor:` Code refactoring
- `perf:` Performance improvement
- `test:` Test addition/modification
- `chore:` Maintenance

## Pull Request Process

1. Update relevant documentation
2. Add tests for changes
3. Ensure all tests pass
4. Squash commits if needed
5. Write descriptive PR title
6. Include detailed PR description
7. Link related issues
8. Request reviewers
9. Address feedback
10. Squash and merge when approved

## Release Process

1. Update version numbers
2. Update CHANGELOG.md
3. Create release branch
4. Update documentation
5. Create pull request
6. Get approvals
7. Merge to main
8. Create GitHub release
9. Announce release

## Questions?

- Open a discussion in Issues
- Check existing documentation
- Review similar implementations
- Ask in pull request comments

## Recognition

Contributors will be recognized in:
- CONTRIBUTORS.md file
- GitHub contributor graph
- Release notes for significant contributions

---

**Thank you for contributing to ITVedas!**

Last Updated: 2026-07-17
