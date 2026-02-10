# Contributing to nanoos_gliders

Thank you for your interest in contributing to the nanoos_gliders package! This document provides guidelines and instructions for contributing.

## Table of Contents

1. [Code of Conduct](#code-of-conduct)
2. [Getting Started](#getting-started)
3. [How to Contribute](#how-to-contribute)
4. [Development Workflow](#development-workflow)
5. [Coding Standards](#coding-standards)
6. [Testing](#testing)
7. [Documentation](#documentation)
8. [Submitting Changes](#submitting-changes)
9. [Review Process](#review-process)

## Code of Conduct

### Our Standards

- Be respectful and inclusive
- Welcome newcomers and help them learn
- Focus on constructive feedback
- Respect differing viewpoints and experiences
- Accept responsibility for mistakes

## Getting Started

### Prerequisites

- Python 3.7+
- Conda or Miniconda
- Git
- Basic understanding of glider oceanography
- Familiarity with ERDDAP (helpful but not required)

### Development Setup

1. **Fork and clone the repository:**
   ```bash
   git clone https://github.com/your-username/nanoos_gliders.git
   cd nanoos_gliders
   ```

2. **Create development environment:**
   ```bash
   conda env create -f gliders_env.yml
   conda activate gliders_env
   ```

3. **Install development dependencies:**
   ```bash
   pip install pytest pytest-cov black flake8 sphinx
   ```

4. **Create a feature branch:**
   ```bash
   git checkout -b feature/your-feature-name
   ```

## How to Contribute

### Types of Contributions

We welcome several types of contributions:

#### 1. Bug Reports

Found a bug? Please report it!

**Before submitting:**
- Check if the bug is already reported in Issues
- Verify it's reproducible with the latest version
- Collect relevant information (Python version, error logs, etc.)

**Bug report should include:**
- Clear, descriptive title
- Steps to reproduce
- Expected vs. actual behavior
- Python and package versions
- Error messages and stack traces
- Sample data or minimal reproducible example

**Template:**
```markdown
## Bug Description
[Clear description of the bug]

## Steps to Reproduce
1. [First step]
2. [Second step]
3. [Continue...]

## Expected Behavior
[What should happen]

## Actual Behavior
[What actually happens]

## Environment
- Python version: 
- Package version: 
- Operating system: 

## Error Log
```
[Paste error messages]
```

## Additional Context
[Any other relevant information]
```

#### 2. Feature Requests

Have an idea for improvement?

**Feature request should include:**
- Clear description of the feature
- Use case and motivation
- Proposed implementation (if you have ideas)
- Examples of similar features in other tools
- Willingness to contribute implementation

**Template:**
```markdown
## Feature Description
[What feature do you want?]

## Motivation
[Why is this feature needed?]

## Proposed Solution
[How might this work?]

## Alternatives Considered
[Other approaches you thought about]

## Additional Context
[Any other relevant information]
```

#### 3. Documentation Improvements

Documentation can always be better!

**Areas for contribution:**
- Fixing typos or unclear explanations
- Adding examples
- Improving API documentation
- Creating tutorials
- Translating documentation

#### 4. Code Contributions

Ready to write code?

**Good first issues:**
- Look for issues labeled "good first issue"
- Bug fixes
- Adding tests
- Improving error messages
- Code cleanup and refactoring

**More involved contributions:**
- New features
- Performance optimizations
- New glider type support
- Enhanced visualizations

## Development Workflow

### 1. Choose or Create an Issue

- Check existing issues for something to work on
- For new features, create an issue first to discuss
- Comment on the issue to indicate you're working on it

### 2. Branch Naming

Use descriptive branch names:
- `feature/add-seaglider-support`
- `bugfix/fix-section-detection`
- `docs/improve-installation-guide`
- `refactor/simplify-plotting-code`

### 3. Make Changes

- Write clean, readable code
- Follow existing code style
- Add comments for complex logic
- Update documentation as needed
- Add or update tests

### 4. Commit Messages

Write clear commit messages:

**Format:**
```
type: Brief description (50 chars or less)

More detailed explanation if needed. Wrap at 72 characters.
Explain the problem this commit solves and why you chose
this approach.

Fixes #123
```

**Types:**
- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation changes
- `style:` Code style/formatting
- `refactor:` Code restructuring
- `test:` Adding/updating tests
- `chore:` Maintenance tasks

**Examples:**
```
feat: Add support for Spray gliders

Implement Dataset and Glider subclass for Spray glider type.
Includes configuration parsing and data format handling.

Fixes #45
```

```
fix: Correct section detection for complex paths

Section detection was failing when gliders made tight loops.
Adjusted tolerance logic to handle overlapping paths.

Fixes #67
```

### 5. Test Your Changes

```bash
# Run all tests
pytest

# Run specific test
pytest tests/test_section_detection.py

# Run with coverage
pytest --cov=nanoos_gliders
```

### 6. Update Documentation

If your changes affect:
- **API**: Update API_REFERENCE.md
- **Usage**: Update USAGE_GUIDE.md
- **Setup**: Update INSTALLATION.md
- **Code**: Update docstrings and comments

### 7. Push and Create Pull Request

```bash
git push origin feature/your-feature-name
```

Then create a Pull Request on GitHub.

## Coding Standards

### Python Style Guide

We follow [PEP 8](https://pep8.org/) with some modifications:

**Line length:**
- Maximum 100 characters (not 79)
- Exception: Long URLs or data strings

**Imports:**
```python
# Standard library
import os
import sys
from datetime import datetime

# Third-party
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# Local application
from classes import Dataset, WAShelfGlider
import gliders_general_functions as gliders_gen
```

**Naming conventions:**
```python
# Modules and packages
lowercase_with_underscores

# Classes
CapitalizedWords

# Functions and variables
lowercase_with_underscores

# Constants
UPPERCASE_WITH_UNDERSCORES
```

### Docstrings

Use NumPy-style docstrings:

```python
def calculate_distance(latitude, longitude):
    """
    Calculate great circle distance between consecutive points.
    
    Parameters
    ----------
    latitude : numpy.ndarray
        Array of latitude values in degrees
    longitude : numpy.ndarray
        Array of longitude values in degrees
    
    Returns
    -------
    numpy.ndarray
        Distance array in meters (length = len(latitude) - 1)
    
    Examples
    --------
    >>> lat = np.array([47.0, 47.1, 47.2])
    >>> lon = np.array([-125.0, -124.9, -124.8])
    >>> distances = calculate_distance(lat, lon)
    >>> print(distances.sum() / 1000)  # Total km
    24.5
    
    Notes
    -----
    Uses the great circle formula assuming spherical Earth
    with radius 6370 km.
    
    See Also
    --------
    great_circle_calc : Alternative implementation
    """
    # Implementation here
```

### Code Organization

**File structure:**
```python
# File header with description
"""
Module for processing glider section data.

This module provides functions for detecting transect sections
and splitting glider data into manageable segments.
"""

# Imports
import numpy as np

# Constants
DEFAULT_TOLERANCE = 0.2

# Classes
class SectionDetector:
    pass

# Functions
def detect_sections(data, tolerance):
    pass

# Main execution
if __name__ == '__main__':
    pass
```

### Error Handling

```python
# Good: Specific exception handling
try:
    data = retrieve_erddap_data(dataset_id)
except requests.ConnectionError as e:
    logger.error(f"ERDDAP connection failed: {e}")
    raise
except ValueError as e:
    logger.error(f"Invalid dataset parameters: {e}")
    return None

# Bad: Bare except
try:
    data = retrieve_erddap_data(dataset_id)
except:
    pass
```

### Type Hints (Encouraged)

```python
from typing import List, Optional, Tuple

def process_deployment(
    dataset_id: str,
    start_time: str,
    end_time: Optional[str] = None
) -> Tuple[pd.DataFrame, List[int]]:
    """
    Process a glider deployment.
    
    Parameters
    ----------
    dataset_id : str
        ERDDAP dataset identifier
    start_time : str
        Start time in ISO format
    end_time : str, optional
        End time in ISO format
        
    Returns
    -------
    data : pd.DataFrame
        Processed glider data
    sections : List[int]
        Section boundary indices
    """
    pass
```

## Testing

### Writing Tests

Create tests in the `tests/` directory:

```python
# tests/test_section_detection.py
import pytest
import numpy as np
from get_min_max import get_min_max


def test_get_min_max_simple():
    """Test section detection with simple dataset."""
    lon = np.array([0.0, 0.5, 1.0, 0.5, 0.0])
    result = get_min_max(lon, Tolerance=0.3, expPts=4)
    assert len(result) == 3
    assert result[0] == 0
    assert result[-1] == 4


def test_get_min_max_no_turning():
    """Test when glider doesn't turn."""
    lon = np.linspace(0, 1, 100)
    result = get_min_max(lon, Tolerance=0.1, expPts=2)
    assert len(result) == 2
    assert result[0] == 0
    assert result[1] == 99


@pytest.mark.parametrize("tolerance,expected_sections", [
    (0.1, 8),
    (0.2, 5),
    (0.3, 3),
])
def test_get_min_max_tolerance(tolerance, expected_sections):
    """Test that tolerance affects number of sections."""
    lon = np.array([/* test data */])
    result = get_min_max(lon, Tolerance=tolerance, expPts=10)
    assert len(result) == expected_sections
```

### Test Categories

**Unit tests:**
- Test individual functions
- Mock external dependencies
- Fast execution

**Integration tests:**
- Test module interactions
- Use test data files
- Verify end-to-end workflows

**Regression tests:**
- Prevent known bugs from reappearing
- Use real-world problematic datasets

### Running Tests Locally

```bash
# All tests
pytest

# Specific test file
pytest tests/test_section_detection.py

# Specific test
pytest tests/test_section_detection.py::test_get_min_max_simple

# With coverage report
pytest --cov=nanoos_gliders --cov-report=html

# Verbose output
pytest -v

# Stop on first failure
pytest -x
```

## Documentation

### Inline Documentation

- Add docstrings to all public functions and classes
- Comment complex algorithms
- Explain "why" not just "what"

### External Documentation

When adding features, update:
- **README.md**: If it affects overview
- **API_REFERENCE.md**: For new functions/classes
- **USAGE_GUIDE.md**: For new workflows
- **INSTALLATION.md**: For new dependencies
- **CHANGELOG.md**: For all changes

### Building Documentation

If we add Sphinx documentation:

```bash
cd docs
make html
open _build/html/index.html
```

## Submitting Changes

### Pull Request Process

1. **Update documentation and tests**
2. **Ensure all tests pass**
3. **Update CHANGELOG.md**
4. **Push to your fork**
5. **Create Pull Request**

### Pull Request Template

```markdown
## Description
[Describe the changes]

## Motivation and Context
[Why is this change needed? What problem does it solve?]

## Type of Change
- [ ] Bug fix (non-breaking change fixing an issue)
- [ ] New feature (non-breaking change adding functionality)
- [ ] Breaking change (fix or feature causing existing functionality to change)
- [ ] Documentation update

## How Has This Been Tested?
[Describe the tests you ran]

## Checklist
- [ ] My code follows the project's style guidelines
- [ ] I have performed a self-review of my code
- [ ] I have commented my code, particularly in hard-to-understand areas
- [ ] I have updated the documentation accordingly
- [ ] My changes generate no new warnings
- [ ] I have added tests that prove my fix is effective or my feature works
- [ ] New and existing unit tests pass locally with my changes
- [ ] I have updated CHANGELOG.md

## Related Issues
Fixes #[issue number]
```

### PR Best Practices

- **Small, focused changes**: Easier to review
- **One concern per PR**: Don't mix features and bug fixes
- **Clear description**: Explain what and why
- **Reference issues**: Link related issues
- **Respond to feedback**: Engage with reviewers

## Review Process

### For Contributors

**What to expect:**
- Initial review within 1 week
- Constructive feedback
- Possible requests for changes
- Merge when approved

**How to respond to reviews:**
- Address all comments
- Ask questions if unclear
- Mark resolved conversations
- Push updates to same branch

### For Reviewers

**Review checklist:**
- [ ] Code follows style guidelines
- [ ] Tests are comprehensive
- [ ] Documentation is updated
- [ ] No unnecessary changes
- [ ] Performance considered
- [ ] Security implications reviewed
- [ ] Backward compatibility maintained (or breaking changes documented)

**Providing feedback:**
- Be respectful and constructive
- Explain reasoning for requested changes
- Suggest alternatives when possible
- Approve when satisfied

## Development Tips

### Debugging

```python
# Use logging instead of print
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

logger.debug("Section detection starting")
logger.info(f"Found {n_sections} sections")
logger.warning("Tolerance may be too high")
logger.error(f"Failed to process: {error}")
```

### Performance Profiling

```python
import cProfile
import pstats

profiler = cProfile.Profile()
profiler.enable()

# Your code here
process_deployment(dataset)

profiler.disable()
stats = pstats.Stats(profiler)
stats.sort_stats('cumulative')
stats.print_stats(20)  # Top 20 functions
```

### Memory Profiling

```python
from memory_profiler import profile

@profile
def memory_intensive_function():
    # Your code
    pass
```

## Getting Help

**Questions about contributing?**
- Open a Discussion on GitHub
- Check existing Issues and Pull Requests
- Review this guide and other documentation
- Contact maintainers

**Stuck on implementation?**
- Describe what you've tried
- Show relevant code snippets
- Ask specific questions

## Recognition

Contributors will be:
- Listed in README.md
- Credited in release notes
- Thanked in CHANGELOG.md

## License

By contributing, you agree that your contributions will be licensed under the same license as the project.

---

Thank you for contributing to nanoos_gliders! Your efforts help improve ocean observing capabilities and benefit the entire community.
