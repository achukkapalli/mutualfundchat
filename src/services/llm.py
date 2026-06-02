import os
from dotenv import load_dotenv
from groq import Groq

from src.utils.normalization import normalize_query_fund_names

# Load environment variables
load_dotenv()

class LLMService:
    def __init__(self, model_name="llama-3.1-8b-instant"):
        self.model_name = model_name
        self.groq_api_key = os.getenv("GROQ_API_KEY")
        if not self.groq_api_key:
            raise ValueError("GROQ_API_KEY environment variable is not set. Please set it in your .env file.")
        self.client = Groq(api_key=self.groq_api_key)
        
        self.system_prompt = (
            "You are a trustworthy, facts-only Mutual Fund FAQ Assistant. Your role is to answer user queries strictly using the provided context.\n"
            "Under no circumstances should you provide investment advice, speculative predictions, or recommendations.\n\n"
            "STRICT CONSTRAINTS:\n"
            "1. Base your answer ONLY on the provided context. If the context does not contain the answer, say: 'I am sorry, but the provided official source data does not contain this information.'\n"
            "   Note on Fund Names: The user query may refer to schemes by their common/alternate names, which correspond to the context fund names as follows:\n"
            "   - 'HDFC Mid-Cap Opportunities Fund' or 'HDFC Mid-Cap Opportunities' or 'HDFC Mid Cap Fund' is the same as 'HDFC Mid Cap Fund Direct Growth'\n"
            "   - 'HDFC Top 100 Fund' or 'HDFC Top 100' or 'HDFC Large Cap Fund' is the same as 'HDFC Large Cap Fund Direct Growth'\n"
            "   - 'HDFC Small Cap Fund' is the same as 'HDFC Small Cap Fund Direct Growth'\n"
            "   - 'HDFC Gold ETF Fund of Fund' or 'HDFC Gold ETF FoF' is the same as 'HDFC Gold ETF Fund of Fund Direct Plan Growth'\n"
            "   - 'HDFC Defence Fund' is the same as 'HDFC Defence Fund Direct Growth'\n"
            "   Treat these names as exactly equivalent. Do not refuse queries simply because of these differences in naming.\n"
            "2. Your entire response MUST NOT exceed 3 sentences. Keep it very concise.\n"
            "3. You MUST include EXACTLY ONE markdown hyperlink citation pointing to the source URL from the context in the format [Source Name](URL) (e.g., [HDFC Mid Cap Fund Direct Growth](https://groww.in/mutual-funds/hdfc-mid-cap-fund-direct-growth)).\n"
            "4. Do not offer opinions, interpretations, returns predictions, or performance estimates."
        )

    def format_context(self, chunks):
        """Formats retrieved chunks into a standardized context block for the prompt."""
        context_parts = []
        for i, chunk in enumerate(chunks, 1):
            source_url = chunk["metadata"].get("source_url", "https://groww.in")
            fund_name = chunk["metadata"].get("fund_name", "the mutual fund")
            section = chunk["metadata"].get("section", "details")
            context_parts.append(
                f"Context Block {i} (Source URL: {source_url}, Fund Name: {fund_name}, Section: {section}):\n"
                f"{chunk['content']}\n"
            )
        return "\n---\n".join(context_parts)

    def generate_response(self, query_text, chunks):
        """
        Generates a response from the LLM based on the user query and the retrieved context chunks.
        """
        if not chunks:
            return "I am sorry, but the provided official source data does not contain this information."
            
        normalized_query = normalize_query_fund_names(query_text)
        formatted_context = self.format_context(chunks)
        
        user_message = (
            f"CONTEXT:\n"
            f"{formatted_context}\n\n"
            f"USER QUERY: {normalized_query}\n"
        )
        
        try:
            chat_completion = self.client.chat.completions.create(
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": user_message}
                ],
                model=self.model_name,
                temperature=0.0,
                max_tokens=300
            )
            return chat_completion.choices[0].message.content.strip()
        except Exception as e:
            return f"Error generating response from LLM: {str(e)}"
