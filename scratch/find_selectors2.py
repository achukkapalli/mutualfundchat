import sys
from bs4 import BeautifulSoup
import re

# Reconfigure stdout to use UTF-8
sys.stdout.reconfigure(encoding='utf-8')

html_path = "scratch/groww_mid_cap.html"
with open(html_path, "r", encoding="utf-8") as f:
    html = f.read()

soup = BeautifulSoup(html, "html.parser")

def find_text_context(target_text):
    print(f"\n=== Searching for: '{target_text}' ===")
    matches = soup.find_all(string=re.compile(target_text, re.IGNORECASE))
    print(f"Found {len(matches)} matches")
    for idx, match in enumerate(matches[:5]):
        parent = match.parent
        print(f"Match {idx+1}: '{match.strip()[:100]}'")
        print(f"  Parent Tag: {parent.name} | Classes: {parent.get('class')}")
        if parent.parent:
            print(f"  Grandparent Tag: {parent.parent.name} | Classes: {parent.parent.get('class')}")
            # print surrounding html
            sibling_text = []
            for child in parent.parent.children:
                if child.string:
                    sibling_text.append(child.string.strip())
                elif hasattr(child, 'text'):
                    sibling_text.append(child.text.strip())
            print(f"  Sibling Text content: {' | '.join([s for s in sibling_text if s])}")

find_text_context("Expense ratio")
find_text_context("Exit load")
find_text_context("Chirag Setalvad")
find_text_context("Benchmark")
find_text_context("Riskometer")
