import pandas as pd
from openai import AzureOpenAI
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct
from dotenv import load_dotenv
import os

# ── Load environment variables ────────────────────────────────────────────────
load_dotenv(r"C:\Perfume_Seeker\.env")

# ── Clients ───────────────────────────────────────────────────────────────────
openai_client = AzureOpenAI(
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    api_key=os.getenv("AZURE_OPENAI_KEY"),
    api_version="2024-02-01"
)

qdrant_client = QdrantClient(
    url=os.getenv("QDRANT_URL"),
    api_key=os.getenv("QDRANT_API_KEY"),
    timeout=60
)

COLLECTION_NAME = "perfumes"

# ── Build embedding text (same logic as 04) ───────────────────────────────────
def build_embedding_text(row):
    parts = []
    if pd.notna(row["Gender"]) and row["Gender"] != "":
        parts.append(row["Gender"])
    if pd.notna(row["Perfumer1"]) and str(row["Perfumer1"]) not in ("unknown", ""):
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

# ── Load new perfumes ─────────────────────────────────────────────────────────
# Option A — from CSV:
# df_new = pd.read_csv(r"C:\Perfume_Seeker\Data_Fragrantica\archive\new_perfumes.csv")

# Option B — hardcoded single entry:
df_new = pd.DataFrame([{
    "Perfume": "Secretions Magnifiques",
    "Brand": "Etat Libre d'Orange",
    "Gender": "unisex",
    "Rating Value": 2.42,
    "Rating Count": 3822,
    "Year": 2006,
    "Perfumer1": "Antoine Lie",
    "Top": "marine, salt, aldehyde",
    "Middle": "blood, milk, adrenalin",
    "Base": "sandalwood, iris, opoponax",
    "accords": "marine, lactonic, aquatic, aromatic, coconut, sweet, iris, woody, powdery, amber",
    "notes_combined": "top: marine, salt, aldehyde| middle: blood, milk, adrenalin | base: sandalwood, iris, opoponax | accords: marine, lactonic, aquatic, aromatic, coconut, sweet, iris, woody, powdery, amber",
    "url": "https://www.fragrantica.com/perfume/Etat-Libre-d-Orange/Secretions-Magnifiques"
}])

# ── Get next available ID ─────────────────────────────────────────────────────
collection_info = qdrant_client.get_collection(COLLECTION_NAME)
next_id = collection_info.points_count
print(f"Current collection size: {next_id}")
print(f"New entries to add: {len(df_new)}")

# ── Build embedding texts ─────────────────────────────────────────────────────
df_new["embedding_text"] = df_new.apply(build_embedding_text, axis=1)
print("\nSample embedding text:")
print(df_new["embedding_text"].iloc[0])

# ── Generate embeddings ───────────────────────────────────────────────────────
texts = df_new["embedding_text"].tolist()
response = openai_client.embeddings.create(
    model="text-embedding-3-small",
    input=texts
)
embeddings = [item.embedding for item in response.data]

# ── Build and upload points ───────────────────────────────────────────────────
points = []
for j, (_, row) in enumerate(df_new.iterrows()):
    points.append(PointStruct(
        id=next_id + j,
        vector=embeddings[j],
        payload={
            "Perfume": row["Perfume"],
            "Brand": row["Brand"],
            "Gender": row["Gender"],
            "Year": int(row["Year"]),
            "Rating Value": float(row["Rating Value"]),
            "Rating Count": int(row["Rating Count"]),
            "Perfumer1": row["Perfumer1"],
            "Top": row["Top"],
            "Middle": row["Middle"],
            "Base": row["Base"],
            "accords": row["accords"],
            "notes_combined": row["notes_combined"],
            "url": row["url"]
        }
    ))

qdrant_client.upsert(collection_name=COLLECTION_NAME, points=points)
print(f"\nAdded {len(points)} new perfume(s) to collection.")
print(f"Collection now has {next_id + len(points)} points.")