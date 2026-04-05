# Lab 3 Submission — Continuous Integration (CI/CD)

## Overview

### Testing Framework

**Framework chosen:** pytest

**Justification:**
- Simple and intuitive syntax that makes tests easy to read and write
- Powerful fixture system for test setup and teardown
- Excellent plugin ecosystem (pytest-cov, pytest-asyncio, etc.)
- Widely adopted in the Python community
- Native support for async/await patterns, perfect for FastAPI
- Better error messages and test discovery compared to unittest

**Test Coverage:**
- **GET /** endpoint: 7 comprehensive tests covering JSON structure, all fields, data types, and values
- **GET /health** endpoint: 5 tests verifying status, fields, timestamp format, and uptime
- **Error handling:** Tests for 404 errors and wrong HTTP methods
- **Total:** 14 tests, all passing

### CI Workflow Configuration

**Workflow triggers:**
- Push to branches: `main`, `master`, `lab03`
- Pull requests to: `main`, `master`
- Path filters: Only runs when files in `app_python/` or `.github/workflows/python-ci.yml` are changed

**Rationale:**
- Path filters prevent unnecessary CI runs when only documentation or other applications change
- PR checks ensure code quality before merging
- Branch-specific triggers allow testing on feature branches without affecting main

### Versioning Strategy

**Strategy chosen:** Calendar Versioning (CalVer)

**Format:** `YYYY.MM.DD` / `YYYY.MM` / `latest` / `branch-SHA`

**Rationale:**
- Simple to implement (no manual git tags required)
- Well-suited for continuous deployment workflows
- Easy to understand when an image was built by looking at the date
- No need for manual version management
- Good for services (as opposed to libraries, which benefit more from SemVer)

**Docker tags created:**
- `funnyfoxd/devops-info-service:2025.02.09` - Full date (specific build)
- `funnyfoxd/devops-info-service:2025.02` - Year.month (rolling monthly tag)
- `funnyfoxd/devops-info-service:latest` - Latest stable (only on main/master branches)
- `funnyfoxd/devops-info-service:lab03-abc1234` - Branch name + commit SHA (for feature branches)

---

## Workflow Evidence

### Successful Workflow Run

**GitHub Actions Workflow:** [Python CI/CD Pipeline](https://github.com/FunnyFoXD/DevOps-Core-Course/actions/workflows/python-ci.yml)

The workflow successfully runs three jobs:
1. **test** - Code quality and testing (linting + pytest)
2. **build-and-push** - Docker image build and push to Docker Hub
3. **security-scan** - Vulnerability scanning with pip-audit

### Tests Passing Locally

```bash
$ pytest -v
============================= test session starts ==============================
platform linux -- Python 3.12.3, pytest-8.3.4, pluggy-1.6.0
collected 14 items

tests/test_app.py::TestMainEndpoint::test_root_endpoint_status_code PASSED [  7%]
tests/test_app.py::TestMainEndpoint::test_root_endpoint_json_structure PASSED [ 14%]
tests/test_app.py::TestMainEndpoint::test_service_info_fields PASSED     [ 21%]
tests/test_app.py::TestMainEndpoint::test_system_info_fields PASSED      [ 28%]
tests/test_app.py::TestMainEndpoint::test_runtime_info_fields PASSED     [ 35%]
tests/test_app.py::TestMainEndpoint::test_request_info_fields PASSED     [ 42%]
tests/test_app.py::TestMainEndpoint::test_endpoints_list PASSED          [ 50%]
tests/test_app.py::TestHealthEndpoint::test_health_endpoint_status_code PASSED [ 57%]
tests/test_app.py::TestHealthEndpoint::test_health_endpoint_json_structure PASSED [ 64%]
tests/test_app.py::TestHealthEndpoint::test_health_status_value PASSED   [ 71%]
tests/test_app.py::TestHealthEndpoint::test_health_uptime_type PASSED    [ 78%]
tests/test_app.py::TestHealthEndpoint::test_health_timestamp_format PASSED [ 85%]
tests/test_app.py::TestErrorHandling::test_404_not_found PASSED          [ 92%]
tests/test_app.py::TestErrorHandling::test_wrong_method PASSED           [100%]

============================== 14 passed in 0.38s ==============================
```

### Docker Image on Docker Hub

**Docker Hub Repository:** [funnyfoxd/devops-info-service](https://hub.docker.com/r/funnyfoxd/devops-info-service)

Images are automatically tagged with CalVer versioning and pushed on each successful build.

### Status Badge

**Status badge** added to `app_python/README.md` and displays current workflow status:

```markdown
[![CI](https://github.com/FunnyFoXD/DevOps-Core-Course/workflows/Python%20CI%2FCD%20Pipeline/badge.svg)](https://github.com/FunnyFoXD/DevOps-Core-Course/actions/workflows/python-ci.yml)
```

---

## Best Practices Implemented

### 1. Dependency Caching
**Practice:** Caching pip dependencies using `actions/setup-python@v5` with `cache: 'pip'` parameter

**Why it helps:**
- Significantly speeds up dependency installation on subsequent workflow runs
- Reduces network usage and GitHub Actions minutes consumption
- Cache is automatically invalidated when `requirements.txt` changes

**Performance improvement:**
- First run: ~30-40 seconds for dependency installation
- Subsequent runs (cache hit): ~5-10 seconds
- **Time saved:** ~25-30 seconds per workflow run

### 2. Docker Layer Caching
**Practice:** Using GitHub Actions cache for Docker build layers (`cache-from: type=gha`, `cache-to: type=gha`)

**Why it helps:**
- Reuses Docker image layers between workflow runs
- Dramatically speeds up Docker builds when only application code changes
- Reduces build time and resource consumption

**Performance improvement:**
- First build: ~2-3 minutes
- Subsequent builds (cache hit): ~30-60 seconds
- **Time saved:** ~1.5-2 minutes per build

### 3. Job Dependencies
**Practice:** Using `needs: test` to ensure Docker build only runs after tests pass

**Why it helps:**
- Prevents building and pushing Docker images when tests fail
- Saves CI/CD minutes and Docker Hub storage
- Ensures only tested code gets deployed

### 4. Path Filters
**Practice:** Workflow only triggers when files in `app_python/` or workflow itself change

**Why it helps:**
- Prevents unnecessary CI runs when only documentation or other apps change
- Saves GitHub Actions minutes
- Faster feedback for developers working on Python app

### 5. Workflow Concurrency
**Practice:** Canceling outdated workflow runs when new commits are pushed (`concurrency` with `cancel-in-progress: true`)

**Why it helps:**
- Prevents running CI for outdated code
- Saves resources and GitHub Actions minutes
- Ensures only the latest commit gets tested

### 6. Conditional Steps
**Practice:** Docker images only pushed on non-PR events (`push: ${{ github.event_name != 'pull_request' }}`)

**Why it helps:**
- Prevents pushing temporary images from pull requests
- Saves Docker Hub storage space
- Security best practice (don't push untrusted code)

### 7. Environment Variables
**Practice:** Using `env` section for repeated values (DOCKER_HUB_USERNAME, IMAGE_NAME)

**Why it helps:**
- Reduces duplication and makes maintenance easier
- Single source of truth for configuration
- Easier to update values in one place

### 8. Security Scanning
**Practice:** Integrated pip-audit for vulnerability scanning of Python dependencies

**Why it helps:**
- Automatically detects known vulnerabilities in dependencies
- Early warning system for security issues
- Uses PyPI Advisory Database (same as pip check)

**Results:**
- Initially found 2 vulnerabilities in Starlette 0.38.6 (CVE-2024-47874, CVE-2025-54121)
- Fixed by updating to Starlette 0.52.1 and FastAPI 0.128.5
- Current scan: No known vulnerabilities found

---

## Key Decisions

### Versioning Strategy: CalVer

**Why CalVer instead of SemVer?**

I chose Calendar Versioning (CalVer) over Semantic Versioning (SemVer) because:

1. **Application type:** This is a service/application, not a library. CalVer works better for continuously deployed services.

2. **Simplicity:** No need to manually create git tags or decide on version bumps. Versions are automatically generated from the build date.

3. **Continuous deployment:** CalVer aligns well with CI/CD workflows where every successful build can be deployed.

4. **Clarity:** It's immediately clear when an image was built by looking at the version tag.

5. **No breaking changes concern:** Since this is an internal service, we don't need to communicate breaking changes to external users through version numbers.

### Docker Tags Strategy

**Tags created by CI:**

- `YYYY.MM.DD` - Full date tag for precise build identification
- `YYYY.MM` - Monthly rolling tag for easier reference
- `latest` - Only on main/master branches, always points to the most recent stable build
- `branch-SHA` - For feature branches, includes branch name and commit SHA for traceability

This strategy provides both precision (date tags) and convenience (latest, monthly tags) while maintaining traceability for all builds.

### Workflow Triggers

**Why these triggers?**

- **Push triggers:** Ensure every commit is tested, catching issues early
- **PR triggers:** Allow code review with CI results before merging
- **Path filters:** Optimize CI usage by only running when relevant files change
- **Branch-specific:** Support both main branches (main/master) and feature branches (lab03)

This configuration balances thoroughness with efficiency.

### Test Coverage

**What's tested:**
- All API endpoints (`GET /`, `GET /health`)
- JSON response structure and required fields
- Data types of all response fields
- Expected values (status codes, field values)
- Error handling (404, wrong HTTP methods)

**What's not tested:**
- Integration tests with a running server (using TestClient instead)
- Load testing or performance testing
- Edge cases with invalid data (could be added)
- Network failures or external dependencies

The current test suite provides good coverage for the application's functionality while keeping tests fast and maintainable.

---

## Challenges

### Challenge 1: Security Vulnerabilities in Dependencies
**Problem:** Initial pip-audit scan found 2 vulnerabilities in Starlette 0.38.6 (CVE-2024-47874, CVE-2025-54121)

**Solution:**
- Updated FastAPI from 0.115.0 to 0.128.5 (supports newer Starlette)
- Updated Starlette from 0.38.6 to 0.52.1 (fixes both CVEs)
- Updated Uvicorn from 0.34.0 to 0.40.0 (compatibility)
- Verified all tests still pass after updates
- Re-ran pip-audit: No vulnerabilities found

### Challenge 2: Snyk Token Not Available
**Problem:** Could not obtain Snyk API token (organization vs personal account confusion)

**Solution:**
- Used pip-audit as an alternative security scanning tool
- pip-audit uses PyPI Advisory Database (same vulnerability sources)
- No API token required, works out of the box
- Integrated into CI workflow with `continue-on-error: true`

### Challenge 3: Syntax Error in F-String
**Problem:** Flake8 detected syntax error in multi-line f-string formatting

**Solution:**
- Fixed f-string formatting in `get_uptime()` function
- Changed from multi-line broken format to single-line format
- Verified syntax with `py_compile` and flake8

### Challenge 4: Workflow Not Triggering
**Problem:** CI didn't run after pushing changes to .gitignore

**Solution:**
- Identified that path filters prevent workflow from running when only non-relevant files change
- Committed changes to workflow and app_python files together
- Workflow now triggers correctly when relevant files change

### Challenge 5: pip-audit Format Issue
**Problem:** Workflow used `--format text` which doesn't exist in pip-audit

**Solution:**
- Changed to `--format columns` (default format)
- Verified locally that format works correctly
- Updated workflow file

---

## Test Coverage

### Coverage Integration

**Tool used:** pytest-cov

**Coverage percentage:** ~85-90% (varies by run)

**What's covered:**
- All API endpoints (`GET /`, `GET /health`)
- All helper functions (`get_system_info()`, `get_uptime()`)
- Error handlers (404, 500)
- Request processing logic

**What's not covered:**
- Main entry point (`if __name__ == "__main__"`) - not executed in tests
- Some edge cases in error handling
- Integration scenarios requiring running server

**Coverage threshold:** Not enforced in CI (optional), but coverage reports are generated and uploaded to Codecov.

**Codecov Integration:**
- Coverage reports uploaded automatically on each CI run
- Coverage badge displays current percentage in README
- Historical coverage tracking available on Codecov dashboard
- Flag: `python` for separate tracking from Go coverage

---

## Multi-App CI Setup (Bonus)

### Path Filters Implementation

This repository contains both Python and Go applications. Path filters ensure that:

- **Python CI** only runs when `app_python/**` files change
- **Go CI** only runs when `app_go/**` files change
- Both workflows can run **in parallel** when both apps change in one commit
- Documentation changes don't trigger unnecessary CI runs

**Benefits:**
- **Resource optimization:** Saves GitHub Actions minutes
- **Faster feedback:** Developers get results faster when working on one app
- **Parallel execution:** No blocking between different language CI pipelines
- **Selective testing:** Only relevant code triggers appropriate workflows

**Example scenarios:**
- Change `app_python/app.py` -> Only Python CI runs
- Change `app_go/main.go` -> Only Go CI runs  
- Change both -> Both CI workflows run simultaneously
- Change `README.md` -> No CI runs

See `app_go/docs/LAB03.md` for detailed Go CI/CD documentation.

---

## Summary

This lab successfully implements a complete CI/CD pipeline for the Python application with:
- Comprehensive unit tests (14 tests, all passing)
- Automated linting and code quality checks
- Docker image building and publishing with CalVer versioning
- Security vulnerability scanning
- Test coverage tracking with Codecov integration
- Multiple CI best practices for optimization and reliability
- Proper workflow configuration with path filters and conditional steps

The pipeline is production-ready and will automatically test, build, and deploy the application on every relevant code change.

