import os
import re
import json
from dotenv import load_dotenv
from groq import Groq

# Load environment variables
load_dotenv()

class IntentClassifier:
    def __init__(self, model_name="llama-3.1-8b-instant"):
        self.model_name = model_name
        self.groq_api_key = os.getenv("GROQ_API_KEY")
        self.client = None
        if self.groq_api_key:
            self.client = Groq(api_key=self.groq_api_key)
            
        # Compile deterministic regex patterns for quick classification
        self.advisory_keywords = [
            r"\bshould\s+i\s+(buy|invest|sell|redeem|choose)\b",
            r"\bwhich\s+(fund|scheme|one)\s+is\s+better\b",
            r"\b(suggest|recommend)\s+a\s+(fund|scheme|investment)\b",
            r"\bbest\s+(mutual\s+)?fund(s)?\b",
            r"\bis\s+it\s+(good|safe|profitable|worth)\s+to\s+(invest|buy)\b",
            r"\bhow\s+much\s+return(s)?\b",
            r"\bpredict\s+return(s)?\b",
            r"\breturns\s+prediction(s)?\b",
            r"\bwill\s+it\s+(double|grow|give|yield)\b",
            r"\bcompare\s+hdfc\b",
            r"\bwhat\s+is\s+your\s+opinion\b",
            r"\bgive\s+me\s+investment\s+advice\b"
        ]
        self.advisory_regex = re.compile("|".join(self.advisory_keywords), re.IGNORECASE)

        # Map query keywords to standard fund names in the DB
        self.fund_mappings = {
            "mid-cap": "HDFC Mid Cap Fund Direct Growth",
            "mid cap": "HDFC Mid Cap Fund Direct Growth",
            "midcap": "HDFC Mid Cap Fund Direct Growth",
            "large-cap": "HDFC Large Cap Fund Direct Growth",
            "large cap": "HDFC Large Cap Fund Direct Growth",
            "largecap": "HDFC Large Cap Fund Direct Growth",
            "top 100": "HDFC Large Cap Fund Direct Growth",
            "small-cap": "HDFC Small Cap Fund Direct Growth",
            "small cap": "HDFC Small Cap Fund Direct Growth",
            "smallcap": "HDFC Small Cap Fund Direct Growth",
            "gold": "HDFC Gold ETF Fund of Fund Direct Plan Growth",
            "etf": "HDFC Gold ETF Fund of Fund Direct Plan Growth",
            "defence": "HDFC Defence Fund Direct Growth",
            "defense": "HDFC Defence Fund Direct Growth"
        }

    def detect_fund_filter(self, query_text):
        """
        Analyzes the query text for mutual fund keywords and returns the 
        standard fund name for filtering, or None if no specific fund is mentioned.
        """
        query_lower = query_text.lower()
        for kw, fund_name in self.fund_mappings.items():
            if kw in query_lower:
                return fund_name
        return None

    def classify_intent(self, query_text):
        """
        Classifies the intent of a user's query as either 'FACTUAL' or 'ADVISORY'.
        Returns a tuple: (category, reason)
        """
        # 1. Deterministic Regex Check (Fast Check)
        if self.advisory_regex.search(query_text):
            return "ADVISORY", "Matched deterministic advisory keyword/phrase pattern."

        # 2. LLM Verification Check (Fallback Check)
        if not self.client:
            # If Groq client is not initialized, fallback to FACTUAL by default
            return "FACTUAL", "Groq client not configured, defaulted to factual."

        try:
            system_prompt = (
                "You are an expert Mutual Fund Query Router. Your sole job is to classify a user's query into one of two categories:\n"
                "1. 'FACTUAL': The query asks for objective, historical, or verifiable facts about a mutual fund scheme "
                "(e.g., expense ratio, exit load, minimum SIP/lumpsum, AUM, category, benchmark index, fund manager names, educational qualifications, active tenure, other schemes managed).\n"
                "2. 'ADVISORY': The query asks for investment advice, recommendations, opinions, comparison of which fund is better, "
                "speculates or asks for performance predictions/returns, or asks whether they should invest/buy/sell/redeem a fund.\n\n"
                "You must output ONLY a valid JSON object matching this structure:\n"
                "{\n"
                "  \"category\": \"FACTUAL\" | \"ADVISORY\",\n"
                "  \"reason\": \"A short explanation of why the query was classified as such.\"\n"
                "}\n"
                "Do not include any other markdown format, text, or explanations outside the JSON."
            )
            
            chat_completion = self.client.chat.completions.create(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Query: {query_text}"}
                ],
                model=self.model_name,
                response_format={"type": "json_object"},
                temperature=0.0,
                max_tokens=150
            )
            
            response_text = chat_completion.choices[0].message.content.strip()
            result = json.loads(response_text)
            
            category = result.get("category", "FACTUAL").upper()
            reason = result.get("reason", "LLM-determined classification.")
            
            if category not in ["FACTUAL", "ADVISORY"]:
                category = "FACTUAL"
                
            return category, reason
            
        except Exception as e:
            # In case of API failure, fallback to FACTUAL
            return "FACTUAL", f"LLM classification failed: {str(e)}. Fallback to factual."
