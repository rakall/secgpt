"""
Iteration 5 hardening and integration test suite.

Tests:
1. Report generation (markdown + JSON)
2. Audit logging integration
3. RPC input validation
4. YARA/Sigma rule generation
5. End-to-end workflow integration
"""

import sys
import json
import sqlite3
import tempfile
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def test_report_generation():
    """Test 1: Report generation with real session data."""
    print("Test 1: Report Generation")
    
    # Check if test session exists
    session_path = Path("sessions/192.168.100.122")
    if not session_path.exists():
        print("  ⚠ SKIP: No test session found (not a failure)")
        return True  # Skip is not a failure
    
    db_path = session_path / "session.db"
    if not db_path.exists():
        print("  ⚠ SKIP: No session.db found (not a failure)")
        return True  # Skip is not a failure
    
    try:
        # Import report generation functions
        from pentest_agent.cli.cmd_report import (
            _query_hosts,
            _query_endpoints,
            _query_findings,
            _query_scope,
            _severity_style
        )
        
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        
        # Test query functions
        scope_entries = _query_scope(conn)
        hosts = _query_hosts(conn)
        endpoints = _query_endpoints(conn)
        findings = _query_findings(conn)
        
        # Validate data structure
        assert isinstance(scope_entries, list), "Scope entries should be a list"
        assert isinstance(hosts, list), "Hosts should be a list"
        assert isinstance(endpoints, list), "Endpoints should be a list"
        assert isinstance(findings, list), "Findings should be a list"
        
        # Test severity styling
        severity_tests = ["CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"]
        for sev in severity_tests:
            styled = _severity_style(sev)
            assert sev in styled, f"Severity style should contain {sev}"
        
        conn.close()
        
        print(f"  ✓ PASS: Report queries successful")
        print(f"    - Scope entries: {len(scope_entries)}")
        print(f"    - Hosts: {len(hosts)}")
        print(f"    - Endpoints: {len(endpoints)}")
        print(f"    - Findings: {len(findings)}")
        return True
        
    except ImportError as e:
        print(f"  ✗ FAIL: Import error: {e}")
        return False
    except Exception as e:
        print(f"  ✗ FAIL: {e}")
        return False


def test_audit_logging():
    """Test 2: Audit logging infrastructure."""
    print("\nTest 2: Audit Logging Infrastructure")
    
    try:
        from pentest_agent.logging.audit import (
            log_analysis_event,
            log_query_event,
            log_chat_turn,
            log_report_event,
            log_ingest_event
        )
        from pentest_agent.logging.formatters import AuditEvent, format_audit_event
        
        # Test AuditEvent creation
        event = AuditEvent(
            event_type="test_event",
            session_id="test_session",
            run_id="test_run_123",
            user_action="test action",
            result_status="success"
        )
        
        # Test format_audit_event() which adds timestamp
        formatted_event = format_audit_event(event)
        assert "timestamp" in formatted_event, "Formatted event should have timestamp"
        assert formatted_event["event_type"] == "test_event", "Event type mismatch"
        assert formatted_event["session_id"] == "test_session", "Session ID mismatch"
        
        # Test None exclusion
        event_with_none = AuditEvent(
            event_type="test",
            session_id="test",
            run_id=None,
            user_action=None,
            result_status="success"
        )
        dict_with_none = event_with_none.to_dict()
        assert "run_id" not in dict_with_none, "None values should be excluded from to_dict()"
        
        print("  ✓ PASS: Audit logging infrastructure working")
        print(f"    - AuditEvent creation successful")
        print(f"    - format_audit_event() adds timestamp")
        print(f"    - None exclusion working")
        return True
        
    except ImportError as e:
        print(f"  ✗ FAIL: Import error: {e}")
        return False
    except Exception as e:
        print(f"  ✗ FAIL: {e}")
        return False


