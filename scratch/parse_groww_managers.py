from bs4 import BeautifulSoup
import re
import json

html_path = "scratch/groww_mid_cap.html"
with open(html_path, "r", encoding="utf-8") as f:
    html = f.read()

soup = BeautifulSoup(html, "html.parser")

# Find only the accordion containers (class matches fundManagement_accordion but not header/icon/body)
accordions = [
    div for div in soup.find_all("div", class_=re.compile("fundManagement_accordion"))
    if "Header" not in "".join(div.get("class", [])) and "Icon" not in "".join(div.get("class", []))
]

print(f"Filtered {len(accordions)} manager accordions")

managers = []
for acc in accordions:
    manager_info = {}
    
    # Name
    name_div = acc.find("div", class_=re.compile("fundManagement_personName"))
    if name_div:
        manager_info["name"] = name_div.text.strip()
    else:
        continue
        
    # Tenure
    # It is usually a sibling of name_div's container or inside nameCard
    card_text_div = name_div.parent
    if card_text_div:
        tenure_div = card_text_div.find("div", class_=re.compile("bodyLarge"))
        if tenure_div:
            manager_info["tenure"] = tenure_div.text.strip()

    # Initials
    initials_div = acc.find("div", class_=re.compile("fundManagement_initials"))
    if initials_div:
        manager_info["initials"] = initials_div.text.strip()
        
    # Hidden details (Education, Experience, Other Schemes)
    body_div = acc.find("div", class_="ac11Hidden")
    if body_div:
        # Find detail blocks
        # e.g., education, experience, other schemes
        # We can find all sections with "detailTitle"
        titles = body_div.find_all("div", class_=re.compile("fundManagement_detailTitle"))
        for title in titles:
            title_text = title.text.strip()
            # The next sibling contains the value
            val_div = title.find_next_sibling()
            if not val_div:
                continue
                
            if "Education" in title_text:
                manager_info["education"] = val_div.text.strip()
            elif "Experience" in title_text:
                manager_info["experience"] = val_div.text.strip()
            elif "manages" in title_text.lower():
                # Extract links
                links = [a.text.strip() for a in val_div.find_all("a") if a.text.strip()]
                manager_info["other_schemes"] = links

    managers.append(manager_info)

print(json.dumps(managers, indent=2))
