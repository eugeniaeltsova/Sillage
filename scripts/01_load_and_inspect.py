import pandas as pd

# ── Load ──────────────────────────────────────────────────────────────────────
df = pd.read_csv(r"C:\\Perfume_Seeker\\Data_Fragrantica\\archive\\fra_cleaned.csv", encoding="latin-1", sep = ";", on_bad_lines="skip")  # adjust filename if needed

# ── Quick overview ────────────────────────────────────────────────────────────
print("Shape:", df.shape)
print("\nColumn names:")
print(df.columns.tolist())
print("\nFirst 3 rows:")
print(df.head(3))
print("\nMissing values per column:")
print(df.isnull().sum())
