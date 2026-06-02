# Implementation Plan: Mutual Fund FAQ Assistant (Facts-Only Q&A)

This document provides a structured, phasewise implementation plan for building the RAG-based Mutual Fund FAQ Assistant. The roadmap is designed to guide development from environment setup to a fully validated, scalable product.

---

## Roadmap Overview

```mermaid
gantt
    title Project Roadmap: Mutual Fund FAQ Assistant
    dateFormat  YYYY-MM-DD
    section Core Infrastructure
    Phase 0: Environment & Setup         :active, p0, 2026-06-01, 2d
    Phase 1: Ingestion & Scraping        : p1, after p0, 4d
    section RAG Pipeline
    Phase 2: Chunking & Vector DB        : p2, after p1, 3d
    Phase 3: Intent & Retrieval Routing   : p3, after p2, 3d
    Phase 4: LLM Generation (Gemini)     : p4, after p3, 3d
    section Compliance & UI
    Phase 5: Output Guardrails & Safety  : p5, after p4, 3d
    Phase 6: User Interface & Launch      : p6, after p5, 3d
```

---

## Phase 0: Project Setup & Environment Initialization
*Establish the foundational environment, folder structures, and dependencies.*

### Tasks
- [ ] Initialize python virtual environment (`.venv`) using Python 3.10+.
- [ ] Create core project directory structure:
  ```text
  mutual-funds-chatbot/
  ├── config/                 # Configuration files (URLs, LLM params)
  ├── docs/                   # Documentation (Architecture, Plan, etc.)
  ├── src/
  │   ├── data/               # Ingestion, parsing, database scripts
  │   ├── services/           # Intent, LLM generation, guardrails
  │   ├── app/                # Streamlit/UI and application entrypoint
  │   └── utils/              # Helper utilities
  ├── tests/                  # Unit and integration tests
  └── requirements.txt
  ```
- [ ] Install core dependencies:
  *   Scraping/Parsing: `beautifulsoup4`, `requests`, `playwright`
  *   Vector DB & NLP: `chromadb` (or `faiss-cpu`), `sentence-transformers`
  *   LLM Orchestration: `groq` (Groq SDK), `langchain` / `llamaindex` (optional/lightweight)
  *   Interface & API: `streamlit`, `fastapi`, `uvicorn`
  *   Testing: `pytest`
- [ ] Set up environment variable management (`python-dotenv`) for the Groq API Key.
- [ ] Create `config/sources.json` to store the initial 5 target Groww URLs.

### Verification Gate
*   Run a smoke test script to verify environment variables load correctly and connection to the Groq API is successful.

---

## Phase 1: Ingestion & Scraping Engine (Scalable)
*Build the engine to fetch, clean, and extract raw data from the 5 mutual fund URLs.*

### Tasks
- [ ] Write a robust scraping utility in `src/data/scraper.py`. 
  > [!NOTE]
  > Since Groww may rely on client-side JS rendering, implement a fallback mechanism using `Playwright` if `requests` + `BeautifulSoup` fails to capture the dynamic data tables.
- [ ] Implement a **Data Cleaning & Sanitization** pipeline:
  *   **Strip Boilerplate**: Remove script tags, stylesheets, ad frames, navigation headers, sidebar links, and footer clutter.
  *   **Normalize Tables**: Convert key-value details (e.g., Expense Ratio, Exit Load) and tables (e.g., Fund Managers list) into clean, structured Markdown formats (e.g., Markdown tables or key-value text lines) so the LLM can easily parse and reason over them.
  *   **Clean Whitespace**: Remove excessive newlines, tab characters, double spaces, and non-breaking spaces (`\xa0`).
- [ ] Develop custom HTML parsers to target specific Groww page elements containing:
  *   Fund Name, Scheme Type (Mid, Large, Small, ETF, Sectoral)
  *   Expense Ratio, Exit Load, Minimum SIP/Lumpsum amount
  *   Riskometer rating and Benchmark Index
  *   Fund Management Team (Name, active tenure, and schemes managed)
- [ ] Standardize the parsed output into a common schema structure:
  ```json
  {
    "fund_name": "HDFC Small Cap Fund Direct Growth",
    "section": "Fund Management",
    "content": "Managed by Chirag Setalvad since 2014...",
    "source_url": "https://groww.in/mutual-funds/hdfc-small-cap-fund-direct-growth",
    "last_updated": "2026-05-31"
  }
  ```
- [ ] Implement local storage for parsed JSON files (`data/raw/`) to avoid unnecessary re-scraping.

### Verification Gate
*   Run unit tests under `tests/test_scraper.py` checking if the scraper successfully pulls, cleans, and correctly parses all five designated HDFC funds without HTML residue.

---

## Phase 2: Chunking & Vector Store Setup
*Format raw data into search-optimized chunks and load them into a vector database.*

### Tasks
- [ ] Implement **Manager-Specific Sub-Chunking** in `src/data/chunker.py`:
  * Map Overview and Exit Load sections 1-to-1 to preserve complete context.
  * For Fund Management sections, split them into two distinct chunks:
    1. **Bio & Tenure Chunk**: Contains the manager's name, active tenure, education, and professional experience.
    2. **Other Schemes Managed Chunk**: Contains the manager's name and the list of other schemes they manage.
  * This prevents token bloat and retrieval cross-contamination from managers who manage up to 46 other schemes (e.g. Dhruv Muchhal).
