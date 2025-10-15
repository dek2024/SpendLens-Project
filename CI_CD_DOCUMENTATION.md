# 🔄 CI/CD Pipeline Documentation

## Overview

SpendLens uses **GitHub Actions** to automatically run tests and enforce code quality on every push and pull request. The pipeline ensures that all code changes meet quality standards before being merged.

---

## 🚀 Workflow File

**Location:** `.github/workflows/tests.yml`

### Triggers

The workflow runs automatically on:
- ✅ Push to any branch (`main`, `master`, `develop`, or feature branches)
- ✅ Pull requests to `main`, `master`, or `develop`

### Pipeline Steps

```yaml
1. 📥 Checkout repository
   ├─ Uses: actions/checkout@v4
   └─ Fetches latest code from GitHub

2. 🐍 Set up Python 3.12
   ├─ Uses: actions/setup-python@v5
   ├─ Installs Python 3.12
   └─ Caches pip dependencies for faster builds

3. 📋 Display Python version
   └─ Shows Python and pip versions for debugging

4. 📦 Install dependencies
   ├─ Upgrades pip
   └─ Installs all packages from requirements.txt

5. 🧪 Run tests with coverage
   ├─ Executes pytest with 73 tests
   ├─ Generates coverage reports (terminal + XML)
   ├─ Enforces ≥85% coverage threshold
   └─ Fails build if coverage is below 85%

6. 📊 Coverage Summary
   ├─ Displays coverage report
   └─ Shows uncovered lines

7. 📤 Upload coverage to Codecov (optional)
   ├─ Uploads coverage.xml to Codecov
   └─ Generates coverage trends and reports

8. 🏅 Generate coverage badge
   ├─ Calculates coverage percentage
   ├─ Determines badge color (green/yellow/red)
   └─ Stores in environment variables

9. ✅ Test Summary
   └─ Displays final execution status
```

---

## 📊 Pipeline Behavior

### ✅ Success Criteria

Pipeline passes when:
- All 73 tests pass
- Code coverage ≥ 85%
- No syntax or import errors

**Result:** Green ✅ badge in README

### ❌ Failure Scenarios

Pipeline fails when:
- Any test fails
- Coverage drops below 85%
- Dependency installation fails
- Syntax errors in code

**Result:** Red ❌ badge in README, blocking PR merge

---

## 🏅 Coverage Badges

### Tests Badge

```markdown
![Tests](https://github.com/YOUR-USERNAME/spendlens.ai/actions/workflows/tests.yml/badge.svg)
```

**Shows:**
- ✅ Passing - All tests pass
- ❌ Failing - Tests failed
- 🔄 Running - Tests in progress

### Coverage Badge

```markdown
![Coverage](https://img.shields.io/badge/coverage-92%25-brightgreen)
```

**Color Coding:**
- 🟢 Bright Green: ≥90% coverage
- 🟢 Green: ≥85% coverage
- 🟡 Yellow: ≥75% coverage
- 🔴 Red: <75% coverage

---

## 🔍 Viewing Workflow Results

### On GitHub

1. Navigate to your repository on GitHub
2. Click **"Actions"** tab at the top
3. See list of workflow runs (most recent first)
4. Click on a run to see detailed logs
5. Expand steps to view output

### Example Workflow Output

```
📥 Checkout repository                     ✅ 2s
🐍 Set up Python 3.12                      ✅ 15s
📋 Display Python version                  ✅ 1s
📦 Install dependencies                    ✅ 45s
🧪 Run tests with coverage                 ✅ 13s
   ├─ 73 tests passed
   └─ Coverage: 92%
📊 Coverage Summary                        ✅ 2s
📤 Upload coverage to Codecov              ✅ 5s
🏅 Generate coverage badge                 ✅ 1s
✅ Test Summary                            ✅ 1s
   └─ Status: PASSED ✅
```

---

## 🧪 Local Testing Before Push

**Always run tests locally before pushing:**

```bash
# Quick test run
pytest tests/test_logic.py -v

# With coverage (same as CI)
pytest tests/test_logic.py -v --cov=src --cov-report=term-missing --cov-fail-under=85

# Generate HTML report
pytest tests/test_logic.py --cov=src --cov-report=html
open htmlcov/index.html
```

---

## 🛠️ Troubleshooting CI Failures

