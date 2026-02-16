# OpenHands Development and Staging Deployment

This skill guides making code changes to OpenHands/OpenHands, deploying to staging for testing, and using Datadog to debug issues.

## Development Workflow

### 1. Make Code Changes

```bash
cd /workspace/project/OpenHands

# Check current branch
git branch

# Make your code changes...
```

### 2. Run Pre-commit Hooks

Before committing, run pre-commit to catch linting/formatting issues:

```bash
# Stage your changes
git add <files>

# Run pre-commit on staged files
pre-commit run --config ./dev_config/python/.pre-commit-config.yaml

# If pre-commit isn't installed
pip install pre-commit
~/.local/bin/pre-commit run --config ./dev_config/python/.pre-commit-config.yaml
```

### 3. Run Tests

```bash
# Install package in dev mode if needed
pip install -e .

# Run specific tests
python -m pytest tests/unit/path/to/test_file.py -v

# Run a specific test class
python -m pytest tests/unit/path/to/test_file.py::TestClassName -v
```

### 4. Commit and Push

```bash
# Commit with descriptive message
git commit -m "fix(component): Short description

Longer description if needed.

Co-authored-by: openhands <openhands@all-hands.dev>"

# Push to branch
git push origin <branch-name>
```

## Deploy to Staging

### Find PR Number

```bash
# Find PR number for your branch
curl -s -H "Authorization: Bearer $GITHUB_TOKEN" \
  "https://api.github.com/repos/OpenHands/OpenHands/pulls?head=OpenHands:<branch-name>&state=open" \
  | jq '.[0] | {number, title, html_url}'
```

### Trigger Staging Deployment

```bash
# Trigger the create-openhands-preview-pr workflow
curl -s -X POST -H "Authorization: Bearer $GITHUB_TOKEN" \
  -H "Accept: application/vnd.github.v3+json" \
  "https://api.github.com/repos/OpenHands/deploy/actions/workflows/201429127/dispatches" \
  -d '{"ref": "main", "inputs": {"prNumber": "<PR_NUMBER>"}}'
```

### Check Deployment Status

```bash
# Check recent workflow runs
curl -s -H "Authorization: Bearer $GITHUB_TOKEN" \
  "https://api.github.com/repos/OpenHands/deploy/actions/runs?workflow_id=201429127&per_page=5" \
  | jq '.workflow_runs[:3] | .[] | {id, status, conclusion, created_at, html_url}'

# Check specific run
curl -s -H "Authorization: Bearer $GITHUB_TOKEN" \
  "https://api.github.com/repos/OpenHands/deploy/actions/runs/<RUN_ID>" \
  | jq '{status, conclusion, html_url}'
```

### Access Staging Environment

After deployment completes, access your staging instance at:
```
https://ohpr-<PR_NUMBER>-<RANDOM>.staging.all-hands.dev/
```

## Datadog Log Analysis

### Prerequisites

Verify Datadog credentials are available:

```bash
[ -n "$DD_API_KEY" ] && echo "DD_API_KEY is set" || echo "DD_API_KEY is NOT set"
[ -n "$DD_APP_KEY" ] && echo "DD_APP_KEY is set" || echo "DD_APP_KEY is NOT set"
[ -n "$DD_SITE" ] && echo "DD_SITE is set" || echo "DD_SITE is NOT set"
```

### Search Logs by Conversation ID

```bash
curl -s -X POST "https://api.${DD_SITE}/api/v2/logs/events/search" \
  -H "DD-API-KEY: ${DD_API_KEY}" \
  -H "DD-APPLICATION-KEY: ${DD_APP_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "filter": {
      "query": "<conversation_id>",
      "from": "now-24h",
      "to": "now"
    },
    "sort": "-timestamp",
    "page": {"limit": 50}
  }' | jq '.data[] | {timestamp: .attributes.timestamp, message: .attributes.message}'
```

### Search Logs by Staging PR

