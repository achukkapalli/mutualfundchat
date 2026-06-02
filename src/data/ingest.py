import os
import json
import hashlib
from src.data.scraper import GrowwScraper
from src.data.chunker import DocumentChunker
from src.data.vector_store import VectorStoreManager

class DataIngestionPipeline:
    def __init__(self, raw_docs_path="data/raw/scraped_documents.json", manifest_path="data/ingest_manifest.json"):
        self.raw_docs_path = raw_docs_path
        self.manifest_path = manifest_path
        self.scraper = GrowwScraper()
        self.chunker = DocumentChunker()
        self.vector_store = VectorStoreManager()

    def get_content_hash(self, text):
        """Generates MD5 hash of text content."""
        return hashlib.md5(text.encode("utf-8")).hexdigest()

    def load_manifest(self):
        """Loads the ingestion manifest to check for existing chunk hashes."""
        if os.path.exists(self.manifest_path):
            try:
                with open(self.manifest_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def save_manifest(self, manifest):
        """Saves the updated manifest file."""
        with open(self.manifest_path, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2, ensure_ascii=False)

    def run(self, force_reindex=False):
        # 1. Run scraping to fetch fresh data if needed
        print("Starting scraping step...")
        self.scraper.run()
        
        # 2. Load scraped documents
        print("\nLoading scraped documents...")
        documents = self.chunker.load_documents(self.raw_docs_path)
        
        # 3. Create chunks
        chunks = self.chunker.chunk_documents(documents)
        print(f"Generated {len(chunks)} semantic chunks.")
        
        # 4. Check manifest for incremental changes
        manifest = self.load_manifest()
        new_or_modified_chunks = []
        updated_manifest = {}

        # Suffix-free ID generation helper to match vector_store.py
        import re
        for c in chunks:
            fund = c["metadata"]["fund_name"]
            sec = c["metadata"]["section"]
            chunk_id = re.sub(r'[^a-zA-Z0-9]', '_', f"{fund}_{sec}").lower()
            
            content = c["content"]
            current_hash = self.get_content_hash(content)
            
            # Keep track in the new manifest
            updated_manifest[chunk_id] = current_hash
            
            if force_reindex or manifest.get(chunk_id) != current_hash:
                print(f"  [Change Detected] Chunk '{chunk_id}' is new or modified.")
                new_or_modified_chunks.append(c)
            else:
                # No change, skip embedding generation
                pass
                
        if new_or_modified_chunks:
            print(f"\nAdding/updating {len(new_or_modified_chunks)} chunks in the vector database...")
            self.vector_store.add_documents(new_or_modified_chunks)
        else:
            print("\nNo database updates needed. All chunks are up-to-date (hashing matched).")

        # 5. Save the updated manifest
        self.save_manifest(updated_manifest)
        print("Ingestion pipeline run completed successfully.")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Mutual Funds Ingestion Pipeline")
    parser.add_argument("--force", action="store_true", help="Force reindexing of all documents")
    args = parser.parse_args()
    
    pipeline = DataIngestionPipeline()
    pipeline.run(force_reindex=args.force)