### Tests Failing Locally

```bash
# Run with verbose output
pytest tests/test_logic.py -v -s

# Stop on first failure
pytest tests/test_logic.py -x

# Run specific failing test
pytest tests/test_logic.py::TestClassName::test_method_name -v
```

### Coverage Below 85%

```bash
# See which lines are missing coverage
pytest tests/test_logic.py --cov=src --cov-report=term-missing

# Generate HTML report for detailed view
pytest tests/test_logic.py --cov=src --cov-report=html
open htmlcov/index.html  # Click on files to see uncovered lines
```

### Dependency Issues

```bash
# Recreate virtual environment
rm -rf .venv
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

---

## 📈 Coverage Trends

### Using Codecov (Optional)

If you've set up Codecov:

1. Visit: `https://codecov.io/gh/YOUR-USERNAME/spendlens.ai`
2. View coverage trends over time
3. See coverage changes per commit
4. Get PR comments with coverage diff

**Setup Codecov:**
```bash
# Add CODECOV_TOKEN to GitHub Secrets
# Get token from: https://codecov.io/
# Settings → Secrets → New repository secret
# Name: CODECOV_TOKEN
# Value: <your-token>
```

---

## 🔒 GitHub Secrets (if needed)

For OpenAI API tests (not currently used):

1. Go to repository **Settings**
2. Navigate to **Secrets and variables** → **Actions**
3. Click **New repository secret**
4. Add:
   - Name: `OPENAI_API_KEY`
   - Value: `sk-...your-key...`

**Update workflow to use secret:**
```yaml
env:
  OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
```

---

## 🔄 Workflow Updates

### Modify Coverage Threshold

Edit `.github/workflows/tests.yml`:

```yaml
# Change from 85% to 90%
--cov-fail-under=90
```

### Add Python Version Matrix

Test on multiple Python versions:

```yaml
strategy:
  matrix:
    python-version: ['3.11', '3.12', '3.13']
```

### Add Linting Step

```yaml
- name: 🔍 Lint with flake8
  run: |
    pip install flake8
    flake8 src tests --max-line-length=100
```

---

## 📋 Best Practices

### Before Committing

✅ Run tests locally  
✅ Check coverage is ≥85%  
✅ Fix any failing tests  
✅ Ensure no syntax errors  

### Commit Messages

Use conventional commits:
```
feat: add new expense category
fix: resolve date parsing bug
test: add edge case for Unicode handling
docs: update README with CI/CD info
ci: update coverage threshold to 90%
```

### Pull Request Workflow

1. Create feature branch
2. Make changes and commit
3. Push branch to GitHub
4. CI runs automatically
5. Review CI results
6. Fix any failures
7. Create PR when CI passes
8. Merge when approved

---

## 📊 Current Status

| Metric | Status |
|--------|--------|
| **Tests** | 73/73 passing ✅ |
| **Coverage** | 92% ✅ |
| **Threshold** | ≥85% ✅ |
| **Python Version** | 3.12 ✅ |
| **CI/CD** | Active ✅ |
| **Badge** | Passing ✅ |

---

## 🎯 Next Steps

### Immediate
- ✅ Push code to GitHub
- ✅ Verify workflow runs successfully
- ✅ Check badges appear in README

### Optional Enhancements
- 🔄 Set up Codecov integration
- 🔄 Add linting (flake8, black, mypy)
- 🔄 Add security scanning (bandit)
- 🔄 Set up branch protection rules
- 🔄 Add pre-commit hooks

---

## 📚 Resources

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [pytest Documentation](https://docs.pytest.org/)
- [pytest-cov Documentation](https://pytest-cov.readthedocs.io/)
- [Codecov Documentation](https://docs.codecov.com/)

---

## ✅ Quick Reference

### Check CI Status
```bash
# View last workflow run
gh run list --limit 1

# View workflow logs
gh run view --log
```

### Update Badge URLs
```markdown
# Replace YOUR-USERNAME with actual GitHub username
![Tests](https://github.com/YOUR-USERNAME/spendlens.ai/actions/workflows/tests.yml/badge.svg)
```

### Force Workflow Run
```bash
# Trigger workflow manually
gh workflow run tests.yml
```

---

**CI/CD Pipeline Status: ✅ READY FOR DEPLOYMENT**
