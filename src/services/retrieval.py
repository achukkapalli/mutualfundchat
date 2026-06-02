import os
import re
from rank_bm25 import BM25Okapi
from src.data.vector_store import VectorStoreManager

class RetrievalService:
    def __init__(self, vector_store_manager=None):
        self.vector_store = vector_store_manager or VectorStoreManager()

    def _tokenize(self, text):
        """Simplistic tokenizer for BM25 ranking (lowercase and word split)."""
        return [word for word in re.findall(r"\w+", text.lower()) if len(word) > 1]

    def retrieve(self, query_text, filter_dict=None, n_results=3):
        """
        Performs hybrid retrieval: Vector Search + BM25 keyword search.
        Deduplicates results and merges them to provide the best context.
        """
        # 1. Vector Search
        # ChromaDB query returns structure: {'documents': [[doc1, doc2, ...]], 'metadatas': [[meta1, meta2, ...]], 'ids': [[id1, id2, ...]]}
        vector_results = self.vector_store.query(query_text, n_results=n_results, filter_dict=filter_dict)
        
        vector_chunks = []
        if vector_results and 'documents' in vector_results and vector_results['documents']:
            docs = vector_results['documents'][0]
            metas = vector_results['metadatas'][0]
            ids = vector_results['ids'][0]
            for doc, meta, cid in zip(docs, metas, ids):
                vector_chunks.append({
                    "id": cid,
                    "content": doc,
                    "metadata": meta,
                    "score_type": "vector"
                })

        # 2. Fetch all candidates for BM25 from ChromaDB (with the same metadata filters)
        collection = self.vector_store.get_or_create_collection()
        all_candidates = collection.get(where=filter_dict)
        
        bm25_chunks = []
        if all_candidates and 'documents' in all_candidates and all_candidates['documents']:
            cand_docs = all_candidates['documents']
            cand_metas = all_candidates['metadatas']
            cand_ids = all_candidates['ids']
            
            # Tokenize corpus for BM25
            tokenized_corpus = [self._tokenize(doc) for doc in cand_docs]
            
            if tokenized_corpus and any(tokenized_corpus):
                bm25 = BM25Okapi(tokenized_corpus)
                tokenized_query = self._tokenize(query_text)
                
                # Get scores
                scores = bm25.get_scores(tokenized_query)
                
                # Zip and sort candidates by score
                ranked_candidates = sorted(
                    zip(cand_ids, cand_docs, cand_metas, scores),
                    key=lambda x: x[3],
                    reverse=True
                )
                
                # Take top candidates up to n_results
                for cid, doc, meta, score in ranked_candidates[:n_results]:
                    # Ignore candidates with zero keyword overlap to avoid noise
                    if score > 0.0:
                        bm25_chunks.append({
                            "id": cid,
                            "content": doc,
                            "metadata": meta,
                            "score_type": "bm25",
                            "score": score
                        })

        # 3. Interleaved Merging (Deduplicating by Chunk ID)
        seen_ids = set()
        hybrid_chunks = []
        
        max_len = max(len(vector_chunks), len(bm25_chunks))
        for i in range(max_len):
            # Add vector chunk at rank i
            if i < len(vector_chunks):
                vc = vector_chunks[i]
                if vc["id"] not in seen_ids:
                    seen_ids.add(vc["id"])
                    hybrid_chunks.append(vc)
                    
            # Add BM25 chunk at rank i
            if i < len(bm25_chunks):
                bc = bm25_chunks[i]
                if bc["id"] not in seen_ids:
                    seen_ids.add(bc["id"])
                    hybrid_chunks.append(bc)

        # Cap the final results list to n_results
        return hybrid_chunks[:n_results]
