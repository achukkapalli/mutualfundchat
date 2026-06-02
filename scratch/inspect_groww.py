import requests
import os

url = "https://groww.in/mutual-funds/hdfc-mid-cap-fund-direct-growth"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

# Create scratch directory if not exists
os.makedirs("scratch", exist_ok=True)

print(f"Fetching {url}...")
res = requests.get(url, headers=headers)
print(f"Status: {res.status_code}")
if res.status_code == 200:
    html_path = "scratch/groww_mid_cap.html"
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(res.text)
    print(f"Saved HTML to {html_path} ({len(res.text)} bytes)")
else:
    print("Failed to fetch.")
