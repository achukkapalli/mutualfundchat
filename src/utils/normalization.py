import re

def normalize_query_fund_names(query_text):
    """
    Normalizes common and alternate mutual fund names in the query text
    to match the standard names used in the corpus context.
    """
    replacements = [
        ("hdfc mid-cap opportunities fund direct growth", "HDFC Mid Cap Fund Direct Growth"),
        ("hdfc top 100 fund (large cap) direct growth", "HDFC Large Cap Fund Direct Growth"),
        ("hdfc gold etf fund of fund direct plan growth", "HDFC Gold ETF Fund of Fund Direct Plan Growth"),
        ("hdfc mid-cap opportunities fund", "HDFC Mid Cap Fund Direct Growth"),
        ("hdfc mid-cap opportunities", "HDFC Mid Cap Fund Direct Growth"),
        ("hdfc mid-cap fund direct growth", "HDFC Mid Cap Fund Direct Growth"),
        ("hdfc top 100 fund direct growth", "HDFC Large Cap Fund Direct Growth"),
        ("hdfc top 100 fund", "HDFC Large Cap Fund Direct Growth"),
        ("hdfc large cap fund direct growth", "HDFC Large Cap Fund Direct Growth"),
        ("hdfc small cap fund direct growth", "HDFC Small Cap Fund Direct Growth"),
        ("hdfc defence fund direct growth", "HDFC Defence Fund Direct Growth"),
        ("hdfc gold etf fof", "HDFC Gold ETF Fund of Fund Direct Plan Growth"),
        ("hdfc gold etf fund of fund", "HDFC Gold ETF Fund of Fund Direct Plan Growth"),
        ("hdfc mid cap fund", "HDFC Mid Cap Fund Direct Growth"),
        ("hdfc mid-cap fund", "HDFC Mid Cap Fund Direct Growth"),
        ("hdfc large cap fund", "HDFC Large Cap Fund Direct Growth"),
        ("hdfc small cap fund", "HDFC Small Cap Fund Direct Growth"),
        ("hdfc defence fund", "HDFC Defence Fund Direct Growth"),
        ("hdfc top 100", "HDFC Large Cap Fund Direct Growth"),
    ]
    
    normalized = query_text
    for old, new in replacements:
        pattern = re.compile(re.escape(old), re.IGNORECASE)
        normalized = pattern.sub(new, normalized)
    return normalized
