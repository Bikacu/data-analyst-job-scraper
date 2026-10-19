import json
import os
import random
import pandas as pd
from playwright.sync_api import sync_playwright

KEYWORDS = ["data-analyst", "business-intelligence-analyst", "analis-data"]
MAX_PAGES = 10
OUT = "jobs_list_all.csv"

def extract_jobs(html):
    marker = "window.SEEK_REDUX_DATA = "
    start = html.find(marker)
    if start == -1:
        return []
    data, _ = json.JSONDecoder().raw_decode(html, start + len(marker))

    jobs = {}
    def walk(obj):
        if isinstance(obj, dict):
            if "companyName" in obj and "listingDate" in obj and "id" in obj:
                jobs[obj["id"]] = obj
            for v in obj.values():
                walk(v)
        elif isinstance(obj, list):
            for v in obj:
                walk(v)
    walk(data)

    rows = []
    for j in jobs.values():
        loc = j.get("locations") or [{}]
        cls = j.get("classifications") or [{}]
        wt = j.get("workTypes")
        rows.append({
            "id": str(j.get("id")),
            "title": j.get("title"),
            "company": j.get("companyName"),
            "location": loc[0].get("label"),
            "salary": j.get("salaryLabel"),
            "category": cls[0].get("subclassification", {}).get("description"),
            "work_type": ", ".join(wt) if isinstance(wt, list) else wt,
            "listing_date": j.get("listingDate"),
            "teaser": j.get("teaser"),
        })
    return rows

# Mulai dari data lama
seen = {}
if os.path.exists("jobs_list.csv"):
    old = pd.read_csv("jobs_list.csv")
    old["id"] = old["id"].astype(str)
    for r in old.to_dict("records"):
        seen[r["id"]] = r
print("Data lama:", len(seen))

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    page = browser.new_page()

    for kw in KEYWORDS:
        base = f"https://id.jobstreet.com/id/{kw}-jobs"
        print(f"\n=== Keyword: {kw} ===")
        for n in range(1, MAX_PAGES + 1):
            url = base if n == 1 else f"{base}?page={n}"
            try:
                page.goto(url, timeout=60000)
                page.wait_for_timeout(5000)
                rows = extract_jobs(page.content())
            except Exception as e:
                print(f"  Hal {n}: error {type(e).__name__}, lanjut keyword berikutnya")
                break

            new = [r for r in rows if r["id"] not in seen]
            for r in new:
                seen[r["id"]] = r
            print(f"  Hal {n}: {len(rows)} lowongan, {len(new)} baru | total {len(seen)}")

            # Simpan setiap halaman
            pd.DataFrame(list(seen.values())).to_csv(OUT, index=False, encoding="utf-8-sig")

            if not rows or not new:
                print("  Tidak ada data baru, pindah keyword.")
                break
            page.wait_for_timeout(random.uniform(6, 12) * 1000)

    browser.close()

print("\nTotal lowongan unik:", len(seen), "->", OUT)