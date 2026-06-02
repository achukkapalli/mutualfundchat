import os
import json
import pytest
from src.data.scraper import GrowwScraper

def test_sources_config_exists():
    assert os.path.exists("config/sources.json"), "config/sources.json must exist"

def test_scraper_load_sources():
    scraper = GrowwScraper()
    sources = scraper.load_sources()
    assert len(sources) == 5, "Scraper should load exactly 5 sources"
    for s in sources:
        assert "name" in s
        assert "url" in s
        assert "category" in s

def test_scraped_documents_exist():
    assert os.path.exists("data/raw/scraped_documents.json"), "scraped_documents.json must be generated"

def test_standardized_documents_format():
    with open("data/raw/scraped_documents.json", "r", encoding="utf-8") as f:
        docs = json.load(f)
        
    assert len(docs) > 0, "Should have generated standardized documents"
    
    required_keys = ["fund_name", "section", "content", "source_url", "last_updated"]
    
    for doc in docs:
        for key in required_keys:
            assert key in doc, f"Standardized document missing key: {key}"
            assert doc[key], f"Value for key '{key}' should not be empty"
            
        # Ensure no HTML tags remain in the contents
        content = doc["content"]
        assert "<" not in content and ">" not in content, f"HTML residue found in document content: {content}"
        
        # Verify source is a groww URL
        assert doc["source_url"].startswith("https://groww.in/mutual-funds/"), f"Invalid source URL: {doc['source_url']}"

def test_scraped_raw_snapshots_exist():
    scraper = GrowwScraper()
    sources = scraper.load_sources()
    
    for s in sources:
        # Sanitize name to match file format
        import re
        sanitized_name = re.sub(r'[^a-zA-Z0-9]', '_', s["name"]).lower()
        snapshot_path = os.path.join("data/raw", f"{sanitized_name}_raw.json")
        
        assert os.path.exists(snapshot_path), f"Snapshot should exist: {snapshot_path}"
        
        with open(snapshot_path, "r", encoding="utf-8") as f:
            raw_data = json.load(f)
            
        assert raw_data["fund_name"] == s["name"] or raw_data["fund_name"] != "Unknown Fund"
        assert raw_data["nav"] != "N/A", f"NAV should not be N/A for {s['name']}"
        assert raw_data["expense_ratio"] != "N/A", f"Expense ratio should not be N/A for {s['name']}"
        assert raw_data["benchmark_index"] != "N/A", f"Benchmark should not be N/A for {s['name']}"
        assert len(raw_data["managers"]) > 0, f"Should have found managers for {s['name']}"
        
        # Verify manager details
        for mgr in raw_data["managers"]:
            assert "name" in mgr and mgr["name"], "Manager name must not be empty"
            assert "tenure" in mgr, "Manager tenure must be present"
            assert "education" in mgr, "Manager education must be present"
            assert "experience" in mgr, "Manager experience must be present"
