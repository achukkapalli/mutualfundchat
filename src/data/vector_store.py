import os
import re
import chromadb
from sentence_transformers import SentenceTransformer

class VectorStoreManager:
    def __init__(self, db_dir="data/vectordb", collection_name="mutual_funds_faq"):
        self.db_dir = db_dir
        self.collection_name = collection_name
        os.makedirs(self.db_dir, exist_ok=True)
        
        # Initialize persistent ChromaDB client
        self.client = chromadb.PersistentClient(path=self.db_dir)
        
        # Load local embedding model (runs fully on CPU/GPU offline)
        print("Loading SentenceTransformer model ('all-MiniLM-L6-v2')...")
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        print("Model loaded successfully.")

    def get_or_create_collection(self):
        """Fetches the existing collection or creates a new one."""
        return self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"}  # Use cosine similarity
        )

    def generate_embeddings(self, texts):
        """Generates list of embeddings (list of lists of floats) for a list of texts."""
        if not texts:
            return []
        # sentence-transformers returns numpy arrays, convert to list for ChromaDB compatibility
        embeddings = self.embedding_model.encode(texts, show_progress_bar=False)
        return embeddings.tolist()

    def add_documents(self, chunks):
        """
        Inserts document chunks into ChromaDB.
        Each chunk is a dict: {'content': str, 'metadata': dict}
        """
        if not chunks:
            return
            
        collection = self.get_or_create_collection()
        
        contents = [c["content"] for c in chunks]
        metadatas = [c["metadata"] for c in chunks]
        
        # Generate unique IDs based on fund name and section name
        ids = []
        for c in chunks:
            fund = c["metadata"]["fund_name"]
            sec = c["metadata"]["section"]
            # Sanitize key string for ID
            sanitized = re.sub(r'[^a-zA-Z0-9]', '_', f"{fund}_{sec}").lower()
            ids.append(sanitized)

        # Generate embeddings locally
        print(f"Generating embeddings for {len(contents)} chunks...")
        embeddings = self.generate_embeddings(contents)
        
        # Insert/upsert into collection
        collection.upsert(
            documents=contents,
            embeddings=embeddings,
            metadatas=metadatas,
            ids=ids
        )
        print(f"Successfully loaded {len(contents)} chunks into collection '{self.collection_name}'")

    def query(self, query_text, n_results=3, filter_dict=None):
        """
        Queries the vector database for similar chunks.
        Allows metadata filtering (e.g. filter by fund_name).
        """
        collection = self.get_or_create_collection()
        
        # Generate embedding for the search query
        query_embedding = self.generate_embeddings([query_text])[0]
        
        # Run search
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=filter_dict
        )
        return results
