class RefusalHandler:
    def __init__(self):
        self.sebi_link = "https://investor.sebi.gov.in"
        self.amfi_link = "https://www.amfiindia.com"

    def get_refusal_response(self, query_text, reason=None):
        """
        Returns a structured refusal response containing a polite refusal message
        and a link to an official education resource.
        """
        message = (
            "I cannot answer this query because it requests investment advice, recommendations, "
            "or speculative performance predictions. As a facts-only assistant, I can only provide objective, "
            "verifiable information about the mutual fund schemes from official sources."
        )
        
        # We can dynamically decide to share SEBI or AMFI education links
        link_title = "SEBI Investor Education"
        link_url = self.sebi_link
        
        # If the user asked "which is better" or compares, maybe AMFI is very relevant
        if "better" in query_text.lower() or "compare" in query_text.lower():
            link_title = "AMFI India"
            link_url = self.amfi_link

        return {
            "answer": f"{message}\n\nFor educational guidance, please refer to the [{link_title}]({link_url}) website.",
            "source_url": link_url,
            "is_refusal": True,
            "refusal_reason": reason
        }