```bash
# Search for logs from your staging PR
curl -s -X POST "https://api.${DD_SITE}/api/v2/logs/events/search" \
  -H "DD-API-KEY: ${DD_API_KEY}" \
  -H "DD-APPLICATION-KEY: ${DD_APP_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "filter": {
      "query": "ohpr-<PR_NUMBER>",
      "from": "now-24h",
      "to": "now"
    },
    "sort": "-timestamp",
    "page": {"limit": 50}
  }' | jq '.data[] | {timestamp: .attributes.timestamp, message: .attributes.message}'
```

### Search for Errors/Warnings

```bash
# Search for errors
curl -s -X POST "https://api.${DD_SITE}/api/v2/logs/events/search" \
  -H "DD-API-KEY: ${DD_API_KEY}" \
  -H "DD-APPLICATION-KEY: ${DD_APP_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "filter": {
      "query": "ohpr-<PR_NUMBER> status:error",
      "from": "now-24h",
      "to": "now"
    },
    "sort": "-timestamp",
    "page": {"limit": 50}
  }' | jq '.data[] | {timestamp: .attributes.timestamp, message: .attributes.message, status: .attributes.status}'

# Search for warnings
curl -s -X POST "https://api.${DD_SITE}/api/v2/logs/events/search" \
  -H "DD-API-KEY: ${DD_API_KEY}" \
  -H "DD-APPLICATION-KEY: ${DD_APP_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "filter": {
      "query": "ohpr-<PR_NUMBER> status:warn",
      "from": "now-24h",
      "to": "now"
    },
    "sort": "-timestamp",
    "page": {"limit": 50}
  }' | jq '.data[] | {timestamp: .attributes.timestamp, message: .attributes.message}'
```

### Search with Keywords

```bash
# Search for specific functionality
curl -s -X POST "https://api.${DD_SITE}/api/v2/logs/events/search" \
  -H "DD-API-KEY: ${DD_API_KEY}" \
  -H "DD-APPLICATION-KEY: ${DD_APP_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "filter": {
      "query": "ohpr-<PR_NUMBER> (keyword1 OR keyword2)",
      "from": "now-24h",
      "to": "now"
    },
    "sort": "-timestamp",
    "page": {"limit": 50}
  }' | jq '.data[] | {timestamp: .attributes.timestamp, message: .attributes.message}'
```

### Count Log Entries

```bash
# Get count of matching logs
curl -s -X POST "https://api.${DD_SITE}/api/v2/logs/events/search" \
  -H "DD-API-KEY: ${DD_API_KEY}" \
  -H "DD-APPLICATION-KEY: ${DD_APP_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "filter": {
      "query": "<your_query>",
      "from": "now-24h",
      "to": "now"
    },
    "page": {"limit": 1}
  }' | jq '.data | length'
```

## Analyzing Conversation Trajectories

If you have a trajectory zip file:

```bash
# Extract trajectory
unzip conversation_<id>.zip

# View metadata
cat meta.json | python3 -m json.tool

# Check first event (full_state) for configuration
python3 -c "import json; data = json.load(open('event_000000_*.json')); print(list(data['value'].keys()))"

# Search for specific field
python3 -c "import json; data = json.load(open('event_000000_*.json')); print(data['value'].get('field_name', 'NOT FOUND'))"
```

## Quick Reference

| Task | Command |
|------|---------|
| Find PR number | `gh pr list --head <branch>` or use API |
| Deploy to staging | Trigger workflow 201429127 with prNumber |
| Check deployment | Check workflow run status |
| Search logs | Use Datadog API with conversation ID or ohpr-<PR> |
| View errors | Add `status:error` to Datadog query |

## Workflow IDs

- **Create OpenHands preview PR**: `201429127`
- **Deploy**: `118962525`

## Tips

1. **Always run pre-commit** before pushing to catch issues early
2. **Use specific queries** in Datadog to narrow down logs
3. **Check both errors and warnings** when debugging
4. **Deployment takes ~5-10 minutes** - check workflow status before testing
5. **Staging URLs follow pattern**: `ohpr-<PR>-<random>.staging.all-hands.dev`
