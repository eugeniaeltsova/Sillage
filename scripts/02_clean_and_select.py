import pandas as pd

# ── Load ──────────────────────────────────────────────────────────────────────
df = pd.read_csv(
    r"C:\Perfume_Seeker\Data_Fragrantica\archive\fra_cleaned.csv",
    encoding="latin-1",
    sep=";",
    on_bad_lines="skip"
)

# ── Clean Rating Value (commas → points) ────
# 
df["Rating Value"] = (
    df["Rating Value"].str.replace(",", ".", regex=False).astype(float)
)

# ── Clean Perfume name (slug → title) ─────────────────────────────────────────
df["Perfume"] = df["Perfume"].str.replace("-", " ").str.strip().str.title()

# ── Clean Brand name (strip) ───────────────────────────────────────────────
df["Brand"] = df["Brand"].str.replace("-", " ").str.strip().str.title()

# ── Fill missing Year ─────────────────────────────────────────────────────────
df["Year"] = df["Year"].fillna(0).astype(int)

# ── Combine accords ───────────────────────────────────────────────────────────
accord_cols = ["mainaccord1", "mainaccord2", "mainaccord3", "mainaccord4", "mainaccord5"]
df["accords"] = df[accord_cols].apply(
    lambda row: ", ".join([str(v) for v in row if pd.notna(v) and str(v).strip() != ""]),
    axis=1
)

# ── Combine notes (structured, keeps top/middle/base tags) ────────────────────
df["notes_combined"] = (
    "top: "     + df["Top"].fillna("unknown") + " | " +
    "middle: "  + df["Middle"].fillna("unknown") + " | " +
    "base: "    + df["Base"].fillna("unknown") + " | " +
    "accords: " + df["accords"]
)

# ── Select final columns ──────────────────────────────────────────────────────
df_clean = df[[
    "url", "Perfume", "Brand", "Gender",
    "Rating Value", "Rating Count", "Year",
    "Perfumer1", "Top", "Middle", "Base",
    "accords", "notes_combined"
]].copy()

# ── Preview ───────────────────────────────────────────────────────────────────
print("Shape:", df_clean.shape)
print("\nSample notes_combined:")
print(df_clean["notes_combined"].head(3).to_string())
print("\nMissing values:")
print(df_clean.isnull().sum())

# ── Save ──────────────────────────────────────────────────────────────────────
df_clean.to_csv(
    r"C:\Perfume_Seeker\Data_Fragrantica\archive\fra_selected.csv",
    index=False,
    encoding="utf-8"
)
print("\nSaved to fra_selected.csv")