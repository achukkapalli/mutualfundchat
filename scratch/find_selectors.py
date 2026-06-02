from bs4 import BeautifulSoup
import re

html_path = "scratch/groww_mid_cap.html"
with open(html_path, "r", encoding="utf-8") as f:
    html = f.read()

soup = BeautifulSoup(html, "html.parser")

print("=== H1 Headers ===")
for h1 in soup.find_all("h1"):
    print(f"H1: {h1.text.strip()} | Classes: {h1.get('class')}")

print("\n=== H2 Headers ===")
for h2 in soup.find_all("h2")[:15]:
    print(f"H2: {h2.text.strip()} | Classes: {h2.get('class')}")

def find_text_context(target_text):
    print(f"\n=== Searching for: '{target_text}' ===")
    matches = soup.find_all(text=re.compile(target_text, re.IGNORECASE))
    print(f"Found {len(matches)} matches")
    for idx, match in enumerate(matches[:5]):
        parent = match.parent
        print(f"Match {idx+1}: '{match.strip()}'")
        print(f"  Parent Tag: {parent.name} | Classes: {parent.get('class')}")
        # Print grandparent if grandparent exists
        if parent.parent:
            print(f"  Grandparent Tag: {parent.parent.name} | Classes: {parent.parent.get('class')}")
            # Print outer HTML snippet
            print(f"  Snippet: {str(parent.parent)[:200]}...")

find_text_context("Expense ratio")
find_text_context("Exit load")
find_text_context("Chirag Setalvad")
find_text_context("Benchmark")
find_text_context("Riskometer")
