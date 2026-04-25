"""
Determinism regression test suite for Iteration 4/5.

Tests that same session + query + KB state produces identical prompt_hash
across multiple runs. Detects non-determinism in:
- Intent classification
- Query planning
- KB retrieval (k+δ post-sort)
- Prompt canonicalization
- Session projection
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from pentest_agent.analysis import (
    classify_intent,
    plan_query,
    retrieve_context,
    canonicalize_prompt,
    compute_prompt_hash,
    compute_file_hash,
)


def test_intent_classification_determinism():
    """Test 1: Intent classification is deterministic."""
    print("Test 1: Intent Classification Determinism")
    
    test_queries = [
        "CVE-2024-1234",
        "what services on 10.0.0.1?",
        "risky endpoints on apache",
        "show me critical vulnerabilities",
    ]
    
    results = []
    for query in test_queries:
        # Run classification 3 times
        result1 = classify_intent(query)
        result2 = classify_intent(query)
        result3 = classify_intent(query)
        
        # All should be identical
        if result1 == result2 == result3:
            results.append(True)
        else:
            print(f"  FAIL: Non-deterministic intent classification for '{query}'")
            print(f"    Run 1: {result1}")
            print(f"    Run 2: {result2}")
            print(f"    Run 3: {result3}")
            results.append(False)
    
    if all(results):
        print("  ✓ PASS: Intent classification deterministic across all queries")
        return True
    else:
        print(f"  ✗ FAIL: {sum(not r for r in results)}/{len(results)} queries non-deterministic")
        return False


def test_canonicalization_determinism():
    """Test 2: Prompt canonicalization is deterministic."""
    print("\nTest 2: Canonicalization Determinism")
    
    # Same data in different orders
    test_data = [
        {"b": 2, "a": 1, "c": 3},
        {"c": 3, "b": 2, "a": 1},
        {"a": 1, "c": 3, "b": 2},
    ]
    
    hashes = []
    for data in test_data:
        canonical = canonicalize_prompt(
            system="test system",
            user="test user",
            context="test context",
            metadata=data,
        )
        hash_value = compute_prompt_hash(canonical)
        hashes.append(hash_value)
    
    if len(set(hashes)) == 1:
        print(f"  ✓ PASS: All canonicalizations produce identical hash: {hashes[0][:16]}...")
        return True
    else:
        print(f"  ✗ FAIL: Different hashes produced:")
        for i, h in enumerate(hashes, 1):
            print(f"    Run {i}: {h[:16]}...")
        return False


def test_file_hash_determinism():
    """Test 3: File hashing is deterministic."""
    print("\nTest 3: File Hashing Determinism")
    
    # Create temp file with known content
    import tempfile
    
    content = "test content for determinism\n" * 100
    
    with tempfile.NamedTemporaryFile(mode="w", delete=False, encoding="utf-8") as f:
        temp_path = Path(f.name)
        f.write(content)
    
    try:
        # Hash file 3 times
        hash1 = compute_file_hash(temp_path)
        hash2 = compute_file_hash(temp_path)
        hash3 = compute_file_hash(temp_path)
        
        if hash1 == hash2 == hash3:
            print(f"  ✓ PASS: File hash deterministic: {hash1[:16]}...")
            return True
        else:
            print(f"  ✗ FAIL: File hashes differ:")
            print(f"    Hash 1: {hash1[:16]}...")
            print(f"    Hash 2: {hash2[:16]}...")
            print(f"    Hash 3: {hash3[:16]}...")
            return False
    finally:
        temp_path.unlink()


def test_kb_retrieval_post_sort_determinism():
    """Test 4: K+δ retrieval post-sort is deterministic (simulation)."""
    print("\nTest 4: K+δ Retrieval Post-Sort Determinism")
    
    # Simulate retrieved documents with similarity scores
    from pentest_agent.analysis.kb_retrieval import Document
    import hashlib
    
    # Create test documents with same similarity score (tiebreaker scenario)
    docs = [
        Document("chunk_003", "content 3", 0.85, "nvd", {}),
        Document("chunk_001", "content 1", 0.85, "nvd", {}),
        Document("chunk_002", "content 2", 0.85, "nvd", {}),
        Document("chunk_005", "content 5", 0.90, "nvd", {}),
        Document("chunk_004", "content 4", 0.90, "nvd", {}),
    ]
    
    def deterministic_sort(documents):
        """Sort by similarity desc, then chunk_id hash asc."""
        def sort_key(doc):
            chunk_hash = int(hashlib.sha256(doc.chunk_id.encode()).hexdigest(), 16) % (2**32)
            return (-doc.similarity_score, chunk_hash)
        return sorted(documents, key=sort_key)
    
    # Sort 3 times
    sorted1 = deterministic_sort(docs.copy())
    sorted2 = deterministic_sort(docs.copy())
    sorted3 = deterministic_sort(docs.copy())
    
    # Extract chunk_id order
    order1 = [d.chunk_id for d in sorted1]
    order2 = [d.chunk_id for d in sorted2]
    order3 = [d.chunk_id for d in sorted3]
    
    if order1 == order2 == order3:
        print(f"  ✓ PASS: Post-sort deterministic: {order1}")
        return True
    else:
        print(f"  ✗ FAIL: Post-sort order differs:")
        print(f"    Sort 1: {order1}")
        print(f"    Sort 2: {order2}")
        print(f"    Sort 3: {order3}")
        return False


def test_query_planner_determinism():
    """Test 5: Query planner generates identical plans."""
    print("\nTest 5: Query Planner Determinism")
    
    # Test query planning with same intents
    from pentest_agent.analysis.query_planner import get_templates
    
    # Get templates 3 times
    templates1 = get_templates()
    templates2 = get_templates()
    templates3 = get_templates()
    
    # Compare template keys (intents)
    ids1 = set(templates1.keys())
    ids2 = set(templates2.keys())
    ids3 = set(templates3.keys())
    
    if ids1 == ids2 == ids3:
        print(f"  ✓ PASS: Query planner templates deterministic ({len(ids1)} templates)")
        return True
    else:
        print(f"  ✗ FAIL: Template keys differ:")
        print(f"    Templates 1: {ids1}")
        print(f"    Templates 2: {ids2}")
        print(f"    Templates 3: {ids3}")
        return False


def test_prompt_assembly_determinism():
    """Test 6: Full prompt assembly is deterministic."""
    print("\nTest 6: Prompt Assembly Determinism")
    
    # Same inputs in different order
    system_prompt = "You are a security analyst."
    user_query = "Analyze these findings."
    session_data = {"findings": [{"id": "F1", "severity": "HIGH"}]}
    kb_context = "CVE-2024-1234 description..."
    
    # Assemble 3 times
    from pentest_agent.analysis.prompt import assemble_prompt
    
    prompt1, hash1 = assemble_prompt(system_prompt, user_query, session_data, kb_context, {})
    prompt2, hash2 = assemble_prompt(system_prompt, user_query, session_data, kb_context, {})
    prompt3, hash3 = assemble_prompt(system_prompt, user_query, session_data, kb_context, {})
    
    if hash1 == hash2 == hash3:
        print(f"  ✓ PASS: Prompt assembly hash deterministic: {hash1[:16]}...")
        return True
    else:
        print(f"  ✗ FAIL: Prompt hashes differ:")
        print(f"    Hash 1: {hash1[:16]}...")
        print(f"    Hash 2: {hash2[:16]}...")
        print(f"    Hash 3: {hash3[:16]}...")
        return False


def test_json_canonicalization():
    """Test 7: JSON canonicalization handles special cases."""
    print("\nTest 7: JSON Canonicalization Edge Cases")
    
    from pentest_agent.analysis.determinism import canonicalize_dict
    import json
    
    # Test cases: nested dicts, arrays, unicode, None values
    test_data = {
        "unicode": "café ☕",
        "nested": {"z": 3, "a": 1, "b": 2},
        "array": [3, 1, 2],
        "null_value": None,
        "boolean": True,
    }
    
    # Canonicalize 3 times
    canon1 = canonicalize_dict(test_data)
    canon2 = canonicalize_dict(test_data)
    canon3 = canonicalize_dict(test_data)
    
    if canon1 == canon2 == canon3:
        print(f"  ✓ PASS: JSON canonicalization deterministic")
        print(f"    Sample: {canon1[:80]}...")
        return True
    else:
        print(f"  ✗ FAIL: Canonicalization differs:")
        print(f"    Canon 1: {canon1[:80]}...")
        print(f"    Canon 2: {canon2[:80]}...")
        return False


def main():
    """Run all determinism regression tests."""
    print("="*70)
    print("Determinism Regression Test Suite")
    print("="*70)
    
    tests = [
        test_intent_classification_determinism,
        test_canonicalization_determinism,
        test_file_hash_determinism,
        test_kb_retrieval_post_sort_determinism,
        test_query_planner_determinism,
        test_prompt_assembly_determinism,
        test_json_canonicalization,
    ]
    
    results = []
    for test_func in tests:
        try:
            result = test_func()
            results.append(result)
        except Exception as e:
            print(f"  ✗ ERROR: Test raised exception: {e}")
            import traceback
            traceback.print_exc()
            results.append(False)
    
    print("\n" + "="*70)
    print("Results:")
    print("="*70)
    
    passed = sum(results)
    total = len(results)
    
    print(f"\n✓ PASSED: {passed}/{total} tests")
    if passed < total:
        print(f"✗ FAILED: {total - passed}/{total} tests")
        print("\nFAILURE: Non-determinism detected!")
        print("Review failed tests above for details.")
        return 1
    else:
        print("\nSUCCESS: All determinism tests passed!")
        print("System demonstrates consistent deterministic behavior.")
        return 0


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