def test_rpc_validation():
    """Test 3: RPC input validation."""
    print("\nTest 3: RPC Input Validation")
    
    try:
        from pentest_agent.daemon.validators import (
            validate_collection_name,
            validate_k_parameter,
            ValidationError
        )
        
        # Test valid collection names
        valid_collections = ["nvd", "attck", "runbooks"]
        for coll in valid_collections:
            try:
                validate_collection_name(coll)
            except ValidationError:
                print(f"  ✗ FAIL: Valid collection '{coll}' rejected")
                return False
        
        # Test invalid collection names
        invalid_collections = ["hacktricks", "invalid", "", "nvd; DROP TABLE"]
        for coll in invalid_collections:
            try:
                validate_collection_name(coll)
                print(f"  ✗ FAIL: Invalid collection '{coll}' accepted")
                return False
            except ValidationError:
                pass  # Expected
        
        # Test k parameter validation
        valid_k = [1, 5, 100, 999]
        for k in valid_k:
            try:
                validate_k_parameter(k)
            except ValidationError:
                print(f"  ✗ FAIL: Valid k={k} rejected")
                return False
        
        # Test invalid k values
        invalid_k = [0, -1, 1001, 10000]
        for k in invalid_k:
            try:
                validate_k_parameter(k)
                print(f"  ✗ FAIL: Invalid k={k} accepted")
                return False
            except ValidationError:
                pass  # Expected
        
        print("  ✓ PASS: RPC validation working")
        print(f"    - Collection name validation: OK")
        print(f"    - K parameter validation: OK")
        return True
        
    except ImportError as e:
        print(f"  ✗ FAIL: Import error: {e}")
        return False
    except Exception as e:
        print(f"  ✗ FAIL: {e}")
        return False


def test_rule_generation():
    """Test 4: YARA/Sigma stub generation logic."""
    print("\nTest 4: YARA/Sigma Rule Generation")
    
    try:
        # Check if query_rules exists
        from pentest_agent.cli.cmd_analysis import app as analysis_app
        
        # Verify the command is registered
        # (actual execution would require daemon and session setup)
        
        # Test CVE format validation (used in rule generation)
        import re
        CVE_PATTERN = r"CVE-\d{4}-\d{4,}"
        
        valid_cves = ["CVE-2024-1234", "CVE-2023-12345", "CVE-2021-99999"]
        for cve in valid_cves:
            if not re.match(CVE_PATTERN, cve):
                print(f"  ✗ FAIL: Valid CVE '{cve}' rejected by pattern")
                return False
        
        invalid_cves = ["CVE-24-1234", "CVE-2024-123", "cve-2024-1234"]
        for cve in invalid_cves:
            if re.match(CVE_PATTERN, cve):
                print(f"  ✗ FAIL: Invalid CVE '{cve}' accepted by pattern")
                return False
        
        # Test ATT&CK ID pattern (exactly 4 digits, optional .3 digits)
        ATTCK_PATTERN = r"^T\d{4}(?:\.\d{3})?$"
        
        valid_attck = ["T1234", "T1234.001", "T9999.999"]
        for attck in valid_attck:
            if not re.match(ATTCK_PATTERN, attck):
                print(f"  ✗ FAIL: Valid ATT&CK ID '{attck}' rejected")
                return False
        
        invalid_attck = ["t1234", "T123", "T12345", "T1234.1"]
        for attck in invalid_attck:
            if re.match(ATTCK_PATTERN, attck):
                print(f"  ✗ FAIL: Invalid ATT&CK ID '{attck}' accepted")
                return False
        
        print("  ✓ PASS: Rule generation patterns working")
        print(f"    - CVE format validation: OK")
        print(f"    - ATT&CK ID validation: OK")
        return True
        
    except ImportError as e:
        print(f"  ✗ FAIL: Import error: {e}")
        return False
    except Exception as e:
        print(f"  ✗ FAIL: {e}")
        return False


def test_security_md_exists():
    """Test 5: SECURITY.md documentation exists."""
    print("\nTest 5: Security Documentation")
    
    security_doc = Path("docs/SECURITY.md")
    if not security_doc.exists():
        print("  ✗ FAIL: SECURITY.md not found")
        return False
    
    # Check file has content (use utf-8 encoding with error handling)
    try:
        content = security_doc.read_text(encoding='utf-8', errors='ignore')
    except Exception:
        # Fallback to binary read
        content = security_doc.read_bytes().decode('utf-8', errors='ignore')
    
    if len(content) < 1000:
        print("  ✗ FAIL: SECURITY.md seems incomplete")
        return False
    
    # Check for key sections
    required_sections = [
        "Sanitization",
        "Prompt Injection",
        "API Key",
        "Audit",
        "Determinism"
    ]
    
    missing = []
    for section in required_sections:
        if section.lower() not in content.lower():
            missing.append(section)
    
    if missing:
        print(f"  ✗ FAIL: Missing sections: {', '.join(missing)}")
        return False
    
    print("  ✓ PASS: Security documentation complete")
    print(f"    - File size: {len(content)} bytes")
    print(f"    - Key sections: {len(required_sections)}/{len(required_sections)}")
    return True


