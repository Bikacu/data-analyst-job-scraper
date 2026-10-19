import re
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

NAVY, TEAL, GRAY = "#1F3A5F", "#2A9D8F", "#D9DEE5"

# 1. Load + hapus iklan duplikat (deskripsi identik)
t = pd.read_csv("jobs_target_all.csv")
d = pd.read_csv("jobs_detail.csv")
t["id"] = t["id"].astype(str); d["id"] = d["id"].astype(str)
df = t.merge(d, on="id").dropna(subset=["description"])
n0 = len(df)
df = df.drop_duplicates(subset="description").reset_index(drop=True)
N = len(df)
print(f"Lowongan dianalisa: {N} (duplikat dibuang: {n0 - N})")

low = df["description"].str.lower()
raw = df["description"]

# 2. Skill
SKILLS = {
    "Excel": r"\bexcel\b|spreadsheet|ms office|microsoft office",
    "SQL": r"\bsql\b|mysql|postgres|sql server",
    "Power BI": r"power\s?bi",
    "Tableau": r"tableau",
    "Python": r"\bpython\b",
    "Looker Studio": r"looker|data studio",
    "Google Sheets": r"google sheets?",
    "ETL": r"\betl\b",
    "R": r"(?<![\w&/])R(?![\w&/])",
    "BigQuery": r"bigquery",
    "Pandas/Numpy": r"pandas|numpy",
    "VBA/Macro": r"\bvba\b|macro",
    "Statistik (skill)": r"statistical|analisis statistik|teknik statistik|metode statistik|uji statistik",
    "Machine Learning": r"machine learning",
    "Dashboard": r"dashboard",
    "Visualisasi": r"visuali[sz]",
    "Komunikasi": r"komunikasi|communication",
    "Problem solving": r"problem.solving|pemecahan masalah",
    "Presentasi": r"presentasi|presentation",
    "Bahasa Inggris": r"bahasa inggris|english",
}
rows = []
for name, pat in SKILLS.items():
    src = raw if name == "R" else low
    c = int(src.str.contains(pat, regex=True, na=False).sum())
    rows.append({"skill": name, "jumlah": c, "persen": round(c / N * 100, 1)})
res = pd.DataFrame(rows).sort_values("jumlah", ascending=False)
res.to_csv("skill_freq.csv", index=False)
print("\n", res.to_string(index=False))

# 3. Pengalaman (tahun)
yrs = low.str.extract(r"(\d+)\s*\+?\s*(?:tahun|years?)")[0].dropna().astype(int)
yrs = yrs[yrs <= 15]
print(f"\nPengalaman disebut di {len(yrs)} lowongan")
print(yrs.value_counts().sort_index().to_string())
fresh = low.str.contains(r"fresh graduate|fresh grad", regex=True).sum()
print("Menyebut fresh graduate:", fresh)

# 4. Gaji per bulan
def parse(s):
    if not isinstance(s, str) or "month" not in s:
        return None
    n = [int(x.replace(".", "")) for x in re.findall(r"\d[\d.]*", s)]
    return (min(n), max(n)) if n else None

sal = df["salary"].apply(parse).dropna()
smin = pd.Series([x[0] for x in sal]); smax = pd.Series([x[1] for x in sal])
print(f"\nGaji per bulan: {len(sal)} lowongan")
if len(sal):
    print("Batas bawah:", sorted(smin), "| median:", int(smin.median()))
    print("Batas atas :", sorted(smax), "| median:", int(smax.median()))

# 5. Lokasi
df["kota"] = df["location"].fillna("").str.split(",").str[0].str.strip()
print("\nTop lokasi:")
print(df["kota"].value_counts().head(6).to_string())

# 6. Grafik 1: skill
top = res.head(12).iloc[::-1]
fig, ax = plt.subplots(figsize=(8, 5))
ax.barh(top["skill"], top["persen"], color=NAVY)
for i, v in enumerate(top["persen"]):
    ax.text(v + 1, i, f"{v:.0f}%", va="center", fontsize=9)
ax.set_xlabel("% lowongan"); ax.set_title(f"Skill paling dicari (n={N})")
for s in ("top", "right"): ax.spines[s].set_visible(False)
plt.tight_layout(); plt.savefig("chart_skills.png", dpi=150); plt.close()

# 7. Grafik 2: pengalaman
if len(yrs):
    vc = yrs.value_counts().sort_index()
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.bar(vc.index.astype(str), vc.values, color=TEAL)
    ax.set_xlabel("Tahun pengalaman diminta"); ax.set_ylabel("Jumlah lowongan")
    ax.set_title(f"Pengalaman yang diminta (n={len(yrs)})")
    for s in ("top", "right"): ax.spines[s].set_visible(False)
    plt.tight_layout(); plt.savefig("chart_experience.png", dpi=150); plt.close()

print("\nGrafik: chart_skills.png, chart_experience.png | Data: skill_freq.csv")    