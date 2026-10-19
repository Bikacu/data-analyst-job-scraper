import os
import random
import pandas as pd
from playwright.sync_api import sync_playwright

df = pd.read_csv("jobs_list_all.csv")
df["id"] = df["id"].astype(str)

# 1. Filter judul
has_data = r"data|business intelligence|\bBI\b|analytics|insight"
has_role = r"analyst|analytic|analis|intelligence|\bBI\b"
exclude = r"engineer|master data|library|support officer|scientist"

t = df["title"].fillna("")
mask = (
    t.str.contains(has_data, case=False, regex=True)
    & t.str.contains(has_role, case=False, regex=True)
    & ~t.str.contains(exclude, case=False, regex=True)
)
target = df[mask].copy()
target.to_csv("jobs_target_all.csv", index=False, encoding="utf-8-sig")
print(f"Lowongan target: {len(target)} dari {len(df)}")

# 2. Tentukan yang belum diambil detailnya
OUT = "jobs_detail.csv"
done = set()
if os.path.exists(OUT):
    done = set(pd.read_csv(OUT)["id"].astype(str))
todo = target[~target["id"].isin(done)]
print(f"Sudah ada detail: {len(target) - len(todo)} | perlu diambil: {len(todo)}")

# 3. Ambil detail (resume-able)
with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    page = browser.new_page()

    for i, (_, row) in enumerate(todo.iterrows(), 1):
        job_id = row["id"]
        url = f"https://id.jobstreet.com/id/job/{job_id}"
        try:
            page.goto(url, timeout=60000)
            page.wait_for_timeout(4000)
            el = page.query_selector('[data-automation="jobAdDetails"]')
            if el is None:
                print(f"[{i}/{len(todo)}] {job_id}: selector tidak ketemu, berhenti.")
                break
            text = el.inner_text()
        except Exception as e:
            print(f"[{i}/{len(todo)}] {job_id}: error {type(e).__name__}, berhenti.")
            break

        pd.DataFrame([{"id": job_id, "description": text}]).to_csv(
            OUT, mode="a", index=False, encoding="utf-8-sig",
            header=not os.path.exists(OUT),
        )
        print(f"[{i}/{len(todo)}] {job_id}: OK ({len(text)} karakter)")

        if i < len(todo):
            page.wait_for_timeout(random.uniform(6, 12) * 1000)

    browser.close()

print("Selesai. Cek", OUT)