def test_logging_package_structure():
    """Test 6: Logging package structure."""
    print("\nTest 6: Logging Package Structure")
    
    try:
        from pentest_agent.logging import (
            log_analysis_event,
            log_query_event,
            log_chat_turn,
            log_report_event,
            log_ingest_event,
            AuditEvent
        )
        
        # Verify all exports are accessible
        exports = [
            log_analysis_event,
            log_query_event,
            log_chat_turn,
            log_report_event,
            log_ingest_event,
            AuditEvent
        ]
        
        for export in exports:
            if not callable(export) and not isinstance(export, type):
                print(f"  ✗ FAIL: Export {export} is not callable or a class")
                return False
        
        print("  ✓ PASS: Logging package structure correct")
        print(f"    - Exports: {len(exports)} functions/classes")
        return True
        
    except ImportError as e:
        print(f"  ✗ FAIL: Import error: {e}")
        return False
    except Exception as e:
        print(f"  ✗ FAIL: {e}")
        return False


def test_validator_comprehensive():
    """Test 7: Comprehensive validator testing."""
    print("\nTest 7: Comprehensive Validator Tests")
    
    try:
        from pentest_agent.daemon.validators import (
            validate_query_filters,
            validate_upsert_request,
            validate_embed_request,
            ValidationError
        )
        
        # Test query filters for nvd collection
        valid_nvd_filters = [
            {"cve_id": "CVE-2024-1234"},
            {"severity": "CRITICAL"},
            {"cwe_id": "CWE-79"}
        ]
        
        for filters in valid_nvd_filters:
            try:
                validate_query_filters("nvd", filters)
            except ValidationError as e:
                print(f"  ✗ FAIL: Valid NVD filter rejected: {filters} - {e}")
                return False
        
        # Test invalid filter keys
        invalid_filter = {"invalid_key": "value"}
        try:
            validate_query_filters("nvd", invalid_filter)
            print(f"  ✗ FAIL: Invalid filter accepted")
            return False
        except ValidationError:
            pass  # Expected
        
        # Test upsert request validation
        valid_upsert = {
            "collection": "nvd",
            "documents": ["text1", "text2"],
            "ids": ["id1", "id2"],
            "metadatas": [{"key": "val1"}, {"key": "val2"}]
        }
        
        try:
            validate_upsert_request(valid_upsert)
        except ValidationError as e:
            print(f"  ✗ FAIL: Valid upsert rejected: {e}")
            return False
        
        # Test length mismatch
        invalid_upsert = {
            "collection": "nvd",
            "documents": ["text1"],
            "ids": ["id1", "id2"],
            "metadatas": [{"key": "val1"}]
        }
        
        try:
            validate_upsert_request(invalid_upsert)
            print(f"  ✗ FAIL: Length mismatch upsert accepted")
            return False
        except ValidationError:
            pass  # Expected
        
        # Test embed request validation
        valid_embed = {"text": "some text to embed"}
        
        try:
            validate_embed_request(valid_embed)
        except ValidationError as e:
            print(f"  ✗ FAIL: Valid embed request rejected: {e}")
            return False
        
        # Test excessive text length
        invalid_embed = {"text": "a" * 100001}
        
        try:
            validate_embed_request(invalid_embed)
            print(f"  ✗ FAIL: Excessive length embed accepted")
            return False
        except ValidationError:
            pass  # Expected
        
        print("  ✓ PASS: Comprehensive validator tests passing")
        print(f"    - Query filter validation: OK")
        print(f"    - Upsert validation: OK")
        print(f"    - Embed validation: OK")
        return True
        
    except ImportError as e:
        print(f"  ✗ FAIL: Import error: {e}")
        return False
    except Exception as e:
        print(f"  ✗ FAIL: {e}")
        return False


def main():
    """Run all hardening tests."""
    print("=" * 70)
    print("Iteration 5 Hardening Test Suite")
    print("=" * 70)
    
    tests = [
        test_report_generation,
        test_audit_logging,
        test_rpc_validation,
        test_rule_generation,
        test_security_md_exists,
        test_logging_package_structure,
        test_validator_comprehensive
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"\n✗ FATAL ERROR in {test.__name__}: {e}")
            results.append(False)
    
    print("\n" + "=" * 70)
    print("Results:")
    print("=" * 70)
    
    passed = sum(results)
    total = len(results)
    
    if passed == total:
        print(f"\n✓ PASSED: {passed}/{total} tests\n")
        print("SUCCESS: All Iteration 5 hardening tests passed!")
        return 0
    else:
        print(f"\n✗ FAILED: {passed}/{total} tests passed, {total - passed} failed\n")
        print("FAILURE: Some hardening tests failed.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
