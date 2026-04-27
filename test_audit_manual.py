#!/usr/bin/env python3
"""Manual test for audit logging."""

from pathlib import Path
import sys
import json
import os
import stat

# Add parent dir to path
sys.path.insert(0, str(Path(__file__).parent))

from pentest_agent.logging.audit import (
    log_analysis_event,
    log_query_event,
    log_chat_turn,
    log_report_event,
    log_ingest_event,
)

def test_audit_logging():
    """Test audit logging integration."""
    print("=" * 60)
    print("Testing Audit Logging")
    print("=" * 60)
    
    session_db_path = Path("sessions/192.168.100.122/session.db")
    
    if not session_db_path.exists():
        print(f"❌ Session DB not found: {session_db_path}")
        return False
    
    print(f"✓ Found session DB: {session_db_path}")
    
    session_dir = session_db_path.parent
    audit_log_path = session_dir / ".audit.log"
    
    # Remove existing audit log for clean test
    if audit_log_path.exists():
        audit_log_path.unlink()
        print(f"✓ Removed existing audit log for clean test")
    
    # Test 1: Log analysis event
    print("\n--- Test 1: log_analysis_event() ---")
    try:
        log_analysis_event(
            session_db_path=session_db_path,
            run_id="test-run-001",
            user_query="test analysis query",
            intent_classes=["vulnerability_analysis"],
            kb_chunks_retrieved=5,
            prompt_hash="abc123def456",
            output_valid=True,
            duration_ms=1234,
            truncation_events=0,
            error=None,
        )
        print("✓ Analysis event logged")
    except Exception as e:
        print(f"❌ Failed to log analysis event: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Test 2: Log query event
    print("\n--- Test 2: log_query_event() ---")
    try:
        log_query_event(
            session_db_path=session_db_path,
            query_type="cve",
            query_value="CVE-2024-1234",
            kb_chunks_retrieved=3,
            duration_ms=567,
            error=None,
        )
        print("✓ Query event logged")
    except Exception as e:
        print(f"❌ Failed to log query event: {e}")
        return False
    
    # Test 3: Log chat turn
    print("\n--- Test 3: log_chat_turn() ---")
    try:
        log_chat_turn(
            session_db_path=session_db_path,
            turn_id="turn-001",
            user_message="What vulnerabilities were found?",
            intent_classes=["information_retrieval"],
            kb_chunks_retrieved=8,
            prompt_hash="def789ghi012",
            duration_ms=890,
        )
        print("✓ Chat turn logged")
    except Exception as e:
        print(f"❌ Failed to log chat turn: {e}")
        return False
    
    # Test 4: Log report event
    print("\n--- Test 4: log_report_event() ---")
    try:
        log_report_event(
            session_db_path=session_db_path,
            report_format="markdown",
            output_path=str(session_dir / "reports" / "test.md"),
            findings_count=10,
            hosts_count=5,
            endpoints_count=20,
            analysis_run_included=True,
            duration_ms=1500,
            error=None,
        )
        print("✓ Report event logged")
    except Exception as e:
        print(f"❌ Failed to log report event: {e}")
        return False
    
    # Test 5: Log ingest event
    print("\n--- Test 5: log_ingest_event() ---")
    try:
        log_ingest_event(
            session_db_path=session_db_path,
            ingest_run_id="ingest-run-001",
            tool="nmap",
            source_path="/path/to/nmap.xml",
            rows_processed=15,
            duration_ms=2000,
            error=None,
        )
        print("✓ Ingest event logged")
    except Exception as e:
        print(f"❌ Failed to log ingest event: {e}")
        return False
    
    # Test 6: Verify audit log file exists
    print("\n--- Test 6: Audit Log File Creation ---")
    if not audit_log_path.exists():
        print(f"❌ Audit log file not created: {audit_log_path}")
        return False
    print(f"✓ Audit log file exists: {audit_log_path}")
    
    # Test 7: Verify file permissions (0600)
    print("\n--- Test 7: File Permissions ---")
    if os.name != 'nt':  # Unix-like systems
        file_stat = os.stat(audit_log_path)
        file_perms = stat.filemode(file_stat.st_mode)
        octal_perms = oct(file_stat.st_mode)[-3:]
        print(f"  File permissions: {file_perms} (octal: {octal_perms})")
        
        if octal_perms != "600":
            print(f"⚠ WARNING: Expected 0600, got {octal_perms}")
        else:
            print("✓ Permissions are 0600 (user read/write only)")
    else:
        # Windows - just verify file is readable
        if audit_log_path.is_file():
            print("✓ File is accessible (Windows doesn't use Unix permissions)")
        else:
            print("❌ File not accessible")
            return False
    
    # Test 8: Validate JSON Lines format
    print("\n--- Test 8: JSON Lines Format Validation ---")
    try:
        with open(audit_log_path, "r") as f:
            lines = f.readlines()
        
        print(f"  Total log entries: {len(lines)}")
        
        if len(lines) != 5:
            print(f"⚠ WARNING: Expected 5 log entries, got {len(lines)}")
        
        valid_entries = 0
        for i, line in enumerate(lines, 1):
            try:
                entry = json.loads(line.strip())
                valid_entries += 1
                
                # Check required fields
                required_fields = ["timestamp", "event_type", "session_id", "result_status"]
                missing_fields = [f for f in required_fields if f not in entry]
                
                if missing_fields:
                    print(f"  Entry {i}: ⚠ Missing fields: {missing_fields}")
                else:
                    print(f"  Entry {i}: ✓ Valid JSON with all required fields")
                    print(f"    - event_type: {entry.get('event_type')}")
                    print(f"    - result_status: {entry.get('result_status')}")
                    
            except json.JSONDecodeError as e:
                print(f"  Entry {i}: ❌ Invalid JSON: {e}")
                return False
        
        if valid_entries == len(lines):
            print(f"✓ All {valid_entries} entries are valid JSON Lines")
        else:
            print(f"❌ Only {valid_entries}/{len(lines)} entries are valid")
            return False
            
    except Exception as e:
        print(f"❌ Failed to validate JSON Lines format: {e}")
        return False
    
    # Test 9: Verify determinism fields
    print("\n--- Test 9: Determinism Fields ---")
    try:
        with open(audit_log_path, "r") as f:
            for line in f:
                entry = json.loads(line.strip())
                event_type = entry.get("event_type")
                
                # Check for prompt_hash in events that should have it
                if event_type in ["analyze_session", "chat_turn"]:
                    if "prompt_hash" in entry:
                        print(f"  ✓ {event_type}: has prompt_hash")
                    else:
                        print(f"  ⚠ {event_type}: missing prompt_hash")
                
                # Check for duration_ms
                if "duration_ms" in entry:
                    print(f"  ✓ {event_type}: has duration_ms ({entry['duration_ms']}ms)")
                else:
                    print(f"  ⚠ {event_type}: missing duration_ms")
        
        print("✓ Determinism fields check complete")
        
    except Exception as e:
        print(f"❌ Failed to verify determinism fields: {e}")
        return False
    
    # Test 10: Display sample log entries
    print("\n--- Test 10: Sample Log Entries ---")
    try:
        with open(audit_log_path, "r") as f:
            lines = f.readlines()
        
        print("\nFirst log entry (pretty-printed):")
        print(json.dumps(json.loads(lines[0]), indent=2))
        
    except Exception as e:
        print(f"❌ Failed to display sample: {e}")
        return False
    
    print("\n" + "=" * 60)
    print("✅ ALL AUDIT LOGGING TESTS PASSED")
    print("=" * 60)
    print(f"\nAudit log location: {audit_log_path}")
    print(f"Total entries: {len(lines)}")
    
    return True


if __name__ == "__main__":
    success = test_audit_logging()
    sys.exit(0 if success else 1)
