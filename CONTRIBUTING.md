# Contributing to PakJobs Aggregator

Thank you for considering contributing to PakJobs Aggregator! This document provides guidelines for contributing to the project.

## Code of Conduct

- Be respectful and inclusive
- Focus on constructive feedback
- Help others learn and grow
- Respect different viewpoints and experiences

## How to Contribute

### Reporting Bugs

**Before submitting a bug report:**
1. Check existing issues to avoid duplicates
2. Verify the bug exists in the latest version
3. Collect relevant information (error messages, logs, environment)

**Bug Report Template:**
```markdown
**Description**: Brief description of the bug

**Steps to Reproduce**:
1. Step 1
2. Step 2
3. Step 3

**Expected Behavior**: What should happen

**Actual Behavior**: What actually happened

**Environment**:
- OS: [Windows/macOS/Linux]
- Python version: [e.g., 3.12.0]
- PostgreSQL version: [e.g., 16.0]

**Error Messages/Logs**:
```
Paste error messages here
```
```

### Suggesting Enhancements

**Enhancement Proposal Template:**
```markdown
**Feature**: Brief title of the feature

**Problem**: What problem does this solve?

**Proposed Solution**: How would this work?

**Alternatives Considered**: Other approaches you've thought about

**Benefits**: Why is this valuable?
```

### Adding New Job Site Scrapers

To add a new Pakistani job site:

1. **Create scraper file**: `scrapers/newsite.py`

```python
from typing import Dict, Optional, Any
from .base import BaseScraper

class NewSiteScraper(BaseScraper):
    def __init__(self):
        super().__init__(
            site_name='newsite',
            base_url='https://www.newsite.pk'
        )
    
    def scrape(self, mode: str = 'incremental') -> Dict[str, int]:
        # Implementation
        pass
    
    def parse_job_listing(self, elem) -> Optional[Dict[str, Any]]:
        # Implementation
        pass
```

2. **Register scraper**: Update `scrapers/__init__.py`

```python
from .newsite import NewSiteScraper

SCRAPERS = {
    # ... existing scrapers
    'newsite': NewSiteScraper,
}
```

3. **Update schema**: Add to site_source CHECK constraint in `schema.sql`

```sql
site_source VARCHAR(50) NOT NULL CHECK (site_source IN (
    'rozee', 'mustakbil', ..., 'newsite'
)),
```

4. **Write tests**: Add tests in `tests/test_scrapers.py`

5. **Update documentation**: Add to README.md

### Pull Request Process

1. **Fork the repository**

2. **Create a feature branch**
```bash
git checkout -b feature/your-feature-name
```

3. **Make your changes**
- Follow existing code style
- Add tests for new features
- Update documentation
- Keep commits focused and atomic

4. **Run tests**
```bash
pytest
```

5. **Run code quality checks**
```bash
# Format code
black .

# Check for errors
flake8 .
```

6. **Commit with clear messages**
```bash
git commit -m "feat: Add NewSite scraper

- Implement NewSiteScraper class
- Add tests for NewSite
- Update documentation
"
```

**Commit Message Convention:**
- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation changes
- `style:` Code formatting
- `refactor:` Code refactoring
- `test:` Adding tests
- `chore:` Maintenance tasks

7. **Push to your fork**
```bash
git push origin feature/your-feature-name
```

8. **Create Pull Request**
- Use clear PR title
- Describe changes in detail
- Reference related issues
- Add screenshots if UI changes

### Code Style Guidelines

**Python (PEP 8)**:
- Use 4 spaces for indentation
- Max line length: 100 characters
- Use descriptive variable names
- Add docstrings to functions/classes
- Type hints for function parameters

**Example:**
```python
def scrape_jobs(site_name: str, mode: str = 'incremental') -> Dict[str, int]:
    """
    Scrape jobs from a specific site
    
    Args:
        site_name: Name of job site to scrape
        mode: Scraping mode ('incremental' or 'full_refresh')
        
    Returns:
        Dictionary with scraping statistics
    """
    # Implementation
    pass
```

