# Streamlit Community Cloud Deployment Plan: Mutual Fund FAQ Assistant

This document outlines the step-by-step procedure to deploy the **Mutual Fund FAQ Assistant** (Facts-Only Q&A) on **Streamlit Community Cloud**.

---

## 1. Prerequisites
Before beginning the deployment, make sure you have:
*   A **GitHub** account.
*   A **Groq Cloud** account with an active API key (`GROQ_API_KEY`).
*   The project files pushed to a repository on GitHub (either public or private).

---

## 2. Repository Preparation & Git Best Practices

Ensure your GitHub repository structure aligns with the following structure:
```text
mutual-funds-chatbot/
├── .streamlit/             # (Optional) Streamlit configuration files
│   └── config.toml
├── config/
│   └── sources.json        # Ingested scheme URL configurations
├── data/
│   ├── raw/                # (Optional) Raw JSON data
│   └── vectordb/           # ChromaDB database files (MANDATORY TO COMMIT)
├── src/
│   ├── app/
│   │   └── main.py         # Application entrypoint
│   ├── data/               # Ingestion and chunking logic
│   ├── services/           # Intent, LLM, retrieval, validation logic
│   └── utils/              # Helper utilities (normalization, etc.)
├── requirements.txt        # Package dependencies
└── README.md
```

### Git Actions
1.  **Commit ChromaDB**: Commit the `data/vectordb/` folder to GitHub. This ensures the app boots up *instantly* with all 32 crawled scheme chunks ready, avoiding the need to run the slow scraping/ingestion script on container startup.
2.  **Gitignore Secrets**: Ensure your local `.env` file containing the `GROQ_API_KEY` is listed in your `.gitignore` file to prevent accidental public disclosure of your secrets.
    ```text
    # .gitignore
    .env
    __pycache__/
    .pytest_cache/
    .venv/
    ```

---

## 3. Step-by-Step Deployment on Streamlit Cloud

Streamlit Community Cloud is the easiest and most premium hosting option for Streamlit applications. Follow these steps:

### Step 1: Sign In & Connect GitHub
1.  Go to [Streamlit Share](https://share.streamlit.io/).
2.  Click **Sign in with GitHub** and authorize Streamlit to access your repositories.

### Step 2: Configure App Details
1.  On the Streamlit Workspace home page, click the **Create app** button in the top right corner.
2.  Fill in the deployment details:
    *   **Repository**: Select your mutual fund chatbot repository (e.g., `username/Mutual-funds-chatbot`).
    *   **Branch**: Select the default branch (usually `main` or `master`).
    *   **Main file path**: Enter `src/app/main.py`. This is critical as the entry point is located in the nested `src/app` folder.

### Step 3: Configure Secrets (Advanced Settings)
The application requires the Groq API key to perform intent classification and answer generation.
1.  Click **Advanced settings** at the bottom of the deployment page.
2.  Under the **Secrets** text area, paste the following key-value configuration:
    ```toml
    GROQ_API_KEY = "your-groq-api-key-here"
    ```
3.  Click **Save**.

### Step 4: Launch the App
1.  Click **Deploy!**
2.  Streamlit will spin up a secure container, install all packages listed in `requirements.txt`, load your ChromaDB embeddings offline, and launch the web server.
3.  Once completed, the app will be live at a URL like `https://<your-app-name>.streamlit.app/`.

---

## 4. Architectural Considerations & Container Behavior

### Ephemeral Storage vs. Git Database
*   **The Problem**: Streamlit Community Cloud runs in ephemeral Docker containers. Any changes written to the local filesystem (such as running the Scraper or manual ingestion updates via the UI) will be lost if the container shuts down or restarts.
*   **The Solution**: By committing the populated `data/vectordb/` folder directly to Git, the database is backed up and packaged alongside the app code, ensuring absolute data consistency across container lifecycles.
*   **Manual Refreshes**: The **"🔄 Refresh Data Now"** button in the sidebar will still function on-demand in the running container session, but any freshly scraped updates will expire when the container sleeps. To update the database permanently, run the pipeline locally and commit/push the new `data/vectordb` files.

---

## 5. Troubleshooting & FAQ

### Issue 1: "ModuleNotFoundError: No module named 'src'"
*   **Why**: Python is unable to find your source packages because of path resolutions in Streamlit.
*   **Fix**: The `src/app/main.py` entrypoint includes `sys.path.append(...)` lines to add the repository root to the syspath. Double-check that your main file contains:
    ```python
    sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    ```

### Issue 2: Build Failures or Timeout During Package Installations
*   **Why**: Large package builds (like `playwright` or heavy ML binaries) might exceed Streamlit Cloud's resource limits or cause setup delays.
*   **Fix**: Since our scraping pipeline is purely based on `requests` and `bs4` (Playwright is not invoked dynamically in the running service), you can safely remove `playwright` from `requirements.txt` before deploying to speed up build times.
