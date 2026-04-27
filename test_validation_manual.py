#!/usr/bin/env python3
"""Manual test for RPC input validation."""

from pathlib import Path
import sys

# Add parent dir to path
sys.path.insert(0, str(Path(__file__).parent))

from pentest_agent.daemon.validators import (
    validate_collection_name,
    validate_query_filters,
    validate_k_parameter,
    validate_query_request,
    validate_upsert_request,
    validate_embed_request,
    ValidationError,
)


def test_validation():
    """Test RPC input validation."""
    print("=" * 60)
    print("Testing RPC Input Validation")
    print("=" * 60)
    
    tests_passed = 0
    tests_failed = 0
    
    # Test 1: validate_collection_name() with valid inputs
    print("\n--- Test 1: validate_collection_name() - Valid ---")
    try:
        for collection in ["nvd", "attck", "runbooks"]:
            validate_collection_name(collection)
            print(f"  ✓ '{collection}' is valid")
        tests_passed += 1
    except Exception as e:
        print(f"  ❌ Unexpected error: {e}")
        tests_failed += 1
    
    # Test 2: validate_collection_name() with invalid inputs
    print("\n--- Test 2: validate_collection_name() - Invalid ---")
    invalid_collections = ["invalid", "nvd; DROP TABLE", 123, None, ""]
    for invalid in invalid_collections:
        try:
            validate_collection_name(invalid)
            print(f"  ❌ Should have rejected: {invalid}")
            tests_failed += 1
        except ValidationError as e:
            print(f"  ✓ Correctly rejected '{invalid}': {e}")
            tests_passed += 1
        except Exception as e:
            print(f"  ❌ Unexpected error for '{invalid}': {e}")
            tests_failed += 1
    
    # Test 3: validate_query_filters() with valid filters
    print("\n--- Test 3: validate_query_filters() - Valid ---")
    valid_filters = [
        ("nvd", {"cve_id": "CVE-2024-1234"}),
        ("nvd", {"severity": "HIGH"}),
        ("attck", {"technique_id": "T1059"}),
        ("attck", {"technique_id": "T1059.001"}),
        ("attck", {"tactic": "execution"}),
        ("attck", {"platform": "windows"}),
        ("runbooks", {"platform": "linux"}),
    ]
    for collection, filters in valid_filters:
        try:
            validate_query_filters(collection, filters)
            print(f"  ✓ {collection}: {filters}")
            tests_passed += 1
        except Exception as e:
            print(f"  ❌ Unexpected rejection: {e}")
            tests_failed += 1
    
    # Test 4: validate_query_filters() with invalid filters
    print("\n--- Test 4: validate_query_filters() - Invalid ---")
    invalid_filters = [
        ("nvd", {"invalid_key": "value"}, "unknown key"),
        ("nvd", {"cve_id": "invalid-format"}, "invalid CVE format"),
        ("nvd", {"cve_id": "CVE-999-1"}, "invalid CVE year"),
        ("attck", {"technique_id": "X1234"}, "invalid technique ID"),
        ("attck", {"technique_id": "T12"}, "technique ID too short"),
        ("attck", {"tactic": "invalid-tactic"}, "invalid tactic"),
        ("attck", {"platform": "invalid-platform"}, "invalid platform"),
        ("nvd", "not-a-dict", "not a dict"),
    ]
    for collection, filters, reason in invalid_filters:
        try:
            validate_query_filters(collection, filters)
            print(f"  ❌ Should have rejected ({reason}): {filters}")
            tests_failed += 1
        except ValidationError as e:
            print(f"  ✓ Correctly rejected ({reason})")
            tests_passed += 1
        except Exception as e:
            print(f"  ❌ Unexpected error ({reason}): {e}")
            tests_failed += 1
    
    # Test 5: validate_k_parameter() with valid values
    print("\n--- Test 5: validate_k_parameter() - Valid ---")
    valid_k_values = [1, 5, 10, 50, 100, 500, 1000]
    for k in valid_k_values:
        try:
            result = validate_k_parameter(k)
            if result == k:
                print(f"  ✓ k={k} is valid")
                tests_passed += 1
            else:
                print(f"  ❌ k={k} returned unexpected value: {result}")
                tests_failed += 1
        except Exception as e:
            print(f"  ❌ Unexpected rejection: k={k}: {e}")
            tests_failed += 1
    
    # Test 6: validate_k_parameter() with invalid values
    print("\n--- Test 6: validate_k_parameter() - Invalid ---")
    invalid_k_values = [
        (0, "zero"),
        (-1, "negative"),
        (1001, "exceeds limit"),
        (10000, "way too large"),
        ("10", "string not int"),
        (10.5, "float not int"),
    ]
    for k, reason in invalid_k_values:
        try:
            validate_k_parameter(k)
            print(f"  ❌ Should have rejected ({reason}): k={k}")
            tests_failed += 1
        except ValidationError as e:
            print(f"  ✓ Correctly rejected k={k} ({reason})")
            tests_passed += 1
        except Exception as e:
            print(f"  ❌ Unexpected error for k={k}: {e}")
            tests_failed += 1
    
    # Test 7: validate_query_request() with valid requests
    print("\n--- Test 7: validate_query_request() - Valid ---")
    valid_requests = [
        {
            "collection": "nvd",
            "query": "SQL injection vulnerability",
            "k": 5,
            "filters": {"severity": "HIGH"},
        },
        {
            "collection": "attck",
            "query": "command execution",
            "k": 10,
            "filters": {},
        },
    ]
    for req in valid_requests:
        try:
            result = validate_query_request(req)
            print(f"  ✓ Valid request: {req['collection']}")
            tests_passed += 1
        except Exception as e:
            print(f"  ❌ Unexpected rejection: {e}")
            tests_failed += 1
    
    # Test 8: validate_query_request() with invalid requests
    print("\n--- Test 8: validate_query_request() - Invalid ---")
    invalid_requests = [
        ({}, "missing all fields"),
        ({"collection": "nvd"}, "missing query and k"),
        ({"collection": "nvd", "query": "test"}, "missing k"),
        ({"collection": "invalid", "query": "test", "k": 5}, "invalid collection"),
        ({"collection": "nvd", "query": "x" * 10001, "k": 5}, "query too long"),
        ({"collection": "nvd", "query": "test", "k": 0}, "invalid k"),
    ]
    for req, reason in invalid_requests:
        try:
            validate_query_request(req)
            print(f"  ❌ Should have rejected ({reason})")
            tests_failed += 1
        except ValidationError as e:
            print(f"  ✓ Correctly rejected ({reason})")
            tests_passed += 1
        except Exception as e:
            print(f"  ❌ Unexpected error ({reason}): {e}")
            tests_failed += 1
    
    # Test 9: validate_upsert_request() with valid requests
    print("\n--- Test 9: validate_upsert_request() - Valid ---")
    valid_upsert = {
        "collection": "nvd",
        "documents": ["doc1", "doc2"],
        "ids": ["id1", "id2"],
        "metadatas": [{"a": 1}, {"b": 2}],
    }
    try:
        result = validate_upsert_request(valid_upsert)
        print("  ✓ Valid upsert request")
        tests_passed += 1
    except Exception as e:
        print(f"  ❌ Unexpected rejection: {e}")
        tests_failed += 1
    
    # Test 10: validate_upsert_request() with invalid requests
    print("\n--- Test 10: validate_upsert_request() - Invalid ---")
    invalid_upserts = [
        (
            {"collection": "nvd", "documents": ["d1"], "ids": ["i1"]},
            "missing metadatas",
        ),
        (
            {
                "collection": "nvd",
                "documents": ["d1", "d2"],
                "ids": ["i1"],
                "metadatas": [{}],
            },
            "mismatched array lengths",
        ),
        (
            {
                "collection": "nvd",
                "documents": ["d"] * 1001,
                "ids": ["i"] * 1001,
                "metadatas": [{}] * 1001,
            },
            "batch size exceeds limit",
        ),
    ]
    for req, reason in invalid_upserts:
        try:
            validate_upsert_request(req)
            print(f"  ❌ Should have rejected ({reason})")
            tests_failed += 1
        except ValidationError as e:
            print(f"  ✓ Correctly rejected ({reason})")
            tests_passed += 1
        except Exception as e:
            print(f"  ❌ Unexpected error ({reason}): {e}")
            tests_failed += 1
    
    # Test 11: validate_embed_request() with valid requests
    print("\n--- Test 11: validate_embed_request() - Valid ---")
    try:
        validate_embed_request({"text": "test text"})
        print("  ✓ Valid embed request")
        tests_passed += 1
    except Exception as e:
        print(f"  ❌ Unexpected rejection: {e}")
        tests_failed += 1
    
    # Test 12: validate_embed_request() with invalid requests
    print("\n--- Test 12: validate_embed_request() - Invalid ---")
    invalid_embeds = [
        ({}, "missing text field"),
        ({"text": 123}, "text not string"),
        ({"text": "x" * 100001}, "text too long"),
    ]
    for req, reason in invalid_embeds:
        try:
            validate_embed_request(req)
            print(f"  ❌ Should have rejected ({reason})")
            tests_failed += 1
        except ValidationError as e:
            print(f"  ✓ Correctly rejected ({reason})")
            tests_passed += 1
        except Exception as e:
            print(f"  ❌ Unexpected error ({reason}): {e}")
            tests_failed += 1
    
    # Summary
    total = tests_passed + tests_failed
    print("\n" + "=" * 60)
    print(f"Test Results: {tests_passed}/{total} passed")
    if tests_failed == 0:
        print("✅ ALL VALIDATION TESTS PASSED")
    else:
        print(f"❌ {tests_failed} tests failed")
    print("=" * 60)
    
    return tests_failed == 0


if __name__ == "__main__":
    success = test_validation()
    sys.exit(0 if success else 1)
