import pandas as pd
import math

# ── Load ──────────────────────────────────────────────────────────────────────
df = pd.read_csv(r"C:\Perfume_Seeker\Data_Fragrantica\archive\fra_selected.csv")

# ── Score ─────────────────────────────────────────────────────────────────────
df["score"] = df["Rating Value"] * df["Rating Count"].apply(lambda x: math.log10(x + 1))

# ── Sort by score descending ──────────────────────────────────────────────────
df = df.sort_values("score", ascending=False).reset_index(drop=True)

# ── Apply brand diversity cap (max 3 per brand) ───────────────────────────────
brand_counts = {}
selected_rows = []

for _, row in df.iterrows():
    brand = row["Brand"]
    if brand_counts.get(brand, 0) < 3:
        selected_rows.append(row)
        brand_counts[brand] = brand_counts.get(brand, 0) + 1
    if len(selected_rows) == 200:
        break

top200 = pd.DataFrame(selected_rows).reset_index(drop=True)

# ── Preview ───────────────────────────────────────────────────────────────────
print("Top 10 by score:")
print(top200[["Perfume", "Brand", "Rating Value", "Rating Count", "score"]].head(10).to_string())
print("\nBrands represented:", top200["Brand"].nunique())
print("Brand distribution (top 10 brands):")
print(top200["Brand"].value_counts().head(10))

# ── Save ──────────────────────────────────────────────────────────────────────
top200.to_csv(
    r"C:\Perfume_Seeker\Data_Fragrantica\archive\fra_top200.csv",
    index=False,
    encoding="utf-8"
)
print("\nSaved to fra_top200.csv")
