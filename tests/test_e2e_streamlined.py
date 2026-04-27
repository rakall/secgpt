#!/usr/bin/env python3
"""
Streamlined End-to-End Workflow Test

Uses direct function calls instead of subprocess for reliability.
Tests the complete pentest workflow with realistic data.
"""

from pathlib import Path
import sys
import json
import shutil

# Add parent dir to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from pentest_agent.cli.cmd_init import init
from pentest_agent.db.connection import open_session_db
from pentest_agent.ingest.nmap import parse_nmap
from pentest_agent.ingest.nuclei import parse_nuclei
from pentest_agent.ingest.openapi import parse_openapi_spec


def run_streamlined_e2e():
    """Run streamlined E2E test using direct functions."""
    print("=" * 70)
    print("Streamlined E2E Workflow Test")
    print("=" * 70)
    
    test_session = "10.0.1.50"
    session_dir = Path(f"sessions/{test_session}")
    session_db = session_dir / "session.db"
    test_data_dir = Path("test_data")
    
    # Clean up
    if session_dir.exists():
        shutil.rmtree(session_dir)
        print("PASS: Cleaned up previous session")
    
    # Phase 1: Initialize
    print("\n" + "-" * 70)
    print("PHASE 1: Session Init")
    print("-" * 70)
    
    init(test_session)
    
    if not session_db.exists():
        print("FAIL: session.db not created")
        return False
    
    print("PASS: Session initialized")
    print(f"  - Directory: {session_dir}")
    print(f"  - Database: {session_db}")
    
    # Phase 2: Scope
    print("\n" + "-" * 70)
    print("PHASE 2: Scope Definition")
    print("-" * 70)
    
    conn = open_session_db(session_db)
    
    # Add scope
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    
    conn.execute("INSERT INTO scope (type, value, added_at) VALUES (?, ?, ?)",
                ("cidr", "10.0.1.0/24", now))
    conn.execute("INSERT INTO scope (type, value, added_at) VALUES (?, ?, ?)",
                ("ip", "10.0.1.50", now))
    conn.commit()
    
    scope_count = conn.execute("SELECT COUNT(*) FROM scope").fetchone()[0]
    
    if scope_count != 2:
        print(f"FAIL: Expected 2 scope entries, got {scope_count}")
        return False
    
    print("PASS: Scope defined")
    print("  - 10.0.1.0/24 (CIDR)")
    print("  - 10.0.1.50 (IP)")
    
    # Phase 3: Ingestion
    print("\n" + "-" * 70)
    print("PHASE 3: Data Ingestion")
    print("-" * 70)
    
    # Nmap
    nmap_file = test_data_dir / "nmap_scan.xml"
    if not nmap_file.exists():
        print(f"FAIL: Test data not found: {nmap_file}")
        return False
    
    nmap_data = parse_nmap(nmap_file)
    
    # Import hosts/ports
    from pentest_agent.ingest.util import insert_hosts_ports
    from pentest_agent.ingest.sanitizer import sanitize_session_ingestion
    
    sanitized = sanitize_session_ingestion(
        session_db=session_db,
        hosts=nmap_data.hosts,
        ports=nmap_data.ports,
        endpoints=[],
        findings=[]
    )
    
    insert_hosts_ports(conn, sanitized.hosts, sanitized.ports)
    conn.commit()
    
    hosts_count = conn.execute("SELECT COUNT(*) FROM hosts").fetchone()[0]
    ports_count = conn.execute("SELECT COUNT(*) FROM ports").fetchone()[0]
    
    print(f"PASS: Nmap ingestion complete")
    print(f"  - Hosts: {hosts_count}")
    print(f"  - Ports: {ports_count}")
    
    # Nuclei
    nuclei_file = test_data_dir / "nuclei_scan.json"
    nuclei_data = parse_nuclei(nuclei_file)
    
    sanitized_findings = sanitize_session_ingestion(
        session_db=session_db,
        hosts=[],
        ports=[],
        endpoints=[],
        findings=nuclei_data.findings
    )
    
    # Insert findings
    from pentest_agent.ingest.util import insert_findings
    insert_findings(conn, sanitized_findings.findings)
    conn.commit()
    
    findings_count = conn.execute("SELECT COUNT(*) FROM findings").fetchone()[0]
    
    print(f"PASS: Nuclei ingestion complete")
    print(f"  - Findings: {findings_count}")
    
    # OpenAPI
    openapi_file = test_data_dir / "openapi_spec.json"
    openapi_data = parse_openapi_spec(openapi_file)
    
    sanitized_endpoints = sanitize_session_ingestion(
        session_db=session_db,
        hosts=[],
        ports=[],
        endpoints=openapi_data.endpoints,
        findings=[]
    )
    
    # Insert endpoints
    from pentest_agent.ingest.util import insert_endpoints
    insert_endpoints(conn, sanitized_endpoints.endpoints)
    conn.commit()
    
    endpoints_count = conn.execute("SELECT COUNT(*) FROM endpoints").fetchone()[0]
    
    print(f"PASS: OpenAPI ingestion complete")
    print(f"  - Endpoints: {endpoints_count}")
    
    # Phase 4: Report Generation
    print("\n" + "-" * 70)
    print("PHASE 4: Report Generation")
    print("-" * 70)
    
    from pentest_agent.cli.cmd_report import (
        _query_scope, _query_hosts, _query_endpoints, _query_findings,
        _build_markdown_report, _build_json_export
    )
    
    scope_data = _query_scope(conn)
    hosts_data = _query_hosts(conn)
    endpoints_data = _query_endpoints(conn)
    findings_data = _query_findings(conn)
    
    # Generate markdown
    md_report = _build_markdown_report(
        target=test_session,
        scope_data=scope_data,
        hosts=hosts_data,
        endpoints=endpoints_data,
        findings=findings_data,
        analysis_run=None
    )
    
    if len(md_report) < 100:
        print("FAIL: Markdown report too short")
        return False
    
    print("PASS: Markdown report generated")
    print(f"  - Size: {len(md_report)} chars")
    
    # Save report
    reports_dir = session_dir / "reports"
    reports_dir.mkdir(exist_ok=True)
    
    md_path = reports_dir / "e2e_test.md"
    md_path.write_text(md_report, encoding="utf-8")
    
    print(f"  - Saved: {md_path}")
    
    # Generate JSON
    json_export = _build_json_export(
        target=test_session,
        scope_data=scope_data,
        hosts=hosts_data,
        endpoints=endpoints_data,
        findings=findings_data,
        analysis_run=None
    )
    
    json_path = reports_dir / "e2e_test.json"
    json_path.write_text(json.dumps(json_export, indent=2), encoding="utf-8")
    
    print(f"PASS: JSON export generated")
    print(f"  - Saved: {json_path}")
    
    # Verify JSON structure
    required_keys = ["metadata", "scope", "hosts", "endpoints", "findings"]
    missing = [k for k in required_keys if k not in json_export]
    
    if missing:
        print(f"FAIL: JSON missing keys: {missing}")
        return False
    
    print("PASS: JSON structure valid")
    
    conn.close()
    
    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    
    print("\nPASS: All phases completed successfully\n")
    
    print("Data Summary:")
    print(f"  - Scope entries: {len(scope_data)}")
    print(f"  - Hosts discovered: {len(hosts_data)}")
    print(f"  - Open ports: {ports_count}")
    print(f"  - API endpoints: {len(endpoints_data)}")
    print(f"  - Findings: {len(findings_data)}")
    
    # Finding breakdown
    if findings_data:
        critical = sum(1 for f in findings_data if f.get("normalized_severity") == "CRITICAL")
        high = sum(1 for f in findings_data if f.get("normalized_severity") == "HIGH")
        medium = sum(1 for f in findings_data if f.get("normalized_severity") == "MEDIUM")
        low = sum(1 for f in findings_data if f.get("normalized_severity") == "LOW")
        
        print(f"\nFindings by Severity:")
        print(f"  - CRITICAL: {critical}")
        print(f"  - HIGH: {high}")
        print(f"  - MEDIUM: {medium}")
        print(f"  - LOW: {low}")
    
    print(f"\nReports Generated:")
    print(f"  - {md_path}")
    print(f"  - {json_path}")
    
    print("\n" + "=" * 70)
    print("RESULT: PASS - End-to-End Workflow Complete")
    print("=" * 70)
    
    return True


if __name__ == "__main__":
    try:
        success = run_streamlined_e2e()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\nFAIL: Exception occurred: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
