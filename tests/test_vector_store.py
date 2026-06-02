import os
import sys

# Ensure project root is in python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.data.vector_store import VectorStoreManager

def test_retrieval():
    manager = VectorStoreManager()
    
    print("\n--- Test 1: Querying for HDFC Mid Cap Fund Manager ---")
    query_1 = "Who is the manager of HDFC Mid Cap Fund and what is their tenure?"
    results_1 = manager.query(query_1, n_results=3, filter_dict={"fund_name": "HDFC Mid Cap Fund Direct Growth"})
    
    print(f"Query: {query_1}")
    found_bio = False
    for doc, metadata in zip(results_1['documents'][0], results_1['metadatas'][0]):
        print(f"\n[Source: {metadata['fund_name']} - {metadata['section']}]")
        print(f"Content: {doc}")
        if "Chirag Setalvad" in doc and "Bio" in metadata['section'] and "HDFC Mid Cap Fund" in metadata['fund_name']:
            found_bio = True
            
    assert found_bio, "Failed to retrieve Chirag Setalvad's bio for HDFC Mid Cap Fund query"
    print(">>> Test 1 Passed!")

    print("\n--- Test 2: Querying for HDFC Defence Fund Exit Load ---")
    query_2 = "What is the exit load for HDFC Defence Fund?"
    results_2 = manager.query(query_2, n_results=2, filter_dict={"fund_name": "HDFC Defence Fund Direct Growth"})
    
    print(f"Query: {query_2}")
    found_exit_load = False
    for doc, metadata in zip(results_2['documents'][0], results_2['metadatas'][0]):
        print(f"\n[Source: {metadata['fund_name']} - {metadata['section']}]")
        print(f"Content: {doc}")
        if "Exit Load" in metadata['section'] and "HDFC Defence Fund" in metadata['fund_name']:
            found_exit_load = True
            
    assert found_exit_load, "Failed to retrieve Exit Load for HDFC Defence Fund"
    print(">>> Test 2 Passed!")

    print("\n--- Test 3: Querying for Other Schemes managed by Chirag Setalvad ---")
    query_3 = "What are the other schemes managed by Chirag Setalvad?"
    results_3 = manager.query(query_3, n_results=2, filter_dict={"fund_name": "HDFC Mid Cap Fund Direct Growth"})
    
    print(f"Query: {query_3}")
    found_other_schemes = False
    for doc, metadata in zip(results_3['documents'][0], results_3['metadatas'][0]):
        print(f"\n[Source: {metadata['fund_name']} - {metadata['section']}]")
        print(f"Content: {doc}")
        if "Other Schemes" in metadata['section'] and "Chirag Setalvad" in doc:
            found_other_schemes = True
            
    assert found_other_schemes, "Failed to retrieve other schemes managed by Chirag Setalvad"
    print(">>> Test 3 Passed!")

    print("\nAll vector store retrieval tests passed successfully!")

if __name__ == "__main__":
    try:
        test_retrieval()
    except AssertionError as e:
        print(f"\nAssertion Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\nUnexpected Error: {e}")
        sys.exit(1)
