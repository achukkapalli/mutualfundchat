import os
import sys
import re

# Ensure project root is in python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.services.intent import IntentClassifier
from src.services.retrieval import RetrievalService
from src.services.llm import LLMService

def count_sentences(text):
    """Simple helper to count sentences based on punctuation."""
    # Strip links to avoid punctuation in URLs from counting as sentence boundaries
    stripped = re.sub(r'\[.*?\]\(.*?\)', 'LINK', text)
    sentences = re.split(r'(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?)\s', stripped)
    return len([s for s in sentences if s.strip()])

def test_llm_generation():
    classifier = IntentClassifier()
    retrieval_service = RetrievalService()
    llm_service = LLMService()

    queries = [
        "Who is the fund manager of HDFC Mid Cap Fund and what is their tenure?",
        "What is the exit load for HDFC Defence Fund?",
        "What is the latest NAV and AUM of HDFC Small Cap Fund?",
        "Who manages HDFC Mid-Cap Opportunities Fund and what are their qualifications?"
    ]

    print("\n================ STARTING LLM GENERATION TESTS ================")

    for query in queries:
        print(f"\nQuery: '{query}'")
        
        # 1. Classify
        cat, reason = classifier.classify_intent(query)
        assert cat == "FACTUAL", f"Expected query to be FACTUAL, got {cat}"
        
        # 2. Retrieve
        fund_filter = classifier.detect_fund_filter(query)
        filter_dict = {"fund_name": fund_filter} if fund_filter else None
        chunks = retrieval_service.retrieve(query, filter_dict=filter_dict, n_results=5)
        
        print(f"  Retrieved {len(chunks)} chunks.")
        
        # 3. Generate
        response = llm_service.generate_response(query, chunks)
        print(f"  Response:\n\"\"\"\n{response}\n\"\"\"")
        
        # 4. Assert sentence count <= 3
        s_count = count_sentences(response)
        print(f"  Sentence Count: {s_count}")
        assert s_count <= 3, f"Response exceeds 3 sentences limit (got {s_count} sentences)"
        
        # 5. Assert exactly one markdown link
        links = re.findall(r'\[([^\]]+)\]\(([^)]+)\)', response)
        print(f"  Links found: {links}")
        assert len(links) == 1, f"Expected exactly one markdown link citation, found {len(links)}"
        
        # Verify the citation points to a valid Groww URL
        cited_url = links[0][1]
        assert cited_url.startswith("https://groww.in/mutual-funds/"), f"Link URL '{cited_url}' does not point to a valid Groww mutual fund page"
        
        print("  Status: PASSED")

    print("\n================ ALL LLM GENERATION TESTS PASSED! ================")

if __name__ == "__main__":
    try:
        test_llm_generation()
    except AssertionError as e:
        print(f"\nAssertion Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\nUnexpected Error: {e}")
        sys.exit(1)
