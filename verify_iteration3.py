#!/usr/bin/env python3
"""Quick verification of Iteration 3 implementation."""

import tempfile
from pathlib import Path

# Test 1: Schema initialization
print("=" * 60)
print("TEST 1: Schema and ingest_runs table creation")
print("=" * 60)

from pentest_agent.db.connection import init_session_db, open_session_db

with tempfile.TemporaryDirectory() as tmpdir:
    db_path = Path(tmpdir) / 'test.db'
    init_session_db(db_path)  # This creates the schema
    conn = open_session_db(db_path)
    
    # Check tables
    tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name").fetchall()
    table_names = [t['name'] for t in tables]
    
    if 'ingest_runs' in table_names:
        print("✓ ingest_runs table created")
        cols = conn.execute('PRAGMA table_info(ingest_runs)').fetchall()
        col_names = [c['name'] for c in cols]
        print(f"✓ Columns: {col_names}")
    else:
        print(f"✗ ingest_runs NOT in tables: {table_names}")
    
    conn.close()

# Test 2: Imports
print("\n" + "=" * 60)
print("TEST 2: Module imports")
print("=" * 60)

try:
    from pentest_agent.ingest.util import normalize_severity, host_id, endpoint_id
    from pentest_agent.ingest.sanitizer import Sanitizer
    from pentest_agent.ingest.resumable import compute_file_hash, get_or_create_ingest_run
    from pentest_agent.ingest.nmap import ingest_nmap
    from pentest_agent.ingest.nuclei import ingest_nuclei
    from pentest_agent.ingest.ffuf import ingest_ffuf
    from pentest_agent.ingest.openapi import ingest_openapi
    from pentest_agent.ingest.burp import ingest_burp
    from pentest_agent.ingest.http_req import ingest_http_req
    from pentest_agent.cli.cmd_ingest import app as ingest_app
    from pentest_agent.cli.cmd_show import app as show_app
    print("✓ All modules imported successfully")
except Exception as e:
    print(f"✗ Import failed: {e}")

# Test 3: Utility functions
print("\n" + "=" * 60)
print("TEST 3: Utility functions")
print("=" * 60)

# Test severity normalization
test_severities = ["critical", "High", "MEDIUM", "low", "9.5", "1.0", "unknown", ""]
for sev in test_severities:
    normalized = normalize_severity(sev)
    print(f"  normalize_severity('{sev}') → {normalized}")

# Test entity ID hashing
test_ip = "192.168.1.1"
hid = host_id(test_ip)
print(f"\n  host_id('{test_ip}') → {hid}")

# Test Sanitizer
test_string = "username=admin&password=secret123&token=eyJhbGc..."
sanitized = Sanitizer.sanitize_string(test_string)
print(f"\n  Sanitized: '{sanitized}'")

# Test 4: CLI registration
print("\n" + "=" * 60)
print("TEST 4: CLI command registration")
print("=" * 60)

from pentest_agent.cli.main import app as main_app
commands = [cmd.name for cmd in main_app.registered_commands]
groups = [tc.name for tc in main_app.registered_groups]
print(f"✓ Commands: {commands}")
print(f"✓ Subcommand groups: {groups}")

if 'ingest' in groups and 'show' in groups:
    print("✓ Both 'ingest' and 'show' groups registered")
else:
    print(f"✗ Missing groups. Expected: ingest, show. Found: {groups}")

print("\n" + "=" * 60)
print("VERIFICATION COMPLETE")
print("=" * 60)
