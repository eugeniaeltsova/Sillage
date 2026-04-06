import pandas as pd
from rapidfuzz import process, fuzz
from openai import AzureOpenAI
from qdrant_client import QdrantClient
from dotenv import load_dotenv
import os
import unicodedata

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

# ── Embedding ─────────────────────────────────────────────────────────────────
def get_embedding(text: str) -> list:
    response = openai_client.embeddings.create(
        model="text-embedding-3-small",
        input=text
    )
    return response.data[0].embedding

# ── Text normalisation ───────────────────────────────────────────────────────

def normalise(text: str) -> str:
    return unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii").lower()

# ── Fuzzy name matching ───────────────────────────────────────────────────────

def find_perfume_by_name(query: str, perfume_names: list) -> str | None:

    # Normalise query
    normalised_query = normalise(query)
    normalised_names = [normalise(name) for name in perfume_names]
    
    result = process.extractOne(
        normalised_query,
        normalised_names,
        scorer=fuzz.token_sort_ratio
    )
    match, score, index = result
    #print(f"match={match}, score={score}, index={index}, type={type(index)}")
    #print(f"Original at index: '{perfume_names[index]}'")
    
    if score >= 80:
        return perfume_names[index]
    return None

# ── Build embedding text (shared with scripts) ────────────────────────────────
def build_embedding_text(row) -> str:
    parts = []
    if pd.notna(row.get("Gender")) and row.get("Gender") != "":
        parts.append(row["Gender"])
    if pd.notna(row.get("Perfumer1")) and str(row.get("Perfumer1")) not in ("unknown", ""):
        parts.append(f"perfumer: {row['Perfumer1']}")
    if pd.notna(row.get("Top")) and row.get("Top") != "":
        parts.append(f"top: {row['Top']}")
    if pd.notna(row.get("Middle")) and row.get("Middle") != "":
        parts.append(f"middle: {row['Middle']}")
    if pd.notna(row.get("Base")) and row.get("Base") != "":
        parts.append(f"base: {row['Base']}")
    if pd.notna(row.get("accords")) and row.get("accords") != "":
        parts.append(f"accords: {row['accords']}")
    return " | ".join(parts)

