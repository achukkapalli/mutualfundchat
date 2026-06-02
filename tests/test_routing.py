import os
import sys

# Ensure project root is in python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.services.intent import IntentClassifier
from src.services.refusal import RefusalHandler
from src.services.retrieval import RetrievalService

def test_intent_and_routing():
    classifier = IntentClassifier()
    refusal_handler = RefusalHandler()
    retrieval_service = RetrievalService()

    # List of queries to test classification and routing
    test_cases = [
        {
            "query": "What is the expense ratio of HDFC Small Cap Fund?",
            "expected_category": "FACTUAL",
            "check_retrieval": True,
            "expected_fund": "HDFC Small Cap Fund Direct Growth"
        },
        {
            "query": "Should I invest in HDFC Small Cap?",
            "expected_category": "ADVISORY",
            "check_retrieval": False,
            "expected_link": "sebi"
        },
        {
            "query": "Who is the fund manager of HDFC Mid Cap?",
            "expected_category": "FACTUAL",
            "check_retrieval": True,
            "expected_fund": "HDFC Mid Cap Fund Direct Growth"
        },
        {
            "query": "Which is better: HDFC Mid Cap or HDFC Defence?",
            "expected_category": "ADVISORY",
            "check_retrieval": False,
            "expected_link": "amfi"
        },
        {
            "query": "What is the exit load for HDFC Defence?",
            "expected_category": "FACTUAL",
            "check_retrieval": True,
            "expected_fund": "HDFC Defence Fund Direct Growth"
        }
    ]

    print("\n================ STARTING ROUTING TESTS ================")
    
    for tc in test_cases:
        query = tc["query"]
        expected_cat = tc["expected_category"]
        
        print(f"\nQuery: '{query}'")
        
        # 1. Classify
        cat, reason = classifier.classify_intent(query)
        print(f"  Classification: {cat} (Reason: {reason})")
        
        assert cat == expected_cat, f"Classification mismatch. Expected: {expected_cat}, Got: {cat}"
        
        # 2. Route
        if cat == "ADVISORY":
            refusal_payload = refusal_handler.get_refusal_response(query, reason)
            print("  Routed to: Refusal Handler")
            print(f"  Refusal Answer: {refusal_payload['answer']}")
            
            assert refusal_payload["is_refusal"] is True, "Expected refusal payload flag to be True"
            
            # Check for correct link association
            expected_link_domain = "investor.sebi.gov.in" if tc["expected_link"] == "sebi" else "www.amfiindia.com"
            assert expected_link_domain in refusal_payload["answer"], f"Expected domain '{expected_link_domain}' in refusal message"
            
        else:
            print("  Routed to: Context Retrieval Engine")
            # Entity matching for metadata filtering
            fund_filter = classifier.detect_fund_filter(query)
            print(f"  Detected Fund Filter: {fund_filter}")
            
            assert fund_filter == tc["expected_fund"], f"Expected fund filter '{tc['expected_fund']}', Got: '{fund_filter}'"
            
            # Retrieve
            filter_dict = {"fund_name": fund_filter} if fund_filter else None
            chunks = retrieval_service.retrieve(query, filter_dict=filter_dict, n_results=3)
            
            print(f"  Retrieved {len(chunks)} hybrid chunks:")
            for i, chunk in enumerate(chunks, 1):
                print(f"    Chunk {i}: [{chunk['metadata']['fund_name']} - {chunk['metadata']['section']}] (Score Type: {chunk['score_type']})")
                print(f"      Content snippet: {chunk['content'][:120]}...")
            
            assert len(chunks) > 0, "Failed to retrieve any context chunks for factual query"
            # Assert all retrieved chunks belong to the filtered fund
            for chunk in chunks:
                assert chunk["metadata"]["fund_name"] == fund_filter, f"Retrieved chunk belongs to wrong fund: {chunk['metadata']['fund_name']}"
                
        print("  Status: PASSED")

    print("\n================ ALL ROUTING TESTS PASSED! ================")

if __name__ == "__main__":
    try:
        test_intent_and_routing()
    except AssertionError as e:
        print(f"\nAssertion Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\nUnexpected Error: {e}")
        sys.exit(1)
