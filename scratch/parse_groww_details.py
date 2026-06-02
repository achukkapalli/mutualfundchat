from bs4 import BeautifulSoup
import re
import json

html_path = "scratch/groww_mid_cap.html"
with open(html_path, "r", encoding="utf-8") as f:
    html = f.read()

soup = BeautifulSoup(html, "html.parser")

data = {}

# 1. Fund Name
h1 = soup.find("h1")
data["fund_name"] = h1.text.strip() if h1 else "Unknown Fund"

# 2. Category & Risk (from breadcrumbs or header labels)
header_div = soup.find("header")
if header_div:
    # Look for tags with tags/labels
    # e.g., "Equity", "Mid Cap", "Very High Risk"
    labels = [div.text.strip() for div in header_div.find_all("div") if len(div.text.strip()) > 0 and len(div.text.strip()) < 30]
    data["header_labels"] = list(set(labels))

# 3. Fund Details (NAV, Min SIP, AUM, Expense Ratio)
# We can search for the class containing fundDetailsContainer
details_container = soup.find("div", class_=re.compile("fundDetails_fundDetailsContainer"))
if details_container:
    # Each detail item is typically in a separate sub-div
    for item in details_container.find_all("div", recursive=False):
        # Sibling text or children text
        text_parts = [c.text.strip() for c in item.find_all(text=False) if c.text.strip()]
        if len(text_parts) >= 2:
            key = text_parts[0]
            val = text_parts[1]
            data[key] = val
        else:
            # Fallback
            full_text = item.text.strip()
            # If full_text is "Expense ratio0.73%"
            for kw in ["Expense ratio", "Min. for SIP", "Fund size", "NAV"]:
                if full_text.startswith(kw):
                    data[kw] = full_text.replace(kw, "").strip()
else:
    # Fallback search by text matches
    for div in soup.find_all("div", class_=re.compile("gap4")):
        text = div.text.strip()
        if "Expense ratio" in text:
            # e.g. "Expense ratio0.73%"
            data["Expense ratio"] = text.replace("Expense ratio", "").strip()
        elif "Min. for SIP" in text:
            data["Min. for SIP"] = text.replace("Min. for SIP", "").strip()

# 4. Exit Load and Tax
exit_load_section = soup.find("div", class_=re.compile("exitLoadStampDutyTax_section"))
if exit_load_section:
    data["Exit Load Text"] = exit_load_section.text.strip()
else:
    # Search for text contains Exit load
    for div in soup.find_all("div"):
        if div.text.strip().startswith("Exit load") and len(div.text.strip()) < 300:
            data["Exit Load Text"] = div.text.strip()

# 5. Benchmark Index
# Search for benchmark text in the document
benchmark_match = soup.find(string=re.compile("Fund benchmark", re.IGNORECASE))
if benchmark_match:
    parent = benchmark_match.parent
    # The benchmark name is usually the next sibling or near
    text_content = parent.parent.text.strip() if parent.parent else parent.text.strip()
    data["Benchmark Index"] = text_content.replace("Fund benchmark", "").strip()

# 6. Fund Managers
managers = []
# Fund managers are usually inside divs containing "Fund management" or "Compare Fund management"
managers_heading = soup.find(string=re.compile("Fund management", re.IGNORECASE))
if managers_heading:
    # Traverse the siblings or parents to find manager blocks
    # Let's find all manager details using text content matches
    manager_blocks = soup.find_all("div", class_=re.compile("fundManagement_managerCard"))
    if not manager_blocks:
        # Fallback: look for "View details" buttons or text
        view_details_matches = soup.find_all(string=re.compile("View details", re.IGNORECASE))
        for match in view_details_matches:
            parent_card = match.parent.parent.parent # adjust up to get the card
            # Let's inspect sibling elements
            card_text = parent_card.text.strip() if parent_card else ""
            if card_text:
                managers.append(card_text)

data["Managers Raw"] = managers

print(json.dumps(data, indent=2))
