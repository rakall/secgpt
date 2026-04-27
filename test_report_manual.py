#!/usr/bin/env python3
"""Manual test for report generation."""

from pathlib import Path
import sys

# Add parent dir to path
sys.path.insert(0, str(Path(__file__).parent))

from pentest_agent.db.connection import open_session_db
from pentest_agent.cli.cmd_report import (
    _query_scope,
    _query_hosts,
    _query_endpoints,
    _query_findings,
    _query_latest_analysis_run,
    _build_markdown_report,
    _build_json_export,
)
import json

def test_report_generation():
    """Test report generation with real session data."""
    print("=" * 60)
    print("Testing Report Generation")
    print("=" * 60)
    
    session_db_path = Path("sessions/192.168.100.122/session.db")
    
    if not session_db_path.exists():
        print(f"❌ Session DB not found: {session_db_path}")
        return False
    
    print(f"✓ Found session DB: {session_db_path}")
    
    # Open DB
    try:
        conn = open_session_db(session_db_path)
        print("✓ Opened session database")
    except Exception as e:
        print(f"❌ Failed to open DB: {e}")
        return False
    
    # Query data
    try:
        print("\n--- Querying Session Data ---")
        scope_data = _query_scope(conn)
        print(f"  Scope entries: {len(scope_data)}")
        
        hosts = _query_hosts(conn)
        print(f"  Hosts: {len(hosts)}")
        
        endpoints = _query_endpoints(conn)
        print(f"  Endpoints: {len(endpoints)}")
        
        findings = _query_findings(conn)
        print(f"  Findings: {len(findings)}")
        
        analysis_run = _query_latest_analysis_run(conn)
        if analysis_run:
            print(f"  Latest analysis run: {analysis_run['run_id']}")
        else:
            print("  No analysis runs found")
        
    except Exception as e:
        print(f"❌ Failed to query data: {e}")
        conn.close()
        return False
    
    # Build markdown report
    try:
        print("\n--- Building Markdown Report ---")
        target = session_db_path.parent.name
        markdown_report = _build_markdown_report(
            target, scope_data, hosts, endpoints, findings, analysis_run
        )
        print(f"✓ Generated markdown report ({len(markdown_report)} chars)")
        
        # Save to file
        report_path = session_db_path.parent / "reports" / "test_manual.md"
        report_path.parent.mkdir(exist_ok=True)
        report_path.write_text(markdown_report, encoding="utf-8")
        print(f"✓ Saved to: {report_path}")
        
        # Show preview
        lines = markdown_report.split("\n")
        print("\n--- Report Preview (first 30 lines) ---")
        for line in lines[:30]:
            print(line)
        print(f"... ({len(lines)} total lines)")
        
    except Exception as e:
        print(f"❌ Failed to build markdown report: {e}")
        import traceback
        traceback.print_exc()
        conn.close()
        return False
    
    # Build JSON export
    try:
        print("\n--- Building JSON Export ---")
        json_export = _build_json_export(
            target, scope_data, hosts, endpoints, findings, analysis_run
        )
        json_str = json.dumps(json_export, indent=2)
        print(f"✓ Generated JSON export ({len(json_str)} chars)")
        
        # Save to file
        json_path = session_db_path.parent / "reports" / "test_manual.json"
        json_path.write_text(json_str, encoding="utf-8")
        print(f"✓ Saved to: {json_path}")
        
        # Show metadata
        print("\n--- JSON Export Metadata ---")
        print(json.dumps(json_export["metadata"], indent=2))
        
    except Exception as e:
        print(f"❌ Failed to build JSON export: {e}")
        import traceback
        traceback.print_exc()
        conn.close()
        return False
    
    conn.close()
    print("\n" + "=" * 60)
    print("✅ ALL TESTS PASSED")
    print("=" * 60)
    return True


if __name__ == "__main__":
    success = test_report_generation()
    sys.exit(0 if success else 1)
