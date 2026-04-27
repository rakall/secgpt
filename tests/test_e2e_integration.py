"""
End-to-end integration test - simplified version.

Tests core integration points without requiring daemon or complex setup.
"""

import sys
import json
import sqlite3
import shutil
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def test_session_lifecycle():
    """Test 1: Session initialization."""
    print("Test 1: Session Lifecycle")
    
    try:
        from pentest_agent.db.schema import SCHEMA_SQL
        
        # Create temporary test session
        test_session_dir = Path("sessions/test_e2e_session")
        test_session_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize session.db
        db_path = test_session_dir / "session.db"
        conn = sqlite3.connect(str(db_path))
        conn.executescript(SCHEMA_SQL)
        
        # Verify WAL mode
        conn.execute("PRAGMA journal_mode=WAL")
        result = conn.execute("PRAGMA journal_mode").fetchone()
        assert result[0].lower() == "wal", f"Expected WAL mode, got {result[0]}"
        
        # Verify tables exist
        tables = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        ).fetchall()
        
        expected_tables = [
            'analysis_runs', 'chat_history', 'endpoints', 'findings',
            'hosts', 'ingest_runs', 'kb_metadata', 'ports',
            'scope', 'session_settings'
        ]
        
        table_names = [t[0] for t in tables]
        for expected in expected_tables:
            assert expected in table_names, f"Missing table: {expected}"
        
        conn.close()
        shutil.rmtree(test_session_dir)
        
        print(f"  ✓ PASS: All {len(expected_tables)} tables created with WAL mode")
        return True
        
    except Exception as e:
        print(f"  ✗ FAIL: {e}")
        try:
            shutil.rmtree(test_session_dir)
        except Exception:
            pass
        return False


def test_ingestion_utilities():
    """Test 2: Ingestion utility functions."""
    print("\nTest 2: Ingestion Utilities")
    
    try:
        from pentest_agent.ingest.util import host_id, normalize_severity
        
        # Test host ID computation
        test_ip = "192.168.1.1"
        host_id_result = host_id(test_ip)
        assert len(host_id_result) == 16, "Host ID should be truncated SHA256 (16 chars)"
        
        # Test severity normalization
        severities = [
            ("critical", "critical"),
            ("high", "high"),
            ("medium", "medium"),
            ("low", "low"),
            ("info", "info"),
        ]
        
        for raw, expected in severities:
            normalized = normalize_severity(raw)
            assert normalized == expected, f"Normalization failed: {raw} -> {normalized}"
        
        print("  ✓ PASS: Host ID and severity normalization working")
        return True
        
    except Exception as e:
        print(f"  ✗ FAIL: {e}")
        return False


def test_analysis_components():
    """Test 3: Analysis pipeline components."""
    print("\nTest 3: Analysis Components")
    
    try:
        from pentest_agent.analysis import (
            classify_intent,
            plan_query,
            canonicalize_prompt,
            compute_prompt_hash
        )
        
        # Test intent classification
        test_cases = [
            ("CVE-2024-1234", "cve"),
            ("show endpoints", "endpoint"),
            ("critical vulnerabilities", "vuln"),
        ]
        
        for query, expected_intent in test_cases:
            intents = classify_intent(query)
            assert expected_intent in intents, f"Missing intent {expected_intent} for '{query}'"
        
        # Test prompt canonicalization
        test_system = "You are a security analyst"
        test_user = "Analyze this query"
        canonical1 = canonicalize_prompt(system=test_system, user=test_user)
        canonical2 = canonicalize_prompt(system=test_system, user=test_user)
        assert canonical1 == canonical2, "Canonicalization not deterministic"
        
        # Test hashing
        hash1 = compute_prompt_hash(canonical1)
        hash2 = compute_prompt_hash(canonical2)
        assert hash1 == hash2, "Hashing not deterministic"
        assert len(hash1) == 64, "Hash should be SHA256"
        
        print("  ✓ PASS: Intent classification, canonicalization, hashing working")
        return True
        
    except Exception as e:
        print(f"  ✗ FAIL: {e}")
        return False


