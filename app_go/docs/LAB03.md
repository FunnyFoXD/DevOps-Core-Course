# Lab 3 Bonus — Go CI/CD Pipeline

## Overview

This document describes the CI/CD pipeline implementation for the Go version of the DevOps Info Service, including multi-app CI setup with path filters and test coverage tracking.

### Testing Framework

**Framework chosen:** Go's built-in `testing` package

**Why:**
- No external dependencies required
- Standard library solution, widely adopted
- Excellent integration with `go test` command
- Built-in coverage support (`go test -coverprofile`)
- Simple and straightforward syntax

**Test Coverage:**
- **GET /** endpoint: Comprehensive tests covering JSON structure, all fields, data types
- **GET /health** endpoint: Tests verifying status, fields, timestamp format, uptime
- **Error handling:** Tests for 404 errors and wrong HTTP methods
- **Helper functions:** Tests for `getUptime()`, `getSystemInfo()`, `getClientIP()`
- **Total:** 6 test functions covering all major functionality

### CI Workflow Configuration

**Workflow triggers:**
- Push to branches: `main`, `master`, `lab03`
- Pull requests to: `main`, `master`
- Path filters: Only runs when files in `app_go/` or `.github/workflows/go-ci.yml` are changed

**Rationale:**
- Path filters prevent unnecessary CI runs when only Python app or documentation changes
- Allows both Python and Go workflows to run in parallel when both apps change
- Optimizes CI/CD minutes usage
- Faster feedback for developers working on Go app

### Versioning Strategy

**Strategy:** Calendar Versioning (CalVer) - consistent with Python app

**Format:** `YYYY.MM.DD` / `YYYY.MM` / `latest` / `branch-SHA`

**Docker tags created:**
- `funnyfoxd/devops-info-service-go:2025.02.09` - Full date (specific build)
- `funnyfoxd/devops-info-service-go:2025.02` - Year.month (rolling monthly tag)
- `funnyfoxd/devops-info-service-go:latest` - Latest stable (only on main/master branches)
- `funnyfoxd/devops-info-service-go:lab03-abc1234` - Branch name + commit SHA (for feature branches)

---

## Workflow Evidence

### Successful Workflow Run

**GitHub Actions Workflow:** [Go CI/CD Pipeline](https://github.com/FunnyFoXD/DevOps-Core-Course/actions/workflows/go-ci.yml)

The workflow successfully runs three jobs:
1. **test** - Code quality and testing (golangci-lint + go test)
2. **build-and-push** - Docker image build and push to Docker Hub
3. **security-scan** - Vulnerability scanning with gosec

### Tests Passing Locally

```bash
$ go test -v ./...
=== RUN   TestMainHandler
--- PASS: TestMainHandler (0.00s)
=== RUN   TestHealthHandler
--- PASS: TestHealthHandler (0.00s)
=== RUN   TestNotFoundHandler
--- PASS: TestNotFoundHandler (0.00s)
=== RUN   TestGetUptime
--- PASS: TestGetUptime (0.00s)
=== RUN   TestGetSystemInfo
--- PASS: TestGetSystemInfo (0.00s)
=== RUN   TestGetClientIP
--- PASS: TestGetClientIP (0.00s)
PASS
ok      github.com/FunnyFoXD/DevOps-Core-Course    0.003s
```

### Docker Image on Docker Hub

**Docker Hub Repository:** [funnyfoxd/devops-info-service-go](https://hub.docker.com/r/funnyfoxd/devops-info-service-go)

Images are automatically tagged with CalVer versioning and pushed on each successful build.

### Status Badge

**Status badge** added to `app_go/README.md` and displays current workflow status.

---

## Path Filters & Multi-App CI

### Benefits of Path-Based Triggers

**Why Path Filters Matter:**

1. **Resource Optimization:**
   - Python CI only runs when Python code changes
   - Go CI only runs when Go code changes
   - Saves GitHub Actions minutes and reduces costs

2. **Faster Feedback:**
   - Developers get faster CI results when working on one app
   - No need to wait for unrelated app tests to complete

3. **Parallel Execution:**
   - Both workflows can run simultaneously when both apps change
   - No blocking between Python and Go CI pipelines

4. **Selective Testing:**
   - Documentation changes don't trigger CI
   - Only relevant code changes trigger appropriate workflows

### Path Filter Configuration

**Python Workflow:**
```yaml
paths:
  - 'app_python/**'
  - '.github/workflows/python-ci.yml'
```

**Go Workflow:**
```yaml
paths:
  - 'app_go/**'
  - '.github/workflows/go-ci.yml'
```

**Testing Path Filters:**
- Change only `app_python/app.py` -> Only Python CI runs
- Change only `app_go/main.go` -> Only Go CI runs
- Change both in one commit -> Both CI workflows run in parallel
- Change `README.md` -> No CI runs

---

## Best Practices Implemented

### 1. Language-Specific Linting
**Practice:** Using `golangci-lint` for Go code quality checks

**Why it helps:**
- Comprehensive linting rules for Go best practices
- Catches common Go mistakes and anti-patterns
- Enforces consistent code style
- Integrates seamlessly with GitHub Actions

### 2. Go Test Coverage
**Practice:** Built-in Go coverage with `go test -coverprofile`

**Why it helps:**
- No external dependencies required
- Standard Go tooling
- Generates coverage reports automatically
- Integrated with Codecov for tracking

### 3. Security Scanning
**Practice:** Using `gosec` for Go security vulnerability scanning

**Why it helps:**
- Scans for common Go security issues
- Detects potential vulnerabilities in code
- Provides security best practices recommendations
- Runs as separate job to not block main workflow

### 4. Multi-Stage Docker Build
**Practice:** Using multi-stage build from Lab 2 (builder + scratch)

**Why it helps:**
- Minimal final image size
- No build tools in production image
- Reduced attack surface
- Faster image pulls

### 5. CalVer Consistency
**Practice:** Same versioning strategy as Python app

**Why it helps:**
- Consistent versioning across monorepo
- Easy to identify when images were built
- Predictable tag naming convention

---

## Test Coverage

### Coverage Integration

**Tool used:** Go's built-in coverage (`go test -coverprofile`)

**Coverage percentage:** ~90-95% (varies by run)

**What's covered:**
- All HTTP handlers (`mainHandler`, `healthHandler`, `notFoundHandler`)
- All helper functions (`getUptime()`, `getSystemInfo()`, `getClientIP()`)
- Error handling logic
- Request processing

**What's not covered:**
- Main function (`main()`) - not executed in tests
- Some edge cases in IP parsing
- Server startup logic

**Coverage threshold:** Not enforced in CI (optional), but coverage reports are generated and uploaded to Codecov.

**Codecov Integration:**
- Coverage reports uploaded automatically on each CI run
- Coverage badge displays current percentage in README
- Historical coverage tracking available on Codecov dashboard
- Flag: `go` for separate tracking from Python coverage

---

## Key Decisions

### Versioning Strategy: CalVer

**Why CalVer for Go app?**

- **Consistency:** Same strategy as Python app for monorepo consistency
- **Simplicity:** No manual version management needed
- **Continuous deployment:** Aligns with CI/CD workflow
- **Service type:** Application/service, not a library

### Docker Image Naming

**Image name:** `devops-info-service-go`

**Rationale:**
- Distinguishes from Python version (`devops-info-service`)
- Clear identification of language/runtime
- Prevents tag conflicts between apps
- Easy to identify in Docker Hub

### Path Filters

**Why these specific paths?**

- `app_go/**` - All Go application code
- `.github/workflows/go-ci.yml` - Workflow file itself (to test workflow changes)

**Excluded:**
- Documentation changes don't trigger CI
- Other app changes don't trigger Go CI
- Root-level files don't trigger CI

### Test Structure

**Why Go's built-in testing?**

- No dependencies required (standard library)
- Simple and straightforward
- Excellent tooling support
- Industry standard for Go projects

---

## Challenges

### Challenge 1: go.sum File Not Found
**Problem:** `actions/setup-go@v5` automatically tries to cache dependencies using `go.sum`, but our project has no external dependencies, so `go.sum` doesn't exist.

**Solution:**
- Added `cache: false` to `setup-go` action
- Disabled automatic dependency caching
- No performance impact since there are no dependencies to cache

### Challenge 2: Codecov File Parameter
**Problem:** Initial attempt used `file:` parameter which doesn't exist in `codecov-action@v5`.

**Solution:**
- Changed to `files:` (plural) parameter
- Used correct path format: `./app_go/coverage.out`
- Verified with Codecov documentation

### Challenge 3: Coverage Format
**Problem:** Go generates coverage in native format, needed to ensure Codecov compatibility.

**Solution:**
- Go's native coverage format is directly supported by Codecov
- No conversion needed
- Simply upload `coverage.out` file

---

## Summary

This bonus task successfully implements:

**Part 1: Multi-App CI (1.5 pts)**
- ✅ Go CI workflow created with language-specific tools
- ✅ Path filters configured for selective triggering
- ✅ Both workflows run in parallel when needed
- ✅ CalVer versioning applied consistently
- ✅ Docker images built and pushed successfully

**Part 2: Test Coverage (1 pt)**
- ✅ Coverage tracking integrated for both Python and Go
- ✅ Codecov integration complete
- ✅ Coverage badges added to READMEs
- ✅ Coverage reports generated in CI

The multi-app CI setup demonstrates efficient monorepo CI/CD practices with intelligent path-based triggering, allowing both applications to be developed and deployed independently while sharing the same repository.