- [ ] Integrate local embeddings generation using a lightweight sentence-transformer model (e.g., `all-MiniLM-L6-v2`) or Gemini's official embeddings.
- [ ] Initialize the local Vector Database (`chromadb` or `faiss`) in `src/data/vector_store.py`.
- [ ] Write the ingestion script (`src/data/ingest.py`) to chunk documents, embed them, insert them into the DB along with metadata (`source_url`, `fund_name`, etc.), and handle content changes using hashing (incremental updates).

### Verification Gate
*   Run indexing script and verify database collection creation. Run a mock query search to ensure vectors retrieve matching context based on cosine similarity.

---

## Phase 3: Intent Classification & Retrieval Routing
*Develop the query classifier to separate factual questions from advisory queries, and implement context retrieval.*

### Tasks
- [ ] Implement the `IntentClassifier` in `src/services/intent.py`. 
  *   Use a hybrid approach: fast Regex/Keyword check + small LLM validation check.
  *   Catch advisory patterns (e.g., *"should I buy"*, *"which is better"*, *"returns prediction"*).
- [ ] Implement the `RefusalHandler` in `src/services/refusal.py` to output:
  *   Polite refusal clarifying the facts-only nature.
  *   A link to SEBI's Investor Education website or AMFI.
- [ ] Implement hybrid retrieval: Vector Search + BM25 keyword matching to locate the correct context chunks.

### Verification Gate
*   Run classifier test cases. Assert that *"What is the expense ratio?"* goes to RAG, while *"Should I invest in HDFC Small Cap?"* immediately returns the refusal payload.

---

## Phase 4: LLM Generation (Groq Integration)
*Integrate the LLM generation service under strict prompt constraints.*

### Tasks
- [ ] Implement the `LLMService` in `src/services/llm.py` to connect with Groq (e.g., using `llama3-8b-8192` or `llama3-70b-8192`).
- [ ] Design and test the **System Prompt** instructing the LLM to:
  *   Rely *only* on the provided context.
  *   Avoid assumptions, opinions, or extrapolations.
  *   Enforce a maximum of 3 sentences.
  *   Include exactly one markdown hyperlink citation pointing to the source URL.
- [ ] Create the prompt constructor that interpolates user query, retrieved context, and system instructions.

### Verification Gate
*   Execute CLI-based end-to-end runs for various factual queries. Confirm the LLM generates accurate, 1-3 sentence answers citing the source URL.

---

## Phase 5: Output Guardrails & Post-Processing
*Enforce compliance, security (PII), and text length validation before displaying responses.*

### Tasks
- [ ] Build the `OutputValidator` in `src/services/validator.py`.
- [ ] Implement PII detection/redaction (identifying PAN, Aadhaar, phone numbers, email addresses, and OTPs in the prompt inputs and LLM output).
- [ ] Implement the Sentence Count Validator. If the model exceeds 3 sentences:
  *   Automatically truncate or trigger a low-temperature regeneration.
- [ ] Implement Link Validation to ensure the generated link matches one of the ingested source URLs.
- [ ] Programmatically append the required footer: `Last updated from sources: <date>`.

### Verification Gate
*   Run edge-case test suites (e.g., injecting a fake PAN card number into the query, or forcing a long generation) and verify redacting and truncation logic.

---

## Phase 6: User Interface (UI) & Launch
*Wrap the system in a minimal, compliant web interface.*

### Tasks
- [ ] Create a Streamlit-based web dashboard (`src/app/main.py`).
- [ ] Implement the UI components:
  *   Header with project title: **Mutual Fund FAQ Assistant**.
  *   Prominent sticky disclaimer: ⚠️ **“Facts-only. No investment advice.”**
  *   Welcome greeting and brief instruction.
  *   Three clickable example questions:
      1. *"Who manages HDFC Small Cap Fund and what is their tenure?"*
      2. *"What is the exit load for HDFC Defence Fund?"*
      3. *"Should I invest in HDFC Large Cap Fund?"*
  *   Interactive chat interface showing conversation bubbles, source citation links, and the source update date.
- [ ] Add configuration settings to let administrators trigger a re-scrape/re-index of the URLs.
- [ ] Write a comprehensive [README.md](file:///c:/Users/aishw/Documents/Mutual%20funds%20chatbot/README.md) file detailing setup instructions, architecture, limitations, and how to scale to extra URLs.

### Verification Gate
*   Run the Streamlit application locally, perform manual QA on the three example questions, and verify that the layout displays beautifully and is fully responsive.

---

## Phase 7: Automated Scheduling & Production Setup
*Configure automated background execution of the ingestion pipeline to keep source data fresh.*

### Tasks
- [ ] Configure system-level automation:
  *   **Linux/macOS**: Write a `crontab` file running `python -m src.data.ingest` daily at midnight.
  *   **Windows**: Set up a basic task in Windows Task Scheduler invoking `.venv/Scripts/python.exe` with arguments `-m src.data.ingest` running daily.
- [ ] Implement an alternative in-process scheduler using `APScheduler` or python's `threading` library to execute background refreshes inside the application lifecycle.
- [ ] Verify scheduler logging to ensure errors are captured and emailed or saved in a log file.

### Verification Gate
*   Trigger the scheduler script manually or wait for the scheduled time, then assert that the log output confirms successful crawling, indexing, and no duplicate vectors were created.

