import os
import re
import json
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import sys

# Configure stdout to use UTF-8 just in case
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

class GrowwScraper:
    def __init__(self, sources_config_path="config/sources.json", output_dir="data/raw"):
        self.sources_config_path = sources_config_path
        self.output_dir = output_dir
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        os.makedirs(self.output_dir, exist_ok=True)

    def load_sources(self):
        if not os.path.exists(self.sources_config_path):
            raise FileNotFoundError(f"Sources config file not found: {self.sources_config_path}")
        with open(self.sources_config_path, "r", encoding="utf-8") as f:
            return json.load(f).get("sources", [])

    def fetch_page_content(self, url):
        """Fetches HTML content of a URL using requests. Falls back to Playwright if needed."""
        try:
            print(f"Fetching URL via requests: {url}")
            res = requests.get(url, headers=self.headers, timeout=15)
            if res.status_code == 200:
                # Basic check to ensure we got actual fund data and not a blank JS template
                if "NAV" in res.text or "Expense ratio" in res.text:
                    return res.text
                print("  Requests succeeded but content seems incomplete. Triggering Playwright fallback...")
            else:
                print(f"  Requests failed with status code: {res.status_code}. Triggering Playwright fallback...")
        except Exception as e:
            print(f"  Error fetching with requests: {e}. Triggering Playwright fallback...")
            
        return self._fetch_with_playwright(url)

    def _fetch_with_playwright(self, url):
        """Fallback dynamic scraper using headless Playwright."""
        try:
            from playwright.sync_api import sync_playwright
            print(f"  Launching Playwright for: {url}")
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                page.goto(url, wait_until="networkidle", timeout=30000)
                content = page.content()
                browser.close()
                return content
        except Exception as e:
            print(f"  Playwright fallback failed: {e}")
            return None

    def clean_text(self, text):
        """Strips excessive whitespaces, tabs, and non-breaking spaces."""
        if not text:
            return ""
        text = text.replace("\xa0", " ")  # Replace non-breaking spaces
        text = re.sub(r'\s+', ' ', text)  # Collapse multiple whitespaces
        return text.strip()

    def parse_fund_page(self, html, url):
        """Parses the raw HTML of a Groww mutual fund page."""
        if not html:
            return None

        soup = BeautifulSoup(html, "html.parser")
        extracted = {}

        # 1. Fund Name
        h1 = soup.find("h1")
        fund_name = self.clean_text(h1.text) if h1 else "Unknown Fund"
        extracted["fund_name"] = fund_name

        # 2. Header labels (Category, segment, risk level)
        category = "Unknown"
        segment = "Unknown"
        risk_level = "Unknown"
        
        header_div = soup.find("header")
        if header_div:
            labels = [self.clean_text(d.text) for d in header_div.find_all("div") if d.text.strip()]
            for label in labels:
                if "Risk" in label:
                    risk_level = label
                elif label in ["Equity", "Debt", "Hybrid", "Other", "Commodities"]:
                    category = label
                elif len(label) < 25 and label not in [fund_name, risk_level, category]:
                    # Mid Cap, Large Cap, Small Cap, Sectoral, etc.
                    segment = label
        
        extracted["category"] = category
        extracted["segment"] = segment
        extracted["risk_level"] = risk_level

        # 3. Fund Details Grid (NAV, Min SIP, AUM, Expense Ratio, Rating)
        nav_val = "N/A"
        nav_date = "N/A"
        min_sip = "N/A"
        aum = "N/A"
        expense_ratio = "N/A"
        rating = "N/A"

        details_container = soup.find("div", class_=re.compile("fundDetails_fundDetailsContainer"))
        if details_container:
            for item in details_container.find_all("div", recursive=False):
                # Clean up any child-wrapper structural items
                text_parts = [self.clean_text(c.text) for c in item.find_all(text=False) if c.text.strip()]
                if len(text_parts) >= 2:
                    key, val = text_parts[0], text_parts[1]
                else:
                    # Fallback key-value split
                    full_text = self.clean_text(item.text)
                    key = ""
                    val = ""
                    for kw in ["Expense ratio", "Min. for SIP", "Min. SIP", "Fund size (AUM)", "Fund size", "NAV", "Rating"]:
                        if full_text.startswith(kw):
                            key = kw
                            val = full_text.replace(kw, "").strip()
                            break
                    if not key:
                        continue
                
                # Assign values
                if "NAV" in key:
                    nav_val = val.replace("₹", "").strip()
                    # Extract date if present, e.g., "NAV: 29 May '26"
                    date_match = re.search(r"NAV:\s*(.*)", key)
                    if date_match:
                        nav_date = date_match.group(1).strip()
                elif "Min. for SIP" in key or "Min. SIP" in key:
                    min_sip = val.replace("₹", "").strip()
                elif "Fund size" in key:
                    aum = val.replace("₹", "").strip()
                elif "Expense ratio" in key:
                    expense_ratio = val.strip()
                elif "Rating" in key:
                    rating = val.strip()
        else:
            # Fallback direct searches
            for div in soup.find_all("div", class_=re.compile("gap4")):
                txt = self.clean_text(div.text)
                if "Expense ratio" in txt:
                    expense_ratio = txt.replace("Expense ratio", "").strip()
                elif "Min. for SIP" in txt or "Min. SIP" in txt:
                    min_sip = txt.replace("Min. for SIP", "").replace("Min. SIP", "").replace("₹", "").strip()

        extracted["nav"] = nav_val
        extracted["nav_date"] = nav_date
        extracted["min_sip"] = min_sip
        extracted["aum"] = aum
        extracted["expense_ratio"] = expense_ratio
        extracted["rating"] = rating

        # 4. Exit Load, Stamp Duty, Tax Implications
        exit_load_val = "N/A"
        stamp_duty_val = "N/A"
        tax_implication_val = "N/A"

        exit_load_section = soup.find("div", class_=re.compile("exitLoadStampDutyTax_section"))
        if exit_load_section:
            # Find sub divs or headings
            text_blocks = exit_load_section.find_all("div", class_=re.compile("exitLoadStampDutyTax_termBlock"))
            if not text_blocks:
                # Alternative structure
                raw_text = self.clean_text(exit_load_section.text)
                # Try pattern matching
                exit_match = re.search(r"Exit load(.*?)(?:Stamp duty|Tax|$)", raw_text, re.IGNORECASE)
                stamp_match = re.search(r"Stamp duty(.*?)(?:Tax|$)", raw_text, re.IGNORECASE)
                tax_match = re.search(r"Tax implication(.*)", raw_text, re.IGNORECASE)
                if exit_match: exit_load_val = exit_match.group(1).strip()
                if stamp_match: stamp_duty_val = stamp_match.group(1).strip()
                if tax_match: tax_implication_val = tax_match.group(1).strip()
            else:
                for block in text_blocks:
                    h5 = block.find("h5")
                    p = block.find("p")
                    if h5 and p:
                        title = self.clean_text(h5.text)
                        desc = self.clean_text(p.text)
                        if "Exit load" in title:
                            exit_load_val = desc
                        elif "Stamp duty" in title:
                            stamp_duty_val = desc
                        elif "Tax" in title:
                            tax_implication_val = desc
        else:
            # Direct text search fallback
            exit_load_heading = soup.find(string=re.compile("Exit load", re.IGNORECASE))
            if exit_load_heading and exit_load_heading.parent:
                p_tag = exit_load_heading.parent.find_next("p")
                if p_tag:
                    exit_load_val = self.clean_text(p_tag.text)
            
            tax_heading = soup.find(string=re.compile("Tax implication", re.IGNORECASE))
            if tax_heading and tax_heading.parent:
                p_tag = tax_heading.parent.find_next("p")
                if p_tag:
                    tax_implication_val = self.clean_text(p_tag.text)

        extracted["exit_load"] = exit_load_val
        extracted["stamp_duty"] = stamp_duty_val
        extracted["tax_implications"] = tax_implication_val

        # 5. Benchmark Index
        benchmark_val = "N/A"
        benchmark_match = soup.find(string=re.compile("Fund benchmark", re.IGNORECASE))
        if benchmark_match:
            parent = benchmark_match.parent
            text_content = self.clean_text(parent.parent.text if parent.parent else parent.text)
            benchmark_val = text_content.replace("Fund benchmark", "").strip()
        
        extracted["benchmark_index"] = benchmark_val

        # 6. Fund Managers accordion parsing
        managers = []
        accordions = [
            div for div in soup.find_all("div", class_=re.compile("fundManagement_accordion"))
            if "Header" not in "".join(div.get("class", [])) and "Icon" not in "".join(div.get("class", []))
        ]

        for acc in accordions:
            manager_info = {}
            
            name_div = acc.find("div", class_=re.compile("fundManagement_personName"))
            if name_div:
                manager_info["name"] = self.clean_text(name_div.text)
            else:
                continue
                
            card_text_div = name_div.parent
            if card_text_div:
                tenure_div = card_text_div.find("div", class_=re.compile("bodyLarge"))
                if tenure_div:
                    manager_info["tenure"] = self.clean_text(tenure_div.text)

            body_div = acc.find("div", class_="ac11Hidden")
            if body_div:
                titles = body_div.find_all("div", class_=re.compile("fundManagement_detailTitle"))
                for title in titles:
                    title_text = self.clean_text(title.text)
                    val_div = title.find_next_sibling()
                    if not val_div:
                        continue
                        
                    if "Education" in title_text:
                        manager_info["education"] = self.clean_text(val_div.text)
                    elif "Experience" in title_text:
                        manager_info["experience"] = self.clean_text(val_div.text)
                    elif "manages" in title_text.lower():
                        links = [self.clean_text(a.text) for a in val_div.find_all("a") if a.text.strip()]
                        manager_info["other_schemes"] = links
            
            managers.append(manager_info)

        extracted["managers"] = managers
        return extracted

    def format_to_sections(self, raw_data, url):
        """Converts raw parsed data into a list of standardized schema documents."""
        if not raw_data:
            return []

        sections = []
        fund_name = raw_data["fund_name"]
        today_str = datetime.today().strftime('%d %B %Y')

        # Document 1: Overview and Basic Details
        overview_text = (
            f"Mutual Fund Scheme: {fund_name}. "
            f"Category: {raw_data['category']}. "
            f"Segment: {raw_data['segment']}. "
            f"Riskometer Classification: {raw_data['risk_level']}. "
            f"Latest Net Asset Value (NAV): Rs. {raw_data['nav']} (as of {raw_data['nav_date']}). "
            f"Minimum Systematic Investment Plan (SIP) Amount: Rs. {raw_data['min_sip']}. "
            f"Fund Size / Assets Under Management (AUM): {raw_data['aum']}. "
            f"Expense Ratio: {raw_data['expense_ratio']}. "
            f"Benchmark Index: {raw_data['benchmark_index']}. "
            f"Groww Scheme Rating: {raw_data['rating']} stars."
        )
        sections.append({
            "fund_name": fund_name,
            "section": "Overview",
            "content": overview_text,
            "source_url": url,
            "last_updated": today_str
        })

        # Document 2: Exit Load, Stamp Duty and Tax Implications
        fees_text = (
            f"Mutual Fund Scheme: {fund_name}. "
            f"Exit Load Details: {raw_data['exit_load']} "
            f"Stamp Duty on Investment: {raw_data['stamp_duty']} "
            f"Tax Implications: {raw_data['tax_implications']}"
        )
        sections.append({
            "fund_name": fund_name,
            "section": "Exit Load and Taxation",
            "content": fees_text,
            "source_url": url,
            "last_updated": today_str
        })

        # Document 3: Fund Management Team
        for manager in raw_data.get("managers", []):
            name = manager.get("name", "Unknown Manager")
            tenure = manager.get("tenure", "N/A")
            education = manager.get("education", "N/A")
            experience = manager.get("experience", "N/A")
            other_schemes = ", ".join(manager.get("other_schemes", []))
            
            manager_text = (
                f"Mutual Fund Scheme: {fund_name}. "
                f"Fund Manager: {name}. "
                f"Active Tenure: {tenure}. "
                f"Educational Qualifications: {education}. "
                f"Professional Experience: {experience}. "
                f"Other Schemes Managed by {name}: {other_schemes}."
            )
            sections.append({
                "fund_name": fund_name,
                "section": f"Fund Management - {name}",
                "content": manager_text,
                "source_url": url,
                "last_updated": today_str
            })

        return sections

    def run(self):
        """Runs the scraper for all configured sources and saves parsed documents."""
        sources = self.load_sources()
        print(f"Found {len(sources)} sources to scrape.")
        
        all_documents = []
        
        for source in sources:
            name = source["name"]
            url = source["url"]
            print(f"\nProcessing scheme: {name}")
            
            html = self.fetch_page_content(url)
            if not html:
                print(f"[ERROR] Failed to fetch content for {name}")
                continue
                
            raw_data = self.parse_fund_page(html, url)
            if not raw_data:
                print(f"[ERROR] Failed to parse content for {name}")
                continue
                
            # Format to schemas
            documents = self.format_to_sections(raw_data, url)
            all_documents.extend(documents)
            
            # Save raw parsed data as a snapshot
            sanitized_name = re.sub(r'[^a-zA-Z0-9]', '_', name).lower()
            snapshot_path = os.path.join(self.output_dir, f"{sanitized_name}_raw.json")
            with open(snapshot_path, "w", encoding="utf-8") as f:
                json.dump(raw_data, f, indent=2, ensure_ascii=False)
            print(f"Saved raw snapshot to {snapshot_path}")

        # Save all standardized schema documents combined
        combined_path = os.path.join(self.output_dir, "scraped_documents.json")
        with open(combined_path, "w", encoding="utf-8") as f:
            json.dump(all_documents, f, indent=2, ensure_ascii=False)
        print(f"\nSaved all {len(all_documents)} standardized documents to {combined_path}")
        return all_documents

if __name__ == "__main__":
    scraper = GrowwScraper()
    scraper.run()
