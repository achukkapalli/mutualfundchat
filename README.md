# Mutual Fund FAQ Assistant (Facts-Only Q&A)

A Retrieval-Augmented Generation (RAG) assistant designed to answer objective, factual questions about specific mutual fund schemes using Groww as the product reference context. 

The chatbot is strictly bounded to offer **facts-only** answers, strictly refusing to provide investment advice, speculative returns predictions, or comparison opinions. It adheres to compliance and safety guardrails, including PII exposure prevention, sentence-length constraints, and automatic regulatory link citation.

---

## System Architecture

The assistant follows a modular RAG pipeline divided into offline ingestion and online query serving:

```text
Offline Ingestion Pipeline:
[Groww Source URLs] ➔ [Scraper Engine] ➔ [Document Parser] 
                       ➔ [Manager-Specific Sub-Chunker] ➔ [SentenceTransformer] 
                       ➔ [Local ChromaDB + Manifest Hash]

Online Query Serving Pipeline:
[User Query] ➔ [PII Redactor] ➔ [Intent Classifier (Regex + Groq Fallback)]
                 ├─► [ADVISORY] ➔ [Refusal Handler] ➔ [Polite Refusal + SEBI/AMFI URL]
                 └─► [FACTUAL]  ➔ [Fund Entity Filter] ➔ [Hybrid Retrieval (Vector + BM25)]
                                  ➔ [Groq LLM Service (llama-3.1-8b-instant)]
                                  ➔ [Output Validator (Sentence Cap, Link Checker, Footer)] ➔ [UI]
```

### Key Technical Design Elements:
1. **Manager-Specific Sub-Chunking**: Splits long manager accordions (e.g. managers handling 40+ other schemes) into a separate "Bio & Tenure" chunk and "Other Schemes Managed" chunk. This prevents query cross-contamination and token bloat.
2. **Intent Classification & Routing**: Performs a fast regex keyword match for advisory queries, falling back to a structured Groq LLM query router when ambiguous. Captures scheme names to apply metadata database filtering.
3. **Hybrid Retrieval**: Interleaves dense Vector Search (ChromaDB + `all-MiniLM-L6-v2`) and sparse Keyword Search (`rank-bm25` BM25Okapi) for high-accuracy matches on terminology (e.g. exit loads, AUM).
4. **Post-Processing Guardrails**: Detects and redacts PII (PAN, Aadhaar, phone, email, OTPs). Caps the text length to $\le 3$ sentences, ensuring citation links are preserved during truncation. Appends the data freshness timestamp footer automatically.

---

## Repository Structure

```text
mutual-funds-chatbot/
├── config/                 # Ingestion source URLs config
│   └── sources.json
├── data/
│   ├── raw/                # Parsed raw document JSON snapshots
│   ├── vectordb/           # ChromaDB persistent directory
│   └── ingest_manifest.json# Manifest tracking document hashes for incremental indexing
├── docs/                   # Product and roadmap documentation
│   ├── architecture.md
│   ├── implementationPlan.md
│   └── problemStatement.md
├── src/
│   ├── app/                # Streamlit user interface dashboard
│   │   └── main.py
│   ├── data/               # Ingestion, scraping, chunking, and db scripts
│   │   ├── chunker.py
│   │   ├── ingest.py
│   │   ├── scraper.py
│   │   └── vector_store.py
│   └── services/           # Intent classification, LLM wrap, and guardrails
│       ├── intent.py
│       ├── refusal.py
│       ├── retrieval.py
│       ├── llm.py
│       └── validator.py
├── tests/                  # Test suites for unit and integration verification
│       ├── test_scraper.py
│       ├── test_vector_store.py
│       ├── test_routing.py
│       └── test_validator.py
├── requirements.txt        # Virtual environment dependencies
└── .env                    # Local environment variables containing GROQ_API_KEY
```

---

## Setup & Running Guide

### 1. Environment Setup
Initialize the virtual environment and install the required dependencies:
```powershell
# Create virtual environment
python -m venv .venv

# Activate virtual environment
# On Windows Powershell:
.\.venv\Scripts\Activate.ps1
# On Linux/macOS:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment Variables
Create a `.env` file in the root directory and insert your Groq API Key:
```text
GROQ_API_KEY="your-groq-api-key-here"
```

### 3. Run Ingestion Pipeline
To crawl the target URLs, chunk their content, embed them locally, and insert them into the ChromaDB vector database:
```powershell
python -m src.data.ingest
```
*Note: This utilizes incremental hashing. Re-running will check MD5 hashes and only update modified or new chunks unless the `--force` flag is supplied.*

### 4. Run the Verification Tests
Confirm all services (scraping, database retrieval, intent classification routing, LLM generation format constraints, and safety validators) are functioning correctly:
```powershell
python -m pytest tests/test_scraper.py
python tests/test_vector_store.py
python tests/test_routing.py
python tests/test_validator.py
```

### 5. Launch the Web Chat Interface
Run the Streamlit application:
```powershell
streamlit run src/app/main.py
```
This will launch a local server and open the web dashboard in your browser.

---

## System Limitations
1. **Source Site Structure Changes**: The ingestion scraper relies on custom CSS classes (e.g. `fundDetails_fundDetailsContainer`) pre-rendered by Groww. If Groww updates their CSS class naming schemes, the BS4 scraper may fail to parse data fields, triggering Playwright to fetch raw strings as fallback.
2. **Context Size**: Due to the $\le 3$ sentences constraint and the target models context size, retrieval returns the top 3 chunks (vector + BM25) to provide a rich context window while remaining highly focused.

---

## Scaling to Extra URLs

The architecture is built for horizontal scale:
1. **Configuration-Driven Sources**: To ingest additional mutual funds, simply edit [config/sources.json](file:///c:/Users/aishw/Documents/Mutual%20funds%20chatbot/config/sources.json) to add new URL entries. No code modification is needed.
2. **Fund Mapping Expansion**: To support automated routing filtering for new funds, add relevant fund segment/abbreviation keywords to the `self.fund_mappings` dictionary in [intent.py](file:///c:/Users/aishw/Documents/Mutual%20funds%20chatbot/src/services/intent.py).
3. **Pluggable Parsers**: For documents other than Groww (e.g. direct AMC factsheets, PDF documents), a new parser class conforming to the scraper schema can be easily written and loaded dynamically.
