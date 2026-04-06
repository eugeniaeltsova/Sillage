import pandas as pd
from openai import AzureOpenAI
from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance, PointStruct
from dotenv import load_dotenv
import os
import time

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

# ── Load data ─────────────────────────────────────────────────────────────────
df = pd.read_csv(r"C:\Perfume_Seeker\Data_Fragrantica\archive\fra_selected.csv")


# ── Build embedding text ──────────────────────────────────────────────────────
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

# ── Preview embedding text ────────────────────────────────────────────────────
print("Sample embedding texts:")
print(df["embedding_text"].head(3).to_string())
print(df["embedding_text"].iloc[0])
print(f"\nTotal perfumes to embed: {len(df)}")

# ── Create Qdrant collection ──────────────────────────────────────────────────
COLLECTION_NAME = "perfumes"

# Delete if exists (clean start)
if qdrant_client.collection_exists(COLLECTION_NAME):
    qdrant_client.delete_collection(COLLECTION_NAME)
    print(f"\nDeleted existing collection: {COLLECTION_NAME}")


qdrant_client.create_collection(
    collection_name=COLLECTION_NAME,
    vectors_config=VectorParams(size=1536, distance=Distance.COSINE)
)
print(f"Created collection: {COLLECTION_NAME}")

# ── Generate embeddings and upload in batches ─────────────────────────────────
BATCH_SIZE = 500  # Adjust based on your needs and rate limits
total = len(df)
uploaded = 0

for i in range(0, total, BATCH_SIZE):
    batch = df.iloc[i:i+BATCH_SIZE]

    # Generate embeddings
    texts = batch["embedding_text"].tolist()
    response = openai_client.embeddings.create(
        model="text-embedding-3-small",
        input=texts
    )
    embeddings = [item.embedding for item in response.data]

    # Build Qdrant points
    points = []
    for j, (idx, row) in enumerate(batch.iterrows()):
        points.append(PointStruct(
            id=idx,
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

    # Upload batch
    qdrant_client.upsert(collection_name=COLLECTION_NAME, points=points)
    uploaded += len(batch)
    print(f"Uploaded {uploaded}/{total} perfumes...")

    # Small delay to avoid rate limiting
    time.sleep(0.5)

print(f"\nDone! {uploaded} perfumes uploaded to Qdrant.")

