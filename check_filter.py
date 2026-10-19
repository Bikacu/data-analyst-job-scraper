import pandas as pd

df = pd.read_csv("jobs_list_all.csv")
t = pd.read_csv("jobs_target_all.csv")
rest = df[~df["id"].astype(str).isin(t["id"].astype(str))]

m = rest["title"].fillna("").str.contains(
    "data|analy|intelligence|BI", case=False, regex=True
)

print("Judul TIDAK lolos filter tapi mengandung data/analy/BI:")
print(rest[m]["title"].value_counts().head(40).to_string())

print("\nContoh judul lain (acak):")
print(rest[~m]["title"].sample(15, random_state=1).to_string())

sal = t["salary"].fillna("").str.contains("month").sum()
print("\nTarget dengan gaji per bulan:", sal, "dari", len(t))