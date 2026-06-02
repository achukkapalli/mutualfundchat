from bs4 import BeautifulSoup
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

html_path = "scratch/groww_mid_cap.html"
with open(html_path, "r", encoding="utf-8") as f:
    html = f.read()

soup = BeautifulSoup(html, "html.parser")

accordions = soup.find_all("div", class_=re.compile("fundManagement_accordion"))
print(f"Found {len(accordions)} accordions")

for idx, acc in enumerate(accordions):
    print(f"\n=== Accordion {idx+1} ===")
    print(acc.prettify()[:2500])