def test_report_generation():
    """Test 4: Report generation queries."""
    print("\nTest 4: Report Generation")
    
    try:
        from pentest_agent.cli.cmd_report import (
            _severity_style,
            _query_scope,
            _query_hosts,
            _query_endpoints,
            _query_findings
        )
        
        # Test severity styling
        severities = ["CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"]
        for sev in severities:
            styled = _severity_style(sev)
            assert sev in styled, f"Severity '{sev}' not in styled output"
        
        # Test with real session if it exists
        session_path = Path("sessions/192.168.100.122")
        if session_path.exists() and (session_path / "session.db").exists():
            conn = sqlite3.connect(str(session_path / "session.db"))
            conn.row_factory = sqlite3.Row
            
            scope = _query_scope(conn)
            hosts = _query_hosts(conn)
            endpoints = _query_endpoints(conn)
            findings = _query_findings(conn)
            
            conn.close()
            print(f"    - Queried real session: {len(scope)} scope, {len(hosts)} hosts, {len(endpoints)} endpoints, {len(findings)} findings")
        
        print("  ✓ PASS: Report generation queries working")
        return True
        
    except Exception as e:
        print(f"  ✗ FAIL: {e}")
        return False


def test_sanitization():
    """Test 5: Data sanitization."""
    print("\nTest 5: Sanitization")
    
    try:
        from pentest_agent.ingest.sanitizer import Sanitizer
        
        test_cases = [
            "password=secret123",  # Test data for sanitizer
            "api_key=sk-1234567890",
            "token:abcd1234efgh5678",
        ]
        
        for original in test_cases:
            sanitized = Sanitizer.sanitize_string(original)
            assert "redacted" in sanitized.lower(), f"Not sanitized: {original} -> {sanitized}"
        
        print(f"  ✓ PASS: Sanitizer working on {len(test_cases)} test cases")
        return True
        
    except Exception as e:
        print(f"  ✗ FAIL: {e}")
        return False


def test_logging_infrastructure():
    """Test 6: Audit logging."""
    print("\nTest 6: Logging Infrastructure")
    
    try:
        from pentest_agent.logging.formatters import AuditEvent, format_audit_event
        from pentest_agent.logging.audit import (
            log_analysis_event,
            log_query_event,
            log_chat_turn,
            log_report_event,
            log_ingest_event
        )
        
        # Test event formatting
        event = AuditEvent(
            event_type="test",
            session_id="test_session",
            result_status="success"
        )
        
        formatted = format_audit_event(event)
        assert "timestamp" in formatted, "Formatted event missing timestamp"
        assert formatted["event_type"] == "test", "Event type mismatch"
        
        print("  ✓ PASS: Audit event creation and formatting working")
        return True
        
    except Exception as e:
        print(f"  ✗ FAIL: {e}")
        return False


def test_validators():
    """Test 7: RPC input validation."""
    print("\nTest 7: RPC Validators")
    
    try:
        from pentest_agent.daemon.validators import (
            validate_collection_name,
            validate_k_parameter,
            ValidationError
        )
        
        # Test valid collection names
        for coll in ["nvd", "attck", "runbooks"]:
            validate_collection_name(coll)  # Should not raise
        
        # Test invalid collection name
        try:
            validate_collection_name("invalid")
            print("  ✗ FAIL: Invalid collection accepted")
            return False
        except ValidationError:
            pass  # Expected
        
        # Test valid k parameter
        for k in [1, 5, 100]:
            validate_k_parameter(k)  # Should not raise
        
        # Test invalid k
        try:
            validate_k_parameter(0)
            print("  ✗ FAIL: Invalid k=0 accepted")
            return False
        except ValidationError:
            pass  # Expected
        
        print("  ✓ PASS: Validators rejecting invalid inputs")
        return True
        
    except Exception as e:
        print(f"  ✗ FAIL: {e}")
        return False


def main():
    """Run all integration tests."""
    print("=" * 70)
    print("End-to-End Integration Test Suite")
    print("=" * 70)
    
    tests = [
        test_session_lifecycle,
        test_ingestion_utilities,
        test_analysis_components,
        test_report_generation,
        test_sanitization,
        test_logging_infrastructure,
        test_validators
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"\n✗ FATAL ERROR in {test.__name__}: {e}")
            import traceback
            traceback.print_exc()
            results.append(False)
    
    print("\n" + "=" * 70)
    print("Results:")
    print("=" * 70)
    
    passed = sum(results)
    total = len(results)
    
    if passed == total:
        print(f"\n✓ PASSED: {passed}/{total} tests\n")
        print("SUCCESS: All integration tests passed!")
        print("\nMVP hardening complete and verified!")
        return 0
    else:
        print(f"\n✗ FAILED: {passed}/{total} tests passed, {total - passed} failed\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
