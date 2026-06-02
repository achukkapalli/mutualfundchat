import json
import os

class DocumentChunker:
    def __init__(self):
        pass

    def load_documents(self, file_path):
        """Loads the scraped documents JSON file."""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Documents file not found: {file_path}")
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def chunk_documents(self, documents):
        """
        Maps pre-segmented documents to individual chunks.
        Splits Fund Management sections into Bio/Tenure and Other Schemes managed
        to avoid token bloat and cross-contamination, while keeping Overview and 
        Exit Load sections 1-to-1.
        """
        chunks = []
        for doc in documents:
            fund_name = doc["fund_name"]
            section = doc["section"]
            content = doc["content"]
            source_url = doc["source_url"]
            last_updated = doc["last_updated"]
            
            # Base metadata
            metadata = {
                "fund_name": fund_name,
                "section": section,
                "source_url": source_url,
                "last_updated": last_updated
            }
            
            if section.startswith("Fund Management") and ". Other Schemes Managed by " in content:
                # Split the chunk
                parts = content.split(". Other Schemes Managed by ", 1)
                bio_text = parts[0].strip()
                other_schemes_list = parts[1].strip()
                
                # Extract manager name from the section (format: "Fund Management - Manager Name")
                manager_name = section.replace("Fund Management - ", "").strip()
                
                # 1. Bio Chunk
                bio_metadata = metadata.copy()
                bio_metadata["section"] = f"Fund Management - {manager_name} - Bio"
                chunks.append({
                    "content": bio_text,
                    "metadata": bio_metadata
                })
                
                # 2. Other Schemes Chunk
                other_metadata = metadata.copy()
                other_metadata["section"] = f"Fund Management - {manager_name} - Other Schemes"
                other_text = f"Mutual Fund Scheme: {fund_name}. Fund Manager: {manager_name}. Other Schemes Managed by {manager_name}: {other_schemes_list}"
                chunks.append({
                    "content": other_text,
                    "metadata": other_metadata
                })
            else:
                # 1-to-1 mapping for other sections
                chunks.append({
                    "content": content,
                    "metadata": metadata
                })
        return chunks
