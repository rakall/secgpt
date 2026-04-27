# Authenticated Web Crawling Guide

Complete guide to using SecGPT's authenticated crawling feature for discovering authenticated endpoints and attack surfaces.

## Overview

The authenticated crawler enables SecGPT to:
- Crawl web applications while authenticated
- Discover hidden endpoints behind authentication
- Map attack surfaces accessible only to logged-in users
- Integrate crawl results with SecGPT analysis

## Table of Contents

1. [Quick Start](#quick-start)
2. [Authentication Methods](#authentication-methods)
3. [Credential Management](#credential-management)
4. [Running Authenticated Crawls](#running-authenticated-crawls)
5. [Advanced Usage](#advanced-usage)
6. [Integration with Analysis](#integration-with-analysis)

---

## Quick Start

### 1. Add Credentials

```bash
# Add basic authentication
agent crawl add-cred \
  --target https://app.example.com \
  --type basic \
  --username admin \
  --password SecureP@ss123

# Add bearer token
agent crawl add-cred \
  --target https://api.example.com \
  --type bearer \
  --token eyJhbGc...
```

### 2. Run a Crawl

```bash
# Crawl authenticated application
agent crawl \
  --target https://app.example.com \
  --max-depth 3 \
  --max-pages 50

# Results are ingested into current session
```

### 3. View Results

```bash
# View discovered endpoints
agent show endpoints

# View high-value targets
agent kb search "attack surface"
```

---

## Authentication Methods

SecGPT supports 6 authentication methods:

### 1. Basic Authentication

HTTP Basic Auth (RFC 7617)

```bash
agent crawl add-cred \
  --target https://app.example.com \
  --type basic \
  --username user \
  --password pass
```

**Use Cases:**
- Legacy applications
- Internal tools
- Simple APIs

---

### 2. Bearer Token

OAuth 2.0 / JWT tokens

```bash
agent crawl add-cred \
  --target https://api.example.com \
  --type bearer \
  --token eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Use Cases:**
- Modern REST APIs
- Microservices
- Mobile backends

---

### 3. API Key

Custom header or query parameter authentication

```bash
# Header-based API key
agent crawl add-cred \
  --target https://api.example.com \
  --type apikey \
  --api-key 1234567890abcdef \
  --header-name X-API-Key

# Query parameter
agent crawl add-cred \
  --target https://api.example.com \
  --type apikey \
  --api-key 1234567890abcdef \
  --param-name api_key
```

**Use Cases:**
- Third-party APIs
- Webhook endpoints
- Cloud services

---

### 4. OAuth 2.0 Client Credentials

Automated OAuth 2.0 flow

```bash
agent crawl add-cred \
  --target https://api.example.com \
  --type oauth2 \
  --client-id my_client_id \
  --client-secret my_client_secret \
  --token-url https://auth.example.com/oauth/token \
  --scope "read write"
```

**Use Cases:**
- Service-to-service auth
- B2B integrations
- Enterprise APIs

---

### 5. Session Cookie

Form-based login with session management

```bash
agent crawl add-cred \
  --target https://app.example.com \
  --type session \
  --username user@example.com \
  --password SecurePass123 \
  --login-url https://app.example.com/login \
  --cookie-name PHPSESSID
```

**Optional CSRF protection:**

```bash
agent crawl add-cred \
  --target https://app.example.com \
  --type session \
  --username user \
  --password pass \
  --login-url https://app.example.com/login \
  --csrf-token-name csrf_token
```

**Use Cases:**
- Traditional web applications
- CMSs (WordPress, Drupal)
- Admin panels

---

## Credential Management

### List Stored Credentials

```bash
# View all credentials for current session
agent crawl list-creds

# Output:
# Target: https://app.example.com
# Type: basic
# ----------
# Target: https://api.example.com
# Type: bearer
```

### Delete Credentials

```bash
# Remove specific credential
agent crawl delete-cred --target https://app.example.com

# Confirmation required
```

### Security

Credentials are stored securely using the system keyring:
- **Windows**: Windows Credential Manager
- **macOS**: Keychain
- **Linux**: Secret Service API (GNOME Keyring / KWallet)

All sensitive data (passwords, tokens, secrets) are encrypted at rest.

---

## Running Authenticated Crawls

### Basic Crawl

```bash
agent crawl --target https://app.example.com
```

**Defaults:**
- Max depth: 3
- Max pages: 100
- Rate limit: 10 req/sec
- Respect robots.txt: Yes

### Customized Crawl

```bash
agent crawl \
  --target https://app.example.com/dashboard \
  --max-depth 5 \
  --max-pages 200 \
  --rate-limit 5 \
  --follow-external
```

**Parameters:**
- `--max-depth`: How many links deep to crawl (1-10)
- `--max-pages`: Maximum pages to visit
- `--rate-limit`: Requests per second (1-50)
- `--follow-external`: Crawl external domains (default: false)

### Crawl Subdomains

```bash
# Crawl subdomain with separate credentials
agent crawl add-cred \
  --target https://admin.example.com \
  --type basic \
  --username admin \
  --password AdminPass

agent crawl --target https://admin.example.com
```

---

## Advanced Usage

### Multi-Step Workflows

```bash
# 1. Add credentials for multiple targets
agent crawl add-cred --target https://app.example.com --type basic --username user1 --password pass1
agent crawl add-cred --target https://api.example.com --type bearer --token token123

# 2. Crawl both applications
agent crawl --target https://app.example.com --max-depth 3
agent crawl --target https://api.example.com --max-depth 2

# 3. Analyze combined attack surface
agent analysis run --query "What are the high-value authenticated endpoints?"
```

### Endpoint Discovery

After crawling, use the discovery module:

```python
from pathlib import Path
from pentest_agent.crawl.discovery import EndpointDiscovery

session_path = Path("sessions/192.168.1.100")
discovery = EndpointDiscovery(session_path / "session.db")

# Get summary
summary = discovery.analyze()
print(f"Found {summary['total_endpoints']} endpoints")
print(f"Admin endpoints: {summary['admin_endpoints']}")
print(f"API endpoints: {summary['api_endpoints']}")

# Get high-value targets
targets = discovery.get_high_value_targets()
for target in targets[:5]:
    print(f"[{target['priority']}] {target['method']} {target['path']}")
```

### Integration with Other Tools

```bash
# 1. Run authenticated crawl
agent crawl --target https://app.example.com

# 2. Export endpoints to file
agent show endpoints --format json > endpoints.json

# 3. Use with other tools (ffuf, nuclei, etc.)
ffuf -w endpoints.json:FUZZ -u FUZZ -mc 200

# 4. Ingest results back
agent ingest ffuf results.json
```

---

## Integration with Analysis

### Analyze Crawl Results

```bash
# Ask about discovered endpoints
agent analysis run --query "What sensitive endpoints were discovered?"

# Get vulnerability recommendations
agent analysis run --query "Which endpoints should I test for authorization bypass?"

# Review forms and inputs
agent analysis run --query "List all forms that accept file uploads"
```

### Generate Reports

```bash
# Include crawl data in report
agent report generate \
  --format markdown \
  --include-endpoints \
  --include-forms

# Output: sessions/192.168.1.100/reports/report_20260427_...md
```

### Using the TUI

1. Launch TUI: `agent-tui`
2. Select your session
3. Press `Enter` to browse findings
4. Endpoints appear in findings table
5. Use filters to find specific endpoint types

---

## Troubleshooting

### Authentication Failures

**Symptom:** "Authentication failed" error

**Solutions:**
1. Verify credentials are correct
2. Check if login URL is accurate (for session auth)
3. Ensure token hasn't expired (for bearer/OAuth)
4. Test manually in browser first

### Rate Limiting

**Symptom:** HTTP 429 errors

**Solution:**
```bash
# Reduce rate limit
agent crawl --target https://app.example.com --rate-limit 2
```

### Incomplete Crawls

**Symptom:** Fewer pages than expected

**Possible Causes:**
1. JavaScript-heavy SPA (crawler doesn't execute JS)
2. External links hit (use `--follow-external`)
3. Depth limit reached
4. Page limit reached

**Solutions:**
```bash
# Increase limits
agent crawl --target https://app.example.com --max-depth 5 --max-pages 500

# For SPAs, use browser automation tools (Selenium, Playwright) then ingest HAR files
```

### Missing Credentials

**Symptom:** "No credentials found for target"

**Solution:**
```bash
# List credentials to verify target URL matches exactly
agent crawl list-creds

# Add with exact URL
agent crawl add-cred --target https://app.example.com ...
```

---

## Best Practices

### 1. Scope Management

Always define crawl scope carefully:

```bash
# ✅ Good: Specific starting point
agent crawl --target https://app.example.com/dashboard

# ❌ Bad: Too broad, may crawl unintended areas
agent crawl --target https://example.com --follow-external
```

### 2. Credential Rotation

For long-running assessments:

```bash
# Delete old credentials
agent crawl delete-cred --target https://app.example.com

# Add fresh credentials
agent crawl add-cred --target https://app.example.com --type bearer --token <new_token>
```

### 3. Rate Limiting

Respect target application:

```bash
# Production: Be conservative
agent crawl --target https://app.example.com --rate-limit 2

# Staging: Can be more aggressive
agent crawl --target https://staging.example.com --rate-limit 20
```

### 4. Session Isolation

Keep different targets in separate sessions:

```bash
# Initialize separate sessions
agent init --session app.example.com
agent init --session api.example.com

# Switch sessions
agent config set active_session app.example.com
agent crawl --target https://app.example.com
```

---

## Example Workflows

### Workflow 1: API Testing

```bash
# 1. Get OAuth token
agent crawl add-cred \
  --target https://api.example.com \
  --type oauth2 \
  --client-id my_client \
  --client-secret my_secret \
  --token-url https://auth.example.com/token

# 2. Crawl API
agent crawl --target https://api.example.com/v1 --max-depth 2

# 3. Generate payloads for discovered endpoints
agent payload generate --all

# 4. Review in TUI
agent-tui
```

### Workflow 2: Web Application Pentest

```bash
# 1. Login credentials
agent crawl add-cred \
  --target https://webapp.example.com \
  --type session \
  --username testuser@example.com \
  --password TestPass123 \
  --login-url https://webapp.example.com/login

# 2. Crawl as authenticated user
agent crawl --target https://webapp.example.com/dashboard --max-depth 4

# 3. Run Nuclei on discovered endpoints
nuclei -l <(agent show endpoints) -o nuclei_results.json

# 4. Ingest results
agent ingest nuclei nuclei_results.json

# 5. Analyze findings
agent analysis run --query "Prioritize findings from authenticated areas"
```

---

## API Reference

### Python API

```python
from pathlib import Path
from pentest_agent.auth.manager import CredentialManager
from pentest_agent.auth.handlers import BasicAuthHandler, BearerTokenHandler
from pentest_agent.crawl.crawler import AuthenticatedCrawler

# Setup credentials
session_path = Path("sessions/example.com")
cred_mgr = CredentialManager(session_path)

# Add credentials
auth_handler = BasicAuthHandler("user", "pass")
cred_mgr.store_credential("https://app.example.com", auth_handler)

# Run crawl
crawler = AuthenticatedCrawler(
    session_path=session_path,
    cred_manager=cred_mgr
)

results = crawler.crawl(
    start_url="https://app.example.com",
    max_depth=3,
    max_pages=100
)

print(f"Discovered {len(results['endpoints'])} endpoints")
print(f"Found {len(results['forms'])} forms")
```

---

## Security Considerations

### Read-Only Operation

SecGPT's crawler is **read-only**:
- Only sends GET requests
- Does not submit forms
- Does not execute POST/PUT/DELETE
- Does not execute JavaScript

### Credential Storage

- Credentials stored in system keyring (encrypted)
- Never logged to disk
- Cleared when session is deleted
- Accessible only to current user

### Network Safety

```bash
# Always verify target before crawling
whois example.com

# Use VPN for sensitive assessments
# Configure proxy if needed (future feature)
```

---

## See Also

- [Payload Generation Guide](PAYLOAD_GENERATION_GUIDE.md)
- [TUI Guide](TUI_GUIDE.md)
- [Analysis Documentation](../README.md#analysis)

---

*Last updated: April 27, 2026*
