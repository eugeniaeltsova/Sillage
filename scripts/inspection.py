import pandas as pd

df = pd.read_csv(r"C:\Perfume_Seeker\Data_Fragrantica\archive\fra_selected.csv")

"""print(df["Rating Value"].describe())
print(df["Rating Count"].describe())
print("\nSample notes:")
print(df["Top"].head(3).to_string())

print(df["Rating Value"].unique()[:20])
print(df[df["Rating Value"].apply(lambda x: not str(x).replace('.','',1).isdigit())]["Rating Value"].unique())"""

def build_embedding_text(row):
    parts = []
    if pd.notna(row["Gender"]) and row["Gender"] != "":
        parts.append(row["Gender"])
    if pd.notna(row["Perfumer1"]) and row["Perfumer1"] not in ("unknown", ""):
        parts.append(f"perfumer: {row['Perfumer1']}")
    if pd.notna(row["Top"]) and row["Top"] != "":
        parts.append(f"top: {row['Top']}")
    if pd.notna(row["Middle"]) and row["Middle"] != "":
        parts.append(f"middle: {row['Middle']}")
    if pd.notna(row["Base"]) and row["Base"] != "":
        parts.append(f"base: {row['Base']}")
    if pd.notna(row["accords"]) and row["accords"] != "":
        parts.append(f"accords: {row['accords']}")
    return " | ".join(parts)

df["embedding_text"] = df.apply(build_embedding_text, axis=1)

print(df["embedding_text"].iloc[0])