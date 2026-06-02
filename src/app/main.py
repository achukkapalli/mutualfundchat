import os
import sys
import streamlit as st

# Ensure project root is in python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.services.intent import IntentClassifier
from src.services.refusal import RefusalHandler
from src.services.retrieval import RetrievalService
from src.services.llm import LLMService
from src.services.validator import OutputValidator
from src.data.ingest import DataIngestionPipeline
from src.utils.normalization import normalize_query_fund_names

# Set page config
st.set_page_config(
    page_title="Mutual Fund FAQ Assistant",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for rich premium styling that adapts dynamically to Streamlit's Light/Dark themes
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&family=Plus+Jakarta+Sans:wght@300;400;600;700&display=swap');

    /* Adjust top padding of the main container and hide Streamlit's default header */
    [data-testid="stHeader"] {
        display: none;
    }
    .main .block-container {
        padding-top: 1.5rem !important;
        margin-top: 0px !important;
    }

    /* Global typography */
    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', sans-serif;
    }
    h1, h2, h3, h4, h5, h6 {
        font-family: 'Outfit', sans-serif;
        font-weight: 600;
        letter-spacing: -0.02em;
    }

    /* Premium Adaptive Header Card */
    .header-card {
        background: var(--secondary-background-color);
        border: 1px solid rgba(128, 128, 128, 0.15);
        border-radius: 16px;
        padding: 24px;
        margin-bottom: 20px;
        box-shadow: 0 4px 20px 0 rgba(0, 0, 0, 0.05);
    }
    .header-card h1 {
        color: var(--text-color) !important;
        margin: 0;
        font-size: 2.2rem;
    }
    .header-card p {
        color: var(--text-color) !important;
        opacity: 0.75;
        margin: 8px 0 0 0;
        font-size: 1.05rem;
    }

    /* Sidebar customization */
    [data-testid="stSidebar"] {
        border-right: 1px solid rgba(128, 128, 128, 0.15);
    }

    /* Clickable example buttons formatting */
    .stButton>button {
        text-align: left !important;
        justify-content: flex-start !important;
        border-radius: 10px !important;
        font-size: 0.9rem !important;
        padding: 10px 14px !important;
        transition: all 0.3s ease !important;
    }
    .stButton>button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 4px 12px rgba(99, 102, 241, 0.15) !important;
    }
</style>
""", unsafe_allow_html=True)

# Initialize Services in session state to cache across reruns
if "intent_classifier" not in st.session_state:
    st.session_state.intent_classifier = IntentClassifier()
if "refusal_handler" not in st.session_state:
    st.session_state.refusal_handler = RefusalHandler()
if "retrieval_service" not in st.session_state:
    st.session_state.retrieval_service = RetrievalService()
if "llm_service" not in st.session_state:
    st.session_state.llm_service = LLMService()
if "output_validator" not in st.session_state:
    st.session_state.output_validator = OutputValidator()

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Sidebar Content
with st.sidebar:
    st.markdown("### 📚 Knowledge Base")
    st.markdown("---")
    
    st.markdown("#### 🔍 Supported Funds")
    st.markdown("""
    * 📈 **HDFC Mid-Cap Opportunities**
    * 📊 **HDFC Top 100 (Large Cap)**
    * 📉 **HDFC Small Cap**
    * 🟡 **HDFC Gold ETF FoF**
    * 🛡️ **HDFC Defence Fund**
    """)
    
    # Push data utilities to the very bottom
    st.markdown("---")
    
    st.markdown("#### 🔄 Update Source Data")
    st.write("Fetch latest mutual fund details on-demand:")
    
    if st.button("🔄 Refresh Data Now", use_container_width=True):
        status_placeholder = st.empty()
        with status_placeholder.container():
            with st.spinner("Executing refresh..."):
                try:
                    pipeline = DataIngestionPipeline()
                    pipeline.run(force_reindex=True)
                    st.success("Data refresh completed successfully!")
                except Exception as e:
                    st.error(f"Error during refresh: {str(e)}")
                    
    st.markdown("---")
    st.markdown("<div style='font-size:0.75rem; opacity:0.6;'>Facts-Only Q&A Assistant v1.0.2<br>© 2026 Mutual Fund Assistant</div>", unsafe_allow_html=True)

# Main UI Header Card
st.markdown("""
<div class='header-card'>
    <h1>📈 Mutual Fund FAQ Assistant</h1>
    <p>Get objective, source-backed facts about HDFC Mutual Fund schemes. Speculative questions, returns predictions, and comparison advisories are strictly refused.</p>
</div>
""", unsafe_allow_html=True)

# Sticky Disclaimer Banner (Native Streamlit Warning for perfect theme-adaptation)
st.warning("⚠️ **DISCLAIMER: Facts-only mode active. No investment advice, comparison suggestions, or recommendations will be provided.**")

# Main page columns (Responsive for desktop, stacks on mobile)
col_chat, col_info = st.columns([7, 3])

# Process query helper function
def process_user_query(query_text):
    # 1. PII Redaction
    clean_query = st.session_state.output_validator.redact_pii(query_text)
    
    # 2. Normalize fund names
    clean_query = normalize_query_fund_names(clean_query)
    
    # 3. Intent Classification
    category, reason = st.session_state.intent_classifier.classify_intent(clean_query)
    
    if category == "ADVISORY":
        # Refusal Payload
        refusal_payload = st.session_state.refusal_handler.get_refusal_response(clean_query, reason)
        st.session_state.messages.append({
            "role": "assistant", 
            "content": refusal_payload["answer"],
            "is_refusal": True
        })
    else:
        # Factual RAG
        fund_filter = st.session_state.intent_classifier.detect_fund_filter(clean_query)
        filter_dict = {"fund_name": fund_filter} if fund_filter else None
        
        chunks = st.session_state.retrieval_service.retrieve(clean_query, filter_dict=filter_dict, n_results=5)
        
        if chunks:
            fallback_url = chunks[0]["metadata"].get("source_url")
            raw_llm_response = st.session_state.llm_service.generate_response(clean_query, chunks)
            validated_response = st.session_state.output_validator.validate_pipeline(
                raw_llm_response, chunks, fallback_url=fallback_url
            )
            st.session_state.messages.append({
                "role": "assistant", 
                "content": validated_response,
                "is_refusal": False
            })
        else:
            st.session_state.messages.append({
                "role": "assistant", 
                "content": "I am sorry, but the provided official source data does not contain this information.\n\n*Last updated from sources: 31 May 2026*",
                "is_refusal": False
            })

with col_info:
    st.markdown("### 💡 Quick Questions")
    st.write("Click on any query below to test the assistant's retrieval and refusal logic:")
    
    examples = [
        "Who manages HDFC Mid-Cap Opportunities Fund and what are their qualifications?",
        "What is the exit load for HDFC Defence Fund?",
        "What is the minimum SIP amount and expense ratio for HDFC Small Cap Fund?"
    ]
    
    for ex in examples:
        if st.button(ex, key=ex, use_container_width=True):
            st.session_state.messages.append({"role": "user", "content": ex})
            with st.spinner("Thinking..."):
                process_user_query(ex)
            st.rerun()

with col_chat:
    # Display message history using Streamlit's native responsive chat elements
    for msg in st.session_state.messages:
        role = msg["role"]
        content = msg["content"]
        is_ref = msg.get("is_refusal", False)
        
        with st.chat_message(role):
            if is_ref:
                st.info(content)
            else:
                st.markdown(content)

    # Chat Input box
    user_query = st.chat_input("Type your factual question about supported HDFC funds...")

    if user_query:
        st.session_state.messages.append({"role": "user", "content": user_query})
        with st.spinner("Processing factual RAG query..."):
            process_user_query(user_query)
        st.rerun()
