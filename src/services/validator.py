import re
from datetime import datetime

class OutputValidator:
    def __init__(self, allowed_urls=None):
        self.allowed_urls = allowed_urls or [
            "https://groww.in/mutual-funds/hdfc-mid-cap-fund-direct-growth",
            "https://groww.in/mutual-funds/hdfc-large-cap-fund-direct-growth",
            "https://groww.in/mutual-funds/hdfc-small-cap-fund-direct-growth",
            "https://groww.in/mutual-funds/hdfc-gold-etf-fund-of-fund-direct-plan-growth",
            "https://groww.in/mutual-funds/hdfc-defence-fund-direct-growth"
        ]
        
        # PII Regex patterns
        self.pan_pattern = re.compile(r'\b[A-Z]{5}[0-9]{4}[A-Z]\b', re.IGNORECASE)
        # Aadhaar: 12 digits, can be formatted as XXXX XXXX XXXX or XXXXXXXXXXXX
        self.aadhaar_pattern = re.compile(r'\b[2-9]\d{3}\s\d{4}\s\d{4}\b|\b[2-9]\d{11}\b')
        self.phone_pattern = re.compile(r'\b(?:\+91[\-\s]?)?[6-9]\d{9}\b')
        self.email_pattern = re.compile(r'\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b')
        # OTP: 4 or 6 digit codes often labeled or contextualized as OTP
        self.otp_pattern = re.compile(r'\b\d{4,6}\b')

    def redact_pii(self, text):
        """Redacts sensitive PII (PAN, Aadhaar, phone, email, OTPs) from text."""
        if not text:
            return ""
        
        # Redact standard matches
        text = self.pan_pattern.sub("[REDACTED_PAN]", text)
        text = self.aadhaar_pattern.sub("[REDACTED_AADHAAR]", text)
        text = self.email_pattern.sub("[REDACTED_EMAIL]", text)
        text = self.phone_pattern.sub("[REDACTED_PHONE]", text)
        
        # Redact OTPs: only if they appear near words like "otp", "code", "pin", "verification"
        def otp_replacer(match):
            start = max(0, match.start() - 20)
            end = min(len(text), match.end() + 20)
            context = text[start:end].lower()
            if any(kw in context for kw in ["otp", "code", "pin", "verification", "one-time", "passcode"]):
                return "[REDACTED_OTP]"
            return match.group(0)
            
        text = self.otp_pattern.sub(otp_replacer, text)
        return text

    def count_sentences(self, text):
        """Counts sentences accurately, ignoring links/decimals."""
        # Replace links to prevent punctuation inside links from splitting sentences
        temp_text = re.sub(r'\[.*?\]\(.*?\)', 'LINK', text)
        # Regex to split on . or ? followed by whitespace, ignoring typical decimal points or abbreviations
        sentences = re.split(r'(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?)\s', temp_text)
        return [s.strip() for s in sentences if s.strip()]

    def enforce_sentence_limit(self, text, original_text_for_link=None):
        """
        Truncates response to maximum of 3 sentences.
        Preserves the markdown link if it gets cut off during truncation.
        """
        sentences = self.count_sentences(text)
        if len(sentences) <= 3:
            return text

        # Truncate to first 3 sentences
        truncated_sentences = sentences[:3]
        truncated_text = " ".join(truncated_sentences)

        # Check if the original text had a link
        link_match = re.search(r'(\[[^\]]+\]\([^)]+\))', original_text_for_link or text)
        if link_match:
            link_str = link_match.group(1)
            # If the truncated text doesn't contain this link anymore, append it
            if link_str not in truncated_text:
                # Append the link to the end of the third sentence (cleaning up trailing period if needed)
                if truncated_text.endswith("."):
                    truncated_text = truncated_text[:-1]
                truncated_text = f"{truncated_text} {link_str}."

        return truncated_text

    def validate_and_correct_link(self, text, fallback_url=None):
        """
        Ensures the response contains exactly one link, and that it is valid.
        If zero or multiple, corrects it to have exactly one pointing to fallback_url.
        """
        links = re.findall(r'\[([^\]]+)\]\(([^)]+)\)', text)
        
        # 1. If no links found, append a markdown link using the fallback_url
        if not links:
            url = fallback_url or self.allowed_urls[0]
            # Strip trailing period to append cleanly
            if text.endswith("."):
                text = text[:-1]
            return f"{text} [Source]({url})."
            
        # 2. If multiple links found, keep the first valid one and strip the others
        if len(links) > 1:
            first_link = None
            for title, url in links:
                if url in self.allowed_urls:
                    first_link = (title, url)
                    break
            
            # If none are in allowed list, use the first link overall or fallback
            if not first_link:
                first_link = links[0]
                
            # Replace all markdown links with their text, except the chosen one
            chosen_markdown = f"[{first_link[0]}]({first_link[1]})"
            
            # Temporary token to protect the chosen link during regex replacements
            protected_text = text.replace(chosen_markdown, "___PROTECTED_LINK___")
            
            # Replace remaining links with just their anchor text
            protected_text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', protected_text)
            
            # Restore the chosen link
            text = protected_text.replace("___PROTECTED_LINK___", chosen_markdown)
            return text

        # 3. Exactly one link exists. Verify it is in the allowed list
        title, url = links[0]
        if url not in self.allowed_urls:
            # Replace the invalid URL with the fallback_url
            corrected_url = fallback_url or self.allowed_urls[0]
            old_link = f"[{title}]({url})"
            new_link = f"[{title}]({corrected_url})"
            text = text.replace(old_link, new_link)
            
        return text

    def append_footer(self, text, last_updated_date=None):
        """Appends the required 'Last updated from sources: <date>' footer."""
        date_str = last_updated_date or datetime.today().strftime('%d %B %Y')
        # Clean any trailing newlines
        text = text.strip()
        return f"{text}\n\n*Last updated from sources: {date_str}*"

    def validate_pipeline(self, response_text, retrieved_chunks, fallback_url=None):
        """
        Runs the full validation and post-processing pipeline on an LLM response.
        """
        # Get the update date from the chunks if available
        last_updated_date = None
        if retrieved_chunks:
            # Gather unique dates
            dates = list(set(c["metadata"].get("last_updated") for c in retrieved_chunks if c["metadata"].get("last_updated")))
            if dates:
                last_updated_date = dates[0] # Pick the first available

        # 1. Redact PII
        processed = self.redact_pii(response_text)
        
        # 2. Link validation and correction
        processed = self.validate_and_correct_link(processed, fallback_url=fallback_url)
        
        # 3. Sentence count enforcement (keeps link safe)
        processed = self.enforce_sentence_limit(processed, response_text)
        
        # 4. Programmatic footer injection
        processed = self.append_footer(processed, last_updated_date)
        
        return processed
