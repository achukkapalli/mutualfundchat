from bs4 import BeautifulSoup
import re
import sys

html_path = "scratch/groww_mid_cap.html"
with open(html_path, "r", encoding="utf-8") as f:
    html = f.read()

soup = BeautifulSoup(html, "html.parser")

out_lines = []

def log(text):
    out_lines.append(text + "\n")

log("=== H1 Headers ===")
for h1 in soup.find_all("h1"):
    log(f"H1: {h1.text.strip()} | Classes: {h1.get('class')}")

log("\n=== H2 Headers ===")
for h2 in soup.find_all("h2")[:15]:
    log(f"H2: {h2.text.strip()} | Classes: {h2.get('class')}")

# Let's inspect the entire "Expense ratio", "Exit load" details table or grid
log("\n=== Checking Grid/Table cells ===")
# Groww pages often use div grids with labels and values. Let's print all parent-grandparent pairs that have values.
for div in soup.find_all("div", class_=re.compile("Details_|gap4|exitLoad")):
    text = div.text.strip()
    if len(text) < 150 and any(kw in text for kw in ["Expense ratio", "Exit load", "Benchmark", "Min. SIP"]):
        log(f"Div (class={div.get('class')}): '{text}'")

def find_text_context(target_text):
    log(f"\n=== Searching for: '{target_text}' ===")
    matches = soup.find_all(string=re.compile(target_text, re.IGNORECASE))
    log(f"Found {len(matches)} matches")
    for idx, match in enumerate(matches[:5]):
        parent = match.parent
        log(f"Match {idx+1}: '{match.strip()[:100]}'")
        log(f"  Parent Tag: {parent.name} | Classes: {parent.get('class')}")
        if parent.parent:
            log(f"  Grandparent Tag: {parent.parent.name} | Classes: {parent.parent.get('class')}")
            sibling_text = []
            for child in parent.parent.children:
                if child.string:
                    sibling_text.append(child.string.strip())
                elif hasattr(child, 'text'):
                    sibling_text.append(child.text.strip())
            log(f"  Sibling Text content: {' | '.join([s for s in sibling_text if s])}")

find_text_context("Expense ratio")
find_text_context("Exit load")
find_text_context("Chirag Setalvad")
find_text_context("Benchmark")
find_text_context("Riskometer")
find_text_context("Min. SIP")

with open("scratch/selectors_output.txt", "w", encoding="utf-8") as f:
    f.writelines(out_lines)

print("Done. Saved output to scratch/selectors_output.txt")