**SQL**:
- Use uppercase for SQL keywords
- Indent nested queries
- Add comments for complex logic

**JavaScript/HTML/CSS**:
- Use 2 spaces for indentation
- Follow Tailwind CSS conventions
- Keep JavaScript minimal (vanilla JS preferred)

### Testing Guidelines

**Write tests for:**
- New scrapers
- API endpoints
- Data processing functions
- Bug fixes

**Test Structure:**
```python
class TestNewFeature:
    """Test description"""
    
    def test_specific_behavior(self):
        """Test a specific aspect"""
        # Arrange
        input_data = ...
        
        # Act
        result = function_under_test(input_data)
        
        # Assert
        assert result == expected_value
```

**Run specific tests:**
```bash
# Single file
pytest tests/test_scrapers.py

# Single test
pytest tests/test_scrapers.py::TestRozeeScraper::test_initialization

# With coverage
pytest --cov=. --cov-report=html
```

### Documentation

**Update when adding features:**
- README.md - Feature overview
- INSTALLATION.md - Setup instructions
- API documentation - New endpoints
- Inline comments - Complex logic

**Documentation Style:**
- Clear and concise
- Include examples
- Use proper Markdown formatting
- Add diagrams for complex flows

### Project Structure

```
pakjobs-aggregator/
├── scrapers/          # Scraper implementations
├── data_pipeline/     # Data processing
├── templates/         # HTML templates
├── static/           # CSS, JS assets
├── tests/            # Test suite
├── scripts/          # Utility scripts
├── app.py            # Main Flask app
└── schema.sql        # Database schema
```

### Development Workflow

1. **Set up development environment**
```bash
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
```

2. **Create feature branch**
```bash
git checkout -b feature/my-feature
```

3. **Make changes and test**
```bash
# Make code changes
# Add tests
pytest

# Format code
black .
flake8 .
```

4. **Commit and push**
```bash
git add .
git commit -m "feat: Description"
git push origin feature/my-feature
```

5. **Create Pull Request**

### Scraper Development Tips

**Respect website ToS:**
- Read and follow robots.txt
- Implement rate limiting (3+ second delays)
- Scrape during off-peak hours
- Don't overwhelm servers

**Error Handling:**
```python
try:
    response = self.make_request(url)
    if response:
        # Process response
except Exception as e:
    self.logger.error(f"Scraping failed: {e}")
    self.stats['errors'] += 1
```

**Incremental Scraping:**
```python
# Stop when seeing existing jobs
if self.job_exists(job_data['source_url']):
    consecutive_seen += 1
    if mode == 'incremental' and consecutive_seen >= 20:
        return self.stats
```

### Performance Considerations

- Use database indexes for queries
- Batch insert jobs (not one by one)
- Cache frequently accessed data
- Implement pagination for large datasets
- Use connection pooling

### Security Best Practices

- Never commit `.env` files
- Use environment variables for secrets
- Encrypt sensitive data (use Fernet)
- Validate all user inputs
- Sanitize database queries (use parameterized queries)

## Review Process

Pull requests will be reviewed for:
- Code quality and style
- Test coverage
- Documentation updates
- Performance impact
- Security implications

**Review Timeline:**
- Initial review: Within 48 hours
- Feedback implementation: As needed
- Final approval: 1-2 reviewers

## Getting Help

- **Questions**: Open a GitHub Discussion
- **Bugs**: Create an Issue
- **Chat**: (Add Discord/Slack link if available)

## Recognition

Contributors will be:
- Listed in CONTRIBUTORS.md
- Mentioned in release notes
- Credited in documentation

## License

By contributing, you agree that your contributions will be licensed under the project's license.

---

Thank you for making PakJobs Aggregator better! 🙏